#!/usr/bin/env python3
"""
Security Manager for Galaksio
Provides security functionality including JWT tokens, input validation, and security headers.
"""

import logging
import re
import jwt
import hashlib
import secrets
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security features for Galaksio."""
    
    def __init__(self, jwt_secret_key: str, jwt_expiration_hours: int = 24):
        self.jwt_secret_key = jwt_secret_key
        self.jwt_expiration_hours = jwt_expiration_hours
        self.blacklisted_tokens = set()
        self.failed_login_attempts = {}
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Content-Security-Policy': self._get_csp_policy()
        }
    
    def generate_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Generate JWT token."""
        try:
            payload = {
                'user_id': user_id,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
                'jti': secrets.token_urlsafe(16)
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, self.jwt_secret_key, algorithm='HS256')
            logger.info(f"Generated token for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise
    
    def validate_token(self, token: str) -> bool:
        """Validate JWT token."""
        try:
            # Check if token is blacklisted
            if token in self.blacklisted_tokens:
                logger.warning("Attempted to use blacklisted token")
                return False
            
            # Decode and validate token
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=['HS256'])
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
                logger.warning("Token expired")
                return False
            
            logger.debug(f"Token validated for user {payload.get('user_id')}")
            return True
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return False
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False
    
    def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist."""
        try:
            self.blacklisted_tokens.add(token)
            logger.info("Token blacklisted")
            return True
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False
    
    def get_token_payload(self, token: str) -> Optional[Dict]:
        """Get payload from JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=['HS256'])
            return payload
        except Exception as e:
            logger.error(f"Error getting token payload: {e}")
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        try:
            salt = secrets.token_hex(16)
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return f"{salt}:{password_hash}"
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            salt, password_hash = hashed_password.split(':')
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == password_hash
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def validate_input(self, input_data: Any, validation_rules: Dict) -> Dict:
        """Validate input data against rules."""
        errors = []
        
        for field, rules in validation_rules.items():
            if field not in input_data:
                if rules.get('required', False):
                    errors.append(f"{field} is required")
                continue
            
            value = input_data[field]
            
            # Type validation
            if 'type' in rules:
                expected_type = rules['type']
                if not isinstance(value, expected_type):
                    errors.append(f"{field} must be of type {expected_type.__name__}")
            
            # Length validation
            if 'min_length' in rules and len(str(value)) < rules['min_length']:
                errors.append(f"{field} must be at least {rules['min_length']} characters long")
            
            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                errors.append(f"{field} must be at most {rules['max_length']} characters long")
            
            # Range validation
            if 'min_value' in rules and value < rules['min_value']:
                errors.append(f"{field} must be at least {rules['min_value']}")
            
            if 'max_value' in rules and value > rules['max_value']:
                errors.append(f"{field} must be at most {rules['max_value']}")
            
            # Pattern validation
            if 'pattern' in rules:
                if not re.match(rules['pattern'], str(value)):
                    errors.append(f"{field} format is invalid")
            
            # Custom validation
            if 'custom' in rules:
                custom_error = rules['custom'](value)
                if custom_error:
                    errors.append(custom_error)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def sanitize_input(self, input_data: Any) -> Any:
        """Sanitize input data to prevent XSS and injection attacks."""
        if isinstance(input_data, str):
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\']', '', input_data)
            return sanitized
        elif isinstance(input_data, dict):
            return {key: self.sanitize_input(value) for key, value in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        else:
            return input_data
    
    def log_failed_attempt(self, identifier: str) -> bool:
        """Log failed login attempt."""
        try:
            if identifier not in self.failed_login_attempts:
                self.failed_login_attempts[identifier] = {
                    'attempts': 0,
                    'first_attempt': datetime.utcnow(),
                    'locked_until': None
                }
            
            attempt_data = self.failed_login_attempts[identifier]
            attempt_data['attempts'] += 1
            
            # Lock account after too many attempts
            if attempt_data['attempts'] >= 5:
                lock_duration = timedelta(minutes=30)
                attempt_data['locked_until'] = datetime.utcnow() + lock_duration
                logger.warning(f"Account {identifier} locked due to too many failed attempts")
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging failed attempt: {e}")
            return False
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked."""
        try:
            if identifier not in self.failed_login_attempts:
                return False
            
            attempt_data = self.failed_login_attempts[identifier]
            if attempt_data['locked_until']:
                if datetime.utcnow() < attempt_data['locked_until']:
                    return True
                else:
                    # Reset after lock period
                    del self.failed_login_attempts[identifier]
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking account lock: {e}")
            return False
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses."""
        return self.security_headers.copy()
    
    def _get_csp_policy(self) -> str:
        """Get Content Security Policy."""
        return "; ".join([
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' *",
            "frame-ancestors 'none'",
            "form-action 'self'"
        ])
    
    def cleanup_expired_data(self):
        """Clean up expired security data."""
        try:
            # Clean up old failed login attempts
            current_time = datetime.utcnow()
            expired_identifiers = []
            
            for identifier, attempt_data in self.failed_login_attempts.items():
                if (current_time - attempt_data['first_attempt']) > timedelta(hours=24):
                    expired_identifiers.append(identifier)
            
            for identifier in expired_identifiers:
                del self.failed_login_attempts[identifier]
            
            # Clean up blacklisted tokens (older than expiration)
            # This would require storing token creation times
            
            logger.debug("Security data cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in security data cleanup: {e}")

# Decorator for requiring authentication
def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'error': 'Authorization token required'}), 401
        
        if not token.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Invalid token format'}), 401
        
        token = token[7:]  # Remove 'Bearer ' prefix
        
        if not security_manager.validate_token(token):
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Decorator for requiring admin role
def require_admin(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization token required'}), 401
        
        token = token[7:]
        
        if not security_manager.validate_token(token):
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        payload = security_manager.get_token_payload(token)
        if not payload or not payload.get('is_admin', False):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Global security manager instance
security_manager = None

def get_security_manager(jwt_secret_key: str, jwt_expiration_hours: int = 24) -> SecurityManager:
    """Get or create the global security manager."""
    global security_manager
    if security_manager is None:
        security_manager = SecurityManager(jwt_secret_key, jwt_expiration_hours)
    return security_manager
