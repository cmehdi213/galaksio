#!/usr/bin/env python3
"""
Galaxy Settings Configuration for Galaksio
Provides centralized configuration management with validation.
"""

import os
from typing import Optional

class GalaxySettings:
    """Enhanced configuration management for Galaksio with validation."""
    
    def __init__(self):
        self.GALAXY_SERVER = self._get_env_var('GALAXY_SERVER', 'https://usegalaxy.org/')
        self.HOST = self._get_env_var('HOST', '0.0.0.0')
        self.PORT = self._get_int_var('PORT', 8081)
        self.DEBUG = self._get_bool_var('DEBUG', False)
        self.SECRET_KEY = self._get_env_var('SECRET_KEY', 'dev-secret-key-change-in-production')
        
        # Paired reads settings
        self.AUTO_PAIR_CONFIDENCE_THRESHOLD = self._get_float_var('AUTO_PAIR_CONFIDENCE_THRESHOLD', 0.7)
        self.SUPPORTED_EXTENSIONS = self._get_env_var('SUPPORTED_EXTENSIONS', 
            '.fastq,.fq,.fasta,.fa,.fas,.fastq.gz,.fq.gz,.fasta.gz,.fa.gz,.fas.gz,.bam,.sam')
        
        # Security settings
        self.CORS_ENABLED = self._get_bool_var('CORS_ENABLED', True)
        self.MAX_FILE_SIZE = self._get_int_var('MAX_FILE_SIZE', 17179869184)  # 16GB in bytes
        
        # Rate limiting settings
        self.RATE_LIMIT_REQUESTS = self._get_int_var('RATE_LIMIT_REQUESTS', 100)
        self.RATE_LIMIT_WINDOW = self._get_int_var('RATE_LIMIT_WINDOW', 60)
        
        # Cache settings
        self.CACHE_MAX_SIZE = self._get_int_var('CACHE_MAX_SIZE', 1000)
        self.CACHE_DEFAULT_TTL = self._get_int_var('CACHE_DEFAULT_TTL', 300)
        
        # Validate configuration
        self._validate_config()
    
    def _get_env_var(self, key: str, default: str) -> str:
        """Get environment variable with validation."""
        value = os.getenv(key, default)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _get_int_var(self, key: str, default: int) -> int:
        """Get integer environment variable."""
        try:
            value = os.getenv(key, str(default))
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be an integer")
    
    def _get_float_var(self, key: str, default: float) -> float:
        """Get float environment variable."""
        try:
            value = os.getenv(key, str(default))
            return float(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be a float")
    
    def _get_bool_var(self, key: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _validate_config(self):
        """Validate configuration values."""
        # Validate URL format
        if not self.GALAXY_SERVER.startswith(('http://', 'https://')):
            raise ValueError("GALAXY_SERVER must start with http:// or https://")
        
        # Validate port range
        if not (1 <= self.PORT <= 65535):
            raise ValueError("PORT must be between 1 and 65535")
        
        # Validate secret key length
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        # Validate confidence threshold
        if not (0.0 <= self.AUTO_PAIR_CONFIDENCE_THRESHOLD <= 1.0):
            raise ValueError("AUTO_PAIR_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
        
        # Validate max file size
        if self.MAX_FILE_SIZE < 1024:  # At least 1KB
            raise ValueError("MAX_FILE_SIZE must be at least 1024 bytes")
        
        # Validate rate limiting
        if self.RATE_LIMIT_REQUESTS < 1:
            raise ValueError("RATE_LIMIT_REQUESTS must be at least 1")
        
        if self.RATE_LIMIT_WINDOW < 1:
            raise ValueError("RATE_LIMIT_WINDOW must be at least 1")
        
        # Validate cache settings
        if self.CACHE_MAX_SIZE < 1:
            raise ValueError("CACHE_MAX_SIZE must be at least 1")
        
        if self.CACHE_DEFAULT_TTL < 1:
            raise ValueError("CACHE_DEFAULT_TTL must be at least 1")
    
    def get_supported_extensions_list(self) -> list:
        """Get supported extensions as a list."""
        return [ext.strip() for ext in self.SUPPORTED_EXTENSIONS.split(',') if ext.strip()]
    
    def get_rate_limit_config(self) -> dict:
        """Get rate limiting configuration."""
        return {
            'max_requests': self.RATE_LIMIT_REQUESTS,
            'window_seconds': self.RATE_LIMIT_WINDOW
        }
    
    def get_cache_config(self) -> dict:
        """Get cache configuration."""
        return {
            'max_size': self.CACHE_MAX_SIZE,
            'default_ttl': self.CACHE_DEFAULT_TTL
        }
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            'GALAXY_SERVER': self.GALAXY_SERVER,
            'HOST': self.HOST,
            'PORT': self.PORT,
            'DEBUG': self.DEBUG,
            'SECRET_KEY': '***REDACTED***',
            'AUTO_PAIR_CONFIDENCE_THRESHOLD': self.AUTO_PAIR_CONFIDENCE_THRESHOLD,
            'SUPPORTED_EXTENSIONS': self.get_supported_extensions_list(),
            'CORS_ENABLED': self.CORS_ENABLED,
            'MAX_FILE_SIZE': self.MAX_FILE_SIZE,
            'RATE_LIMIT_REQUESTS': self.RATE_LIMIT_REQUESTS,
            'RATE_LIMIT_WINDOW': self.RATE_LIMIT_WINDOW,
            'CACHE_MAX_SIZE': self.CACHE_MAX_SIZE,
            'CACHE_DEFAULT_TTL': self.CACHE_DEFAULT_TTL
        }
    
    def update_from_dict(self, config_dict: dict):
        """Update settings from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Re-validate after update
        self._validate_config()

# Global settings instance
settings = GalaxySettings()
