"""
Updated server.py for Galaxy 25.0 compatibility
"""

import logging
import re
from os import remove as removeFile
import requests
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.objects import GalaxyInstance as GalaxyInstanceObjects
from flask import (
    Flask, json, jsonify, request, Response as flask_response,
    send_from_directory, render_template_string
)
from .servlets import AdminFunctions
from .servlets import GalaxyAPI

# HTML regex patterns remain the same
HTML_REGEX = re.compile(r'((?:src|action|href)=["\'])/')
JQUERY_REGEX = re.compile(r'(\$\.(?:get|post)\(["\'])/')
JS_LOCATION_REGEX = re.compile(r'((?:window|document)\.location.\*=.\*["\'])/')
CSS_REGEX = re.compile(r'(url\(["\']?)/')
REGEXES = [HTML_REGEX, JQUERY_REGEX, JS_LOCATION_REGEX, CSS_REGEX]

class Application(object):
    def __init__(self):
        self.app = Flask(__name__)
        self.isFirstLaunch = False
        self.isDocker = False
        self.settings = AdminFunctions.readConfigurationFile()
        self.app.config['MAX_CONTENT_LENGTH'] = self.settings.MAX_CONTENT_LENGTH * pow(1024, 2)
        
        # Configure logging
        logging.basicConfig(level=getattr(logging, self.settings.LOG_LEVEL))
        self.log = logging.getLogger(__name__)
        
        self.log("Starting application...")
        self.log(f"Galaksio starting with Galaxy server: {self.settings.GALAXY_SERVER}")
        
        # Set up routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all Flask routes"""
        
        @self.app.route(self.settings.SERVER_SUBDOMAIN + '/')
        def main():
            if self.isFirstLaunch:
                self.log("First launch detected, showing install form")
                return send_from_directory(self.settings.ROOT_DIRECTORY + 'client/src/', 'install.html')
            else:
                return send_from_directory(self.settings.ROOT_DIRECTORY + 'client/src/', 'index.html')

        @self.app.route(self.settings.SERVER_SUBDOMAIN + '/<path:filename>')
        def get_static(filename):
            return send_from_directory(self.settings.ROOT_DIRECTORY + 'client/src/', filename)

        @self.app.route(self.settings.SERVER_SUBDOMAIN + '/tmp/<path:filename>')
        def get_tmp_static(filename):
            return send_from_directory(self.settings.TMP_DIRECTORY, filename)

        @self.app.route(self.settings.SERVER_SUBDOMAIN + '/api/<path:service>', methods=['OPTIONS', 'POST', 'GET', 'DELETE', 'PUT'])
        def forward_request(service, method=None):
            return self.handle_api_request(service, method)

        @self.app.route(self.settings.SERVER_SUBDOMAIN + '/other/<path:service>', methods=['OPTIONS', 'POST', 'GET', 'DELETE', 'PUT'])
        def other_request(service, method=None):
            return self.handle_other_request(service, method)

    def handle_api_request(self, service, method=None):
        """Handle API requests with Galaxy 25.0 compatibility"""
        try:
            auth = None
            if request.authorization is not None and len(request.authorization) > 0:
                auth = ()
                for i in request.authorization:
                    auth = auth + (request.authorization[i],)

            if method is None:
                method = request.method

            if service == "upload/":
                return self.handle_file_upload()
            elif service == "signup/":
                return self.handle_signup()
            else:
                return self.forward_to_galaxy_api(service, method, auth)

        except Exception as e:
            self.log(f"Error in API request: {str(e)}")
            return jsonify({'error': str(e)}), 500

    def handle_file_upload(self):
        """Handle file uploads with Galaxy 25.0 compatibility"""
        try:
            if self.settings.SAFE_UPLOAD:
                self.log("New upload request detected")
                
                data = dict(request.form)
                tmp_files = AdminFunctions.storeTmpFiles(request.files, self.settings.TMP_DIRECTORY)
                self.log("All files were temporary stored at: " + ", ".join(tmp_files))
                
                history_id = data.get("history_id")[0]
                galaxy_key = data.get("key")[0]
                
                # Use updated BioBlend for Galaxy 25.0
                gi = GalaxyInstance(self.settings.GALAXY_SERVER, galaxy_key)
                responses = []
                
                for tmp_file in tmp_files:
                    try:
                        response = gi.tools.upload_file(tmp_file, history_id)
                        responses.append(response)
                        self.log(f"Successfully uploaded file: {tmp_file}")
                    except Exception as e:
                        self.log(f"Error uploading file {tmp_file}: {str(e)}")
                        responses.append({'error': str(e), 'file': tmp_file})
                
                # Clean up temporary files
                for tmp_file in tmp_files:
                    try:
                        removeFile(tmp_file)
                    except:
                        pass
                
                return jsonify({'success': True, 'responses': responses})
            else:
                # Forward directly to Galaxy API
                return self.forward_to_galaxy_api("tools", request.method, None)

        except Exception as e:
            self.log(f"Error in file upload: {str(e)}")
            return jsonify({'error': str(e)}), 500

    def handle_signup(self):
        """Handle user signup"""
        try:
            self.log("New sign up request detected")
            service = "/user/create?cntrller=user"
            data = dict(request.form)
            
            resp = requests.request(
                method=request.method,
                url=self.settings.GALAXY_SERVER + service,
                params=dict(request.args),
                headers={'content-type': 'application/x-www-form-urlencoded'},
                data=data,
                auth=request.authorization,
                cookies=request.cookies,
                allow_redirects=False
            )
            
            return self.create_response(resp)
            
        except Exception as e:
            self.log(f"Error in signup: {str(e)}")
            return jsonify({'error': str(e)}), 500

    def forward_to_galaxy_api(self, service, method, auth):
        """Forward request to Galaxy API"""
        try:
            service = "/api/" + service
            self.log(f"Forwarding request to Galaxy API: {service}")
            
            resp = requests.request(
                method=method,
                url=self.settings.GALAXY_SERVER + service,
                params=dict(request.args),
                data=request.get_data(),
                auth=auth,
                cookies=request.cookies,
                allow_redirects=False
            )
            
            return self.create_response(resp)
            
        except Exception as e:
            self.log(f"Error forwarding to Galaxy API: {str(e)}")
            return jsonify({'error': str(e)}), 500

    def handle_other_request(self, service, method=None):
        """Handle other special requests"""
        try:
            if service == 'workflows/report/':
                file_path = GalaxyAPI.generateWorkflowReport(request, self.settings)
                return jsonify({'success': True, 'path': file_path})
            return ""
            
        except Exception as e:
            self.log(f"Error in other request: {str(e)}")
            return jsonify({'error': str(e)}), 500

    def create_response(self, resp):
        """Create Flask response from requests response"""
        headers = []
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in list(resp.raw.headers.items()) 
                   if name.lower() not in excluded_headers]
        
        self.log("Done! Returning response...")
        response = flask_response(resp.content, resp.status_code, headers)
        return response

    def run(self, host=None, port=None, debug=None):
        """Run the Flask application"""
        host = host or self.settings.SERVER_HOST
        port = port or self.settings.SERVER_PORT
        debug = debug or False
        
        self.log(f"Starting Galaksio server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
