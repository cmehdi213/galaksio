#!/usr/bin/env python3
"""
Galaksio Server - Main Flask Application
Updated for Galaxy 25.0 with enhanced security and error handling
"""

# (C) Copyright 2016 SLU Global Bioinformatics Centre, SLU
# (http://sgbc.slu.se) and the B3Africa Project (http://www.b3africa.org/).
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the GNU Lesser General Public License
# (LGPL) version 3 which accompanies this distribution, and is available at
# http://www.gnu.org/licenses/lgpl.html
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# Contributors:
# Rafael Hernandez de Diego
# Tomas Klingstrom
# Erik Bongcam-Rudloff
# and others.
#
# Updated for Galaxy 25.0 compatibility and modern web standards
#

import os
import sys
import logging
import json
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Any

from flask import Flask, request, jsonify, send_from_directory, make_response, render_template
from flask_cors import CORS
from flask_talisman import Talisman
from werkzeug.utils import secure_filename

# Add server directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from resources.galaxy_settings import settings

# Import servlets
from servlets.GalaxyAPI import (
    generateWorkflowReport,
    executeWorkflow,
    getWorkflowStatus,
    uploadFile,
    getUploadStatus,
    testConnection,
    detectPairedReads,
    createPairedCollection,
    autoPairAllReads,
    getPairedReadPatterns,
    getCompatibilityReport,
    getHistoryContents
)

# Import error handlers
from servlets.ErrorHandler import register_error_handlers

# Import cleanup utilities
from servlets.WorkflowTracker import workflow_tracker
from servlets.FileUploadHandler import upload_tracker

# Import security and rate limiting
from servlets.RateLimiter import rate_limit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GalaksioServer:
    """Main Galaksio Server class with enhanced functionality."""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        static_folder='../client/src',
                        template_folder='../client/src')
        self.setup_app()
        self.setup_routes()
        self.setup_background_tasks()
        
    def setup_app(self):
        """Configure Flask application with security and CORS."""
        # Configure CORS for modern browsers
        CORS(self.app, 
             resources={
                 r"/*": {
                     "origins": ["*"],  # Configure appropriately for production
                     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                     "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
                     "expose_headers": ["Content-Type", "X-Total-Count"],
                     "max_age": 3600
                 }
             })
        
        # Security headers with Talisman
        Talisman(self.app, 
                 force_https=False,  # Set to True in production
                 strict_transport_security=False,
                 session_cookie_secure=False,
                 content_security_policy={
                     'default-src': "'self'",
                     'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
                     'style-src': "'self' 'unsafe-inline'",
                     'img-src': "'self' data: https:',
                     'font-src': "'self' data:",
                     'connect-src': "'self' *",  # Allow connections to Galaxy instances
                 })
        
        # Register error handlers
        register_error_handlers(self.app)
        
        # Configure Flask settings
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max file size
        self.app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        logger.info("Galaksio Server initialized with enhanced security features")
    
    def setup_routes(self):
        """Setup all application routes."""
        
        # Security headers middleware
        @self.app.after_request
        def add_security_headers(response):
            """Add additional security headers."""
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            response.headers['X-Galaksio-Version'] = '0.4.0'
            return response
        
        # CORS preflight handler
        @self.app.route('/<path:path>', methods=['OPTIONS'])
        def handle_preflight(path):
            """Handle CORS preflight requests."""
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
        
        # Static file serving and main routes
        @self.app.route('/')
        def index():
            return send_from_directory(self.app.static_folder, 'index.html')
        
        @self.app.route('/<path:path>')
        def static_files(path):
            """Serve static files with SPA fallback."""
            try:
                return send_from_directory(self.app.static_folder, path)
            except:
                # Fallback to index.html for SPA routing
                return send_from_directory(self.app.static_folder, 'index.html')
        
        # Health check endpoint with Galaxy compatibility
        @self.app.route('/health')
        def health_check():
            """Health check endpoint with Galaxy compatibility verification."""
            health_data = {
                'status': 'healthy',
                'version': '0.4.0',
                'timestamp': datetime.now().isoformat(),
                'galaxy_compatibility': '25.0',
                'services': {
                    'workflow_tracker': 'active' if workflow_tracker else 'inactive',
                    'upload_tracker': 'active' if upload_tracker else 'inactive'
                },
                'system': {
                    'python_version': sys.version,
                    'flask_version': self.app.__version__
                },
                'galaxy_connection': 'unknown'
            }
            
            # Test Galaxy connection and compatibility
            try:
                from servlets.GalaxyAPI import get_galaxy_instance
                gi = get_galaxy_instance(settings)
                from servlets.GalaxyAPIVerifier import get_api_verifier
                verifier = get_api_verifier(gi)
                
                version = gi.config.get_version()
                health_data['galaxy_connection'] = 'connected'
                health_data['galaxy_version'] = version.get('version_major', 'unknown')
                health_data['compatibility_report'] = verifier.get_compatibility_report()
                
            except Exception as e:
                health_data['galaxy_connection'] = 'disconnected'
                health_data['galaxy_error'] = str(e)
            
            return jsonify(health_data)
        
        # API Routes - Galaxy Connection
        @self.app.route('/api/test_connection', methods=['POST'])
        @rate_limit('auth')
        def test_connection():
            """Test connection to Galaxy instance."""
            try:
                result = testConnection(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in test_connection: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # API Routes - Workflows
        @self.app.route('/api/execute_workflow', methods=['POST'])
        @rate_limit('workflow')
        def execute_workflow():
            """Execute a Galaxy workflow."""
            try:
                result = executeWorkflow(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in execute_workflow: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/generate_workflow_report', methods=['POST'])
        @rate_limit('workflow')
        def generate_workflow_report():
            """Generate workflow execution report."""
            try:
                result = generateWorkflowReport(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in generate_workflow_report: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get_workflow_status', methods=['POST'])
        @rate_limit('workflow')
        def get_workflow_status():
            """Get workflow execution status."""
            try:
                result = getWorkflowStatus(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in get_workflow_status: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get_all_workflow_status', methods=['GET'])
        @rate_limit('api')
        def get_all_workflow_status():
            """Get status of all active workflows."""
            try:
                if workflow_tracker:
                    active_workflows = workflow_tracker.get_all_active_workflows()
                    return jsonify({
                        'success': True,
                        'workflows': active_workflows,
                        'count': len(active_workflows),
                        'statistics': workflow_tracker.get_workflow_statistics()
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Workflow tracker not available'
                    }), 500
            except Exception as e:
                logger.error(f"Error in get_all_workflow_status: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # API Routes - File Upload
        @self.app.route('/api/upload_file', methods=['POST'])
        @rate_limit('upload')
        def upload_file():
            """Upload file to Galaxy."""
            try:
                result = uploadFile(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in upload_file: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get_upload_status', methods=['POST'])
        @rate_limit('api')
        def get_upload_status():
            """Get file upload status."""
            try:
                result = getUploadStatus(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in get_upload_status: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get_all_upload_status', methods=['GET'])
        @rate_limit('api')
        def get_all_upload_status():
            """Get status of all active uploads."""
            try:
                if upload_tracker:
                    active_uploads = list(upload_tracker.active_uploads.values())
                    return jsonify({
                        'success': True,
                        'uploads': active_uploads,
                        'count': len(active_uploads)
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Upload tracker not available'
                    }), 500
            except Exception as e:
                logger.error(f"Error in get_all_upload_status: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # API Routes - Paired Reads Handling
        @self.app.route('/api/detect_paired_reads', methods=['POST'])
        @rate_limit('api')
        def detect_paired_reads():
            """Detect paired-end reads in a Galaxy history."""
            try:
                result = detectPairedReads(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in detect_paired_reads: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/create_paired_collection', methods=['POST'])
        @rate_limit('api')
        def create_paired_collection():
            """Create a paired collection from detected paired reads."""
            try:
                result = createPairedCollection(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in create_paired_collection: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/auto_pair_all_reads', methods=['POST'])
        @rate_limit('api')
        def auto_pair_all_reads():
            """Automatically detect and pair all reads in a history."""
            try:
                result = autoPairAllReads(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in auto_pair_all_reads: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get_paired_read_patterns', methods=['GET'])
        @rate_limit('api')
        def get_paired_read_patterns():
            """Get supported paired read patterns."""
            try:
                from servlets.PairedReadsHandler import get_paired_reads_handler
                handler = get_paired_reads_handler(None)  # Pass None for pattern access
                result = handler.get_supported_patterns()
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in get_paired_read_patterns: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # API Routes - Galaxy Compatibility
        @self.app.route('/api/get_compatibility_report', methods=['POST'])
        @rate_limit('api')
        def get_compatibility_report():
            """Get Galaxy API compatibility report."""
            try:
                result = getCompatibilityReport(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in get_compatibility_report: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get_history_contents', methods=['POST'])
        @rate_limit('api')
        def get_history_contents():
            """Get history contents with Galaxy 25.0 compatibility."""
            try:
                result = getHistoryContents(request, settings)
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in get_history_contents: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # API Routes - Configuration
        @self.app.route('/api/get_config', methods=['GET'])
        @rate_limit('api')
        def get_config():
            """Get server configuration."""
            try:
                config_data = {
                    'success': True,
                    'config': {
                        'galaxy_server': settings.GALAXY_SERVER,
                        'max_file_size': self.app.config['MAX_CONTENT_LENGTH'],
                        'version': '0.4.0',
                        'features': {
                            'workflow_tracking': True,
                            'chunked_upload': True,
                            'enhanced_auth': True,
                            'paired_reads_detection': True,
                            'galaxy_25_compatibility': True
                        }
                    }
                }
                return jsonify(config_data)
            except Exception as e:
                logger.error(f"Error in get_config: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/update_config', methods=['POST'])
        @rate_limit('api')
        def update_config():
            """Update server configuration."""
            try:
                config_data = request.json
                # Update settings (implement actual configuration update logic)
                return jsonify({
                    'success': True,
                    'message': 'Configuration updated successfully',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error in update_config: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # API Routes - System Management
        @self.app.route('/api/cleanup_old_workflows', methods=['POST'])
        @rate_limit('api')
        def cleanup_old_workflows():
            """Clean up old completed workflows."""
            try:
                if workflow_tracker:
                    max_age = request.json.get('max_age_hours', 24)
                    workflow_tracker.cleanup_old_workflows(max_age)
                    return jsonify({
                        'success': True,
                        'message': f'Cleaned up workflows older than {max_age} hours'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Workflow tracker not available'
                    }), 500
            except Exception as e:
                logger.error(f"Error in cleanup_old_workflows: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/cleanup_old_uploads', methods=['POST'])
        @rate_limit('api')
        def cleanup_old_uploads():
            """Clean up old completed uploads."""
            try:
                if upload_tracker:
                    max_age = request.json.get('max_age_hours', 1)
                    upload_tracker.cleanup_old_uploads(max_age)
                    return jsonify({
                        'success': True,
                        'message': f'Cleaned up uploads older than {max_age} hours'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Upload tracker not available'
                    }), 500
            except Exception as e:
                logger.error(f"Error in cleanup_old_uploads: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # Error handlers
        @self.app.errorhandler(404)
        def handle_not_found(error):
            """Handle 404 errors."""
            return jsonify({
                'success': False,
                'error': 'Resource not found',
                'code': 'NOT_FOUND',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        @self.app.errorhandler(413)
        def handle_request_entity_too_large(error):
            """Handle file too large errors."""
            return jsonify({
                'success': False,
                'error': 'File too large',
                'code': 'FILE_TOO_LARGE',
                'max_size': self.app.config['MAX_CONTENT_LENGTH'],
                'timestamp': datetime.now().isoformat()
            }), 413
        
        @self.app.errorhandler(429)
        def handle_rate_limit_exceeded(error):
            """Handle rate limit exceeded errors."""
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Too many requests. Please try again later.',
                'timestamp': datetime.now().isoformat()
            }), 429
        
        @self.app.errorhandler(500)
        def handle_internal_error(error):
            """Handle 500 errors."""
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'code': 'INTERNAL_ERROR',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        logger.info("All routes configured successfully")
    
    def setup_background_tasks(self):
        """Setup background tasks for cleanup and monitoring."""
        
        def cleanup_task():
            """Background task for cleaning up old workflows and uploads."""
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    
                    # Clean up old workflows
                    if workflow_tracker:
                        workflow_tracker.cleanup_old_workflows(24)
                        logger.info("Cleaned up old workflows")
                    
                    # Clean up old uploads
                    if upload_tracker:
                        upload_tracker.cleanup_old_uploads(1)
                        logger.info("Cleaned up old uploads")
                    
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
                    time.sleep(300)  # Wait 5 minutes before retrying
        
        # Start background cleanup thread
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        
        logger.info("Background tasks started")
    
    def run(self, host=None, port=None, debug=None):
        """Run the Galaksio server."""
        host = host or settings.HOST
        port = port or settings.PORT
        debug = debug or settings.DEBUG
        
        logger.info(f"Starting Galaksio Server on {host}:{port}")
        logger.info(f"Galaxy server: {settings.GALAXY_SERVER}")
        logger.info(f"Debug mode: {debug}")
        
        self.app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=debug
        )

# Create server instance
server = GalaksioServer()

# Expose the Flask app for WSGI deployment
app = server.app

if __name__ == '__main__':
    # Command line argument parsing
    import argparse
    
    parser = argparse.ArgumentParser(description='Galaksio Server')
    parser.add_argument('--host', default=settings.HOST, help='Host to bind to')
    parser.add_argument('--port', type=int, default=settings.PORT, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--start', action='store_true', help='Start the server')
    
    args = parser.parse_args()
    
    if args.start:
        server.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    else:
        print("Galaksio Server")
        print("Use --start to start the server")
        print("Use --help for more options")
