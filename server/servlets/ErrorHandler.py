#!/usr/bin/env python3
"""
Enhanced Error Handler for Galaxy 25.0
Provides comprehensive error handling and user-friendly messages.
"""

import logging
import traceback
from typing import Dict, Optional, Any
from flask import jsonify, current_app
from bioblend.galaxy.client import ConnectionError

logger = logging.getLogger(__name__)

class GalaksioError(Exception):
    """Base exception for Galaksio-specific errors."""
    
    def __init__(self, message: str, error_code: str = "GENERIC_ERROR", 
                 details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class GalaxyConnectionError(GalaksioError):
    """Galaxy connection errors."""
    pass

class AuthenticationError(GalaksioError):
    """Authentication errors."""
    pass

class WorkflowExecutionError(GalaksioError):
    """Workflow execution errors."""
    pass

class FileUploadError(GalaksioError):
    """File upload errors."""
    pass

class ErrorHandler:
    """Enhanced error handler with user-friendly messages."""
    
    ERROR_MESSAGES = {
        # Galaxy Connection Errors
        'CONNECTION_FAILED': {
            'user_message': 'Unable to connect to Galaxy instance',
            'technical_message': 'Connection to Galaxy server failed',
            'suggestions': [
                'Check if Galaxy instance is running',
                'Verify the Galaxy URL is correct',
                'Check network connectivity',
                'Verify firewall settings'
            ]
        },
        'AUTHENTICATION_FAILED': {
            'user_message': 'Authentication failed',
            'technical_message': 'Invalid API key or credentials',
            'suggestions': [
                'Verify your API key is correct',
                'Check if API key has expired',
                'Ensure you have necessary permissions',
                'Try generating a new API key'
            ]
        },
        'WORKFLOW_NOT_FOUND': {
            'user_message': 'Workflow not found',
            'technical_message': 'Specified workflow does not exist',
            'suggestions': [
                'Check workflow ID is correct',
                'Verify you have access to the workflow',
                'Refresh workflow list'
            ]
        },
        'HISTORY_NOT_FOUND': {
            'user_message': 'History not found',
            'technical_message': 'Specified history does not exist',
            'suggestions': [
                'Check history ID is correct',
                'Verify you have access to the history',
                'Create a new history if needed'
            ]
        },
        'FILE_UPLOAD_FAILED': {
            'user_message': 'File upload failed',
            'technical_message': 'Unable to upload file to Galaxy',
            'suggestions': [
                'Check file size limits',
                'Verify file format is supported',
                'Check available disk space',
                'Try uploading a smaller file first'
            ]
        },
        'WORKFLOW_EXECUTION_FAILED': {
            'user_message': 'Workflow execution failed',
            'technical_message': 'Workflow encountered errors during execution',
            'suggestions': [
                'Check input data is valid',
                'Verify workflow parameters',
                'Check Galaxy job queue status',
                'Review workflow error logs'
            ]
        },
        'INVALID_INPUT_DATA': {
            'user_message': 'Invalid input data',
            'technical_message': 'Input data validation failed',
            'suggestions': [
                'Check data format is correct',
                'Verify all required fields are filled',
                'Check data type compatibility',
                'Review input validation rules'
            ]
        },
        'PERMISSION_DENIED': {
            'user_message': 'Permission denied',
            'technical_message': 'Insufficient permissions for requested operation',
            'suggestions': [
                'Check your user permissions',
                'Contact Galaxy administrator',
                'Verify API key has necessary permissions',
                'Check if resource is shared with you'
            ]
        },
        'TIMEOUT_ERROR': {
            'user_message': 'Operation timed out',
            'technical_message': 'Operation took too long to complete',
            'suggestions': [
                'Try again later',
                'Check Galaxy server load',
                'Reduce data size if possible',
                'Contact administrator if problem persists'
            ]
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: Optional[Dict] = None) -> Dict:
        """
        Handle an exception and return user-friendly error response.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
        
        Returns:
            Dict with error information
        """
        context = context or {}
        
        # Log the error
        self.logger.error(f"Error occurred: {str(error)}", exc_info=True)
        
        # Determine error type and code
        error_code = self._determine_error_code(error)
        error_info = self.ERROR_MESSAGES.get(error_code, self.ERROR_MESSAGES['GENERIC_ERROR'])
        
        # Create error response
        error_response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': error_info['user_message'],
                'technical_message': error_info['technical_message'],
                'suggestions': error_info['suggestions'],
                'context': context,
                'timestamp': self._get_timestamp()
            }
        }
        
        # Add stack trace for development
        if current_app and current_app.debug:
            error_response['error']['stack_trace'] = traceback.format_exc()
        
        return error_response
    
    def _determine_error_code(self, error: Exception) -> str:
        """Determine error code based on exception type."""
        if isinstance(error, ConnectionError):
            return 'CONNECTION_FAILED'
        elif isinstance(error, AuthenticationError):
            return 'AUTHENTICATION_FAILED'
        elif isinstance(error, WorkflowExecutionError):
            return 'WORKFLOW_EXECUTION_FAILED'
        elif isinstance(error, FileUploadError):
            return 'FILE_UPLOAD_FAILED'
        elif hasattr(error, 'response'):
            # Handle HTTP errors
            status_code = getattr(error.response, 'status_code', 0)
            if status_code == 401:
                return 'AUTHENTICATION_FAILED'
            elif status_code == 403:
                return 'PERMISSION_DENIED'
            elif status_code == 404:
                return 'WORKFLOW_NOT_FOUND'
            elif status_code == 408:
                return 'TIMEOUT_ERROR'
        
        # Default error code
        return 'GENERIC_ERROR'
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def create_user_error(self, message: str, error_code: str = "USER_ERROR", 
                          suggestions: Optional[list] = None) -> Dict:
        """Create a user-friendly error response."""
        error_response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'technical_message': message,
                'suggestions': suggestions or [],
                'timestamp': self._get_timestamp()
            }
        }
        
        return error_response

# Global error handler instance
error_handler = ErrorHandler()

def handle_galaxy_error(error: Exception, context: Optional[Dict] = None) -> Dict:
    """Convenience function for handling Galaxy errors."""
    return error_handler.handle_error(error, context)

def create_error_response(message: str, error_code: str = "USER_ERROR", 
                         suggestions: Optional[list] = None) -> Dict:
    """Convenience function for creating error responses."""
    return error_handler.create_user_error(message, error_code, suggestions)

# Flask error handlers
def register_error_handlers(app):
    """Register error handlers with Flask app."""
    
    @app.errorhandler(GalaksioError)
    def handle_galaksio_error(error):
        response = error_handler.handle_error(error)
        return jsonify(response), 400
    
    @app.errorhandler(ConnectionError)
    def handle_connection_error(error):
        response = error_handler.handle_error(error)
        return jsonify(response), 503
    
    @app.errorhandler(404)
    def handle_not_found(error):
        response = create_error_response(
            "Resource not found",
            "NOT_FOUND",
            ["Check the URL is correct", "Verify the resource exists"]
        )
        return jsonify(response), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        response = create_error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            ["Try again later", "Contact support if problem persists"]
        )
        return jsonify(response), 500
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        response = error_handler.handle_error(error)
        return jsonify(response), 500
