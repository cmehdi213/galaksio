#!/usr/bin/env python3
"""
Rate Limiter for Galaksio
Provides rate limiting functionality to prevent abuse.
"""

import logging
import time
import threading
from typing import Dict, Optional, Callable
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter implementation using sliding window algorithm."""
    
    def __init__(self, default_requests: int = 100, default_window: int = 60):
        self.default_requests = default_requests
        self.default_window = default_window
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.limits: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.start_cleanup_thread()
    
    def set_limit(self, key: str, requests: int, window: int):
        """Set rate limit for a specific key."""
        with self.lock:
            self.limits[key] = {
                'requests': requests,
                'window': window
            }
            logger.debug(f"Rate limit set for {key}: {requests} requests per {window} seconds")
    
    def check_rate_limit(self, key: str) -> Dict:
        """Check if request is allowed."""
        with self.lock:
            current_time = time.time()
            
            # Get limit for this key
            limit = self.limits.get(key, {
                'requests': self.default_requests,
                'window': self.default_window
            })
            
            # Get request timestamps for this key
            request_times = self.requests[key]
            
            # Remove old requests outside the window
            window_start = current_time - limit['window']
            while request_times and request_times[0] < window_start:
                request_times.popleft()
            
            # Check if limit exceeded
            if len(request_times) >= limit['requests']:
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_time': request_times[0] + limit['window'] if request_times else current_time,
                    'limit': limit['requests'],
                    'window': limit['window']
                }
            
            # Add current request
            request_times.append(current_time)
            
            return {
                'allowed': True,
                'remaining': limit['requests'] - len(request_times),
                'reset_time': request_times[0] + limit['window'] if request_times else current_time,
                'limit': limit['requests'],
                'window': limit['window']
            }
    
    def get_client_key(self, request_type: str = 'default') -> str:
        """Get client key for rate limiting."""
        # Try to get client IP
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        # Try to get API key if available
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header.split(' ')[1]
        else:
            api_key = request.headers.get('X-API-Key') or request.json.get('key') if request.json else None
        
        # Try to get user agent
        user_agent = request.headers.get('User-Agent', 'unknown')
        
        # Create unique key
        if api_key:
            return f"{request_type}:{api_key}"
        else:
            return f"{request_type}:{ip}:{hash(user_agent) % 10000}"
    
    def start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup():
            while True:
                try:
                    time.sleep(300)  # Clean up every 5 minutes
                    self.cleanup_old_requests()
                except Exception as e:
                    logger.error(f"Error in rate limiter cleanup thread: {e}")
        
        self.cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        self.cleanup_thread.start()
        logger.info("Rate limiter cleanup thread started")
    
    def cleanup_old_requests(self):
        """Clean up old request records."""
        with self.lock:
            current_time = time.time()
            keys_to_remove = []
            
            for key, request_times in self.requests.items():
                # Remove old requests
                window_start = current_time - 3600  # Keep last hour
                while request_times and request_times[0] < window_start:
                    request_times.popleft()
                
                # Remove empty keys
                if not request_times:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.requests[key]
            
            logger.debug(f"Rate limiter cleanup completed, removed {len(keys_to_remove)} keys")
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        with self.lock:
            total_keys = len(self.requests)
            total_requests = sum(len(times) for times in self.requests.values())
            
            # Get most active clients
            active_clients = sorted(
                self.requests.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
            
            return {
                'total_clients': total_keys,
                'total_requests': total_requests,
                'active_clients': [
                    {'key': key, 'request_count': len(times)}
                    for key, times in active_clients
                ],
                'configured_limits': len(self.limits),
                'timestamp': time.time()
            }

# Decorator for rate limiting
def rate_limit(limit_type: str = 'default'):
    """Decorator for rate limiting."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client key
            client_key = rate_limiter.get_client_key(limit_type)
            
            # Check rate limit
            result = rate_limiter.check_rate_limit(client_key)
            
            if not result['allowed']:
                logger.warning(f"Rate limit exceeded for {client_key}")
                response = jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': int(result['reset_time'] - time.time())
                })
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                response.headers['X-RateLimit-Reset'] = str(int(result['reset_time']))
                response.headers['Retry-After'] = str(int(result['reset_time'] - time.time()))
                return response, 429
            
            # Add rate limit headers to response
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                response.headers['X-RateLimit-Reset'] = str(int(result['reset_time']))
            
            return response
        return decorated_function
    return decorator

# Global rate limiter instance
rate_limiter = None

def get_rate_limiter(default_requests: int = 100, default_window: int = 60) -> RateLimiter:
    """Get or create the global rate limiter."""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = RateLimiter(default_requests, default_window)
    return rate_limiter

# Configure default rate limits
def configure_rate_limits():
    """Configure default rate limits for different endpoint types."""
    if rate_limiter:
        # Authentication endpoints
        rate_limiter.set_limit('auth', 5, 60)  # 5 requests per minute
        
        # Workflow endpoints
        rate_limiter.set_limit('workflow', 50, 60)  # 50 requests per minute
        
        # Upload endpoints
        rate_limiter.set_limit('upload', 20, 60)  # 20 requests per minute
        
        # API endpoints
        rate_limiter.set_limit('api', 100, 60)  # 100 requests per minute
        
        # Admin endpoints
        rate_limiter.set_limit('admin', 10, 60)  # 10 requests per minute
        
        logger.info("Rate limits configured")
