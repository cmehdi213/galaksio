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
# Updated for Galaxy 25.0 compatibility
#

import os
import sys
import logging
import json
from flask import Flask, request, jsonify, send_from_directory, make_response
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
    testConnection
)

# Import error handlers
from servlets.ErrorHandler import register_error_handlers

# Initialize Flask app
def create_app():
    app = Flask(__name__, 
                static_folder='../client/src',
                template_folder='../client/src')
    
    # Configure CORS for modern browsers
    CORS(app, 
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
    Talisman(app, 
             force_https=False,  # Set to True in production
             strict_transport_security=False,
             session_cookie_secure=False,
             content_security_policy={
                 'default-src': "'self'",
                 'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
                 'style-src': "'self' 'unsafe-inline'",
                 'img-src': "'self' data: https:",
                 'font-src': "'self' data:",
                 'connect-src': "'self' *",  # Allow connections to Galaxy instances
             })
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add additional security headers."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
    
    # Add preflight request handler
    @app.route('/<path:path>', methods=['OPTIONS'])
    def handle_preflight(path):
        """Handle CORS preflight requests."""
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # Static file serving
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def static_files(path):
        return send_from_directory(app.static_folder, path)
    
    # API Routes
    @app.route('/api/test_connection', methods=['POST'])
    def test_connection():
        """Test connection to Galaxy instance."""
        try:
            result = testConnection(request, settings)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in test_connection: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/execute_workflow', methods=['POST'])
    def execute_workflow():
        """Execute a Galaxy workflow."""
        try:
            result = executeWorkflow(request, settings)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in execute_workflow: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/generate_workflow_report', methods=['POST'])
    def generate_workflow_report():
        """Generate workflow execution report."""
        try:
            result = generateWorkflowReport(request, settings)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in generate_workflow_report: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/get_workflow_status', methods=['POST'])
    def get_workflow_status():
        """Get workflow execution status."""
        try:
            result = getWorkflowStatus(request, settings)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in get_workflow_status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/upload_file', methods=['POST'])
    def upload_file():
        """Upload file to Galaxy."""
        try:
            result = uploadFile(request, settings)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in upload_file: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/get_upload_status', methods=['POST'])
    def get_upload_status():
        """Get file upload status."""
        try:
            result = getUploadStatus(request, settings)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in get_upload_status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({'status': 'healthy', 'version': '0.4.0'})
    
    return app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run the application
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
        threaded=True
    )
