#!/usr/bin/env python3
"""
Enhanced Authentication Handler for Galaxy 25.0
Handles various authentication methods and provides better error handling.
"""

import logging
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.objects import GalaxyInstance as GalaxyInstanceObjects
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class GalaxyAuthHandler:
    """Enhanced authentication handler for Galaxy connections."""
    
    def __init__(self, galaxy_url, api_key=None):
        self.galaxy_url = galaxy_url.rstrip('/')
        self.api_key = api_key
        self.gi = None
        self.gi_objects = None
        self.user_info = None
    
    def authenticate(self):
        """
        Authenticate with Galaxy instance using multiple methods.
        Returns tuple (success: bool, message: str)
        """
        try:
            # Method 1: Direct API key authentication
            if self.api_key:
                return self._authenticate_with_api_key()
            
            # Method 2: Session-based authentication (if available)
            return self._authenticate_with_session()
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False, f"Authentication error: {str(e)}"
    
    def _authenticate_with_api_key(self):
        """Authenticate using API key."""
        try:
            # Create Galaxy instance
            self.gi = GalaxyInstance(self.galaxy_url, self.api_key)
            self.gi_objects = GalaxyInstanceObjects(self.galaxy_url, self.api_key)
            
            # Test connection by getting user info
            self.user_info = self.gi.users.get_current_users()
            
            if not self.user_info:
                return False, "Invalid API key or insufficient permissions"
            
            logger.info(f"Successfully authenticated as: {self.user_info[0].get('email', 'Unknown')}")
            return True, "Authentication successful"
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                return False, "Invalid API key or insufficient permissions"
            elif "404" in error_msg:
                return False, "Galaxy instance not found or URL incorrect"
            else:
                return False, f"Connection error: {error_msg}"
    
    def _authenticate_with_session(self):
        """Authenticate using session-based method (for future implementation)."""
        return False, "Session-based authentication not yet implemented"
    
    def test_connection(self):
        """Test the connection to Galaxy instance."""
        if not self.gi:
            return False, "Not authenticated"
        
        try:
            # Test basic API call
            version = self.gi.config.get_version()
            if version:
                return True, f"Connected to Galaxy {version.get('version_major', 'unknown')}"
            return False, "Could not get Galaxy version"
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def get_instance(self):
        """Get the authenticated Galaxy instance."""
        return self.gi
    
    def get_objects_instance(self):
        """Get the authenticated Galaxy objects instance."""
        return self.gi_objects
    
    def get_user_info(self):
        """Get current user information."""
        return self.user_info

def authenticate_galaxy(galaxy_url, api_key=None):
    """
    Convenience function for Galaxy authentication.
    
    Args:
        galaxy_url (str): Galaxy instance URL
        api_key (str, optional): Galaxy API key
    
    Returns:
        tuple: (auth_handler: GalaxyAuthHandler, success: bool, message: str)
    """
    auth_handler = GalaxyAuthHandler(galaxy_url, api_key)
    success, message = auth_handler.authenticate()
    
    return auth_handler, success, message
