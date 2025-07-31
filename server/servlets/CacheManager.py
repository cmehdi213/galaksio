#!/usr/bin/env python3
"""
Cache Manager for Galaksio
Provides caching functionality with TTL support and cleanup.
"""

import logging
import time
import threading
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages application cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.start_cleanup_thread()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key not in self.cache:
                return None
            
            cache_entry = self.cache[key]
            
            # Check if expired
            if cache_entry['expires_at'] < time.time():
                self._remove_key(key)
                return None
            
            # Update access time
            self.access_times[key] = time.time()
            return cache_entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        with self.lock:
            # Check if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Set cache entry
            expires_at = time.time() + (ttl or self.default_ttl)
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            self.access_times[key] = time.time()
            
            logger.debug(f"Cache set: {key}")
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self.lock:
            return self._remove_key(key)
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            logger.info("Cache cleared")
            return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self.lock:
            if key not in self.cache:
                return False
            
            # Check if expired
            if self.cache[key]['expires_at'] < time.time():
                self._remove_key(key)
                return False
            
            return True
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        with self.lock:
            if key not in self.cache:
                return None
            
            cache_entry = self.cache[key]
            remaining_ttl = cache_entry['expires_at'] - time.time()
            return max(0, int(remaining_ttl))
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            now = time.time()
            total_entries = len(self.cache)
            expired_entries = sum(1 for entry in self.cache.values() 
                                if entry['expires_at'] < now)
            
            # Calculate memory usage (approximate)
            total_memory = sum(len(str(entry['value'])) for entry in self.cache.values())
            
            # Hit rate calculation (simplified)
            hit_rate = 0.0  # Would need tracking for accurate calculation
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'max_size': self.max_size,
                'usage_percentage': (total_entries / self.max_size * 100) if self.max_size > 0 else 0,
                'total_memory_bytes': total_memory,
                'hit_rate': hit_rate,
                'default_ttl': self.default_ttl,
                'timestamp': datetime.now().isoformat()
            }
    
    def _remove_key(self, key: str) -> bool:
        """Remove key from cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            logger.debug(f"Cache removed: {key}")
            return True
        return False
    
    def _evict_lru(self):
        """Evict least recently used entries."""
        if not self.access_times:
            return
        
        # Find least recently used key
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove_key(lru_key)
        logger.debug(f"Cache evicted (LRU): {lru_key}")
    
    def start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup():
            while True:
                try:
                    time.sleep(60)  # Check every minute
                    self.cleanup_expired_cache()
                except Exception as e:
                    logger.error(f"Error in cache cleanup thread: {e}")
        
        self.cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        self.cleanup_thread.start()
        logger.info("Cache cleanup thread started")
    
    def cleanup_expired_cache(self):
        """Clean up expired cache entries."""
        with self.lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self.cache.items() 
                if entry['expires_at'] < now
            ]
            
            for key in expired_keys:
                self._remove_key(key)
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

# Decorator for caching function results
def cache_result(ttl: int = 300, key_prefix: str = 'func_cache'):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}")
            return result
        
        return wrapper
    return decorator

# Global cache manager instance
cache_manager = None

def get_cache_manager(max_size: int = 1000, default_ttl: int = 300) -> CacheManager:
    """Get or create the global cache manager."""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager(max_size, default_ttl)
    return cache_manager
