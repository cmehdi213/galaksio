"""
Galaksio Galaxy API Integration
Updated for Galaxy 25.0 with enhanced authentication and error handling
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

from os import path as osPath
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.objects import GalaxyInstance as GalaxyInstanceObjects
import logging
import json
from flask import request, jsonify, current_app

# Import new handlers
from .AuthHandler import authenticate_galaxy, GalaxyAuthHandler
from .WorkflowTracker import get_workflow_tracker, track_workflow_execution
from .ErrorHandler import handle_galaxy_error, GalaksioError, AuthenticationError

logger = logging.getLogger(__name__)

# Global authentication handler
auth_handler = None

def get_auth_handler(settings):
    """Get or create the global authentication handler."""
    global auth_handler
    
    if auth_handler is None:
        galaxy_key = request.values.get("key") or request.json.get("key") if request else None
        auth_handler, success, message = authenticate_galaxy(settings.GALAXY_SERVER, galaxy_key)
        
        if not success:
            raise AuthenticationError(message)
    
    return auth_handler

def get_galaxy_instance(settings):
    """Get authenticated Galaxy instance."""
    try:
        auth = get_auth_handler(settings)
        return auth.get_instance()
    except Exception as e:
        logger.error(f"Failed to get Galaxy instance: {e}")
        raise AuthenticationError(f"Authentication failed: {str(e)}")

def get_galaxy_objects_instance(settings):
    """Get authenticated Galaxy objects instance."""
    try:
        auth = get_auth_handler(settings)
        return auth.get_objects_instance()
    except Exception as e:
        logger.error(f"Failed to get Galaxy objects instance: {e}")
        raise AuthenticationError(f"Authentication failed: {str(e)}")

def generateWorkflowReport(request, settings):
    """
    Generate a workflow report using Galaxy 25.0 compatible API calls
    """
    try:
        # Get the invocation and workflow data
        invocation = request.json.get("invocation")
        workflow = request.json.get("workflow")
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        gi_objects = get_galaxy_objects_instance(settings)
        
        workflow_steps = {}
        for step in workflow.get("steps"):
            workflow_steps[step.get("uuid")] = step
        
        for step in invocation.get("steps"):
            workflow_step = workflow_steps.get(step.get("workflow_step_uuid"))
            if workflow_step:
                workflow_step["state"] = step.get("state")
                workflow_step["job_id"] = step.get("job_id")
                
                try:
                    # Get job information with error handling
                    job_info = gi.jobs.show_job(step.get("job_id"))
                    workflow_step["job_info"] = job_info
                except Exception as e:
                    logger.warning(f"Could not get job info for {step.get('job_id')}: {e}")
        
        return {
            'success': True,
            'workflow': workflow,
            'invocation': invocation
        }
        
    except Exception as e:
        logger.error(f"Error generating workflow report: {e}")
        return handle_galaxy_error(e, {'function': 'generateWorkflowReport'})

def executeWorkflow(request, settings):
    """
    Execute a workflow using Galaxy 25.0 compatible API calls
    """
    try:
        # Get workflow parameters
        workflow_id = request.json.get("workflow_id")
        history_id = request.json.get("history_id")
        parameters = request.json.get("parameters", {})
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Execute workflow
        invocation = gi.workflows.invoke_workflow(
            workflow_id,
            history_id=history_id,
            inputs=parameters.get("inputs", {}),
            params=parameters.get("params", {}),
            import_inputs_to_history=True
        )
        
        invocation_id = invocation.get("id")
        
        # Start tracking the workflow execution
        if invocation_id:
            tracker = get_workflow_tracker(gi)
            tracker.start_tracking(workflow_id, invocation_id)
        
        return {
            'success': True,
            'invocation_id': invocation_id,
            'message': 'Workflow execution started'
        }
        
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return handle_galaxy_error(e, {'function': 'executeWorkflow'})

def getWorkflowStatus(request, settings):
    """
    Get the status of a workflow execution
    """
    try:
        invocation_id = request.json.get("invocation_id")
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Get workflow tracker
        tracker = get_workflow_tracker(gi)
        status = tracker.get_workflow_status(invocation_id)
        
        if status:
            return {
                'success': True,
                'status': status
            }
        else:
            # Fallback to direct Galaxy API call
            invocation = gi.invocations.show_invocation(invocation_id)
            return {
                'success': True,
                'status': {
                    'invocation_id': invocation_id,
                    'state': invocation.get('state'),
                    'steps': invocation.get('steps', [])
                }
            }
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        return handle_galaxy_error(e, {'function': 'getWorkflowStatus'})

def uploadFile(request, settings):
    """
    Upload a file to Galaxy using enhanced file upload handler
    """
    try:
        # Import here to avoid circular imports
        from .FileUploadHandler import FileUploadHandler, get_upload_tracker
        
        # Get parameters
        history_id = request.form.get("history_id")
        file_obj = request.files.get("file")
        filename = file_obj.filename if file_obj else None
        
        if not file_obj or not history_id:
            return {
                'success': False,
                'error': 'Missing required parameters'
            }
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Create upload handler
        upload_handler = FileUploadHandler(gi)
        
        # Generate upload ID
        import uuid
        upload_id = str(uuid.uuid4())
        
        # Start tracking upload
        upload_tracker = get_upload_tracker()
        upload_tracker.start_upload(upload_id, filename, 0)  # Size will be updated
        
        # Progress callback
        def progress_callback(bytes_uploaded):
            upload_tracker.update_progress(upload_id, bytes_uploaded)
        
        # Upload file
        result = upload_handler.upload_file(file_obj, filename, history_id, progress_callback)
        
        # Complete tracking
        upload_tracker.complete_upload(upload_id, result)
        
        # Add upload ID to result
        result['upload_id'] = upload_id
        
        return result
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return handle_galaxy_error(e, {'function': 'uploadFile'})

def getUploadStatus(request, settings):
    """
    Get the status of a file upload
    """
    try:
        from .FileUploadHandler import get_upload_tracker
        
        upload_id = request.json.get("upload_id")
        
        if not upload_id:
            return {
                'success': False,
                'error': 'Missing upload_id'
            }
        
        # Get upload tracker
        upload_tracker = get_upload_tracker()
        status = upload_tracker.get_upload_status(upload_id)
        
        if status:
            return {
                'success': True,
                'status': status
            }
        else:
            return {
                'success': False,
                'error': 'Upload not found'
            }
        
    except Exception as e:
        logger.error(f"Error getting upload status: {e}")
        return handle_galaxy_error(e, {'function': 'getUploadStatus'})

def testConnection(request, settings):
    """
    Test connection to Galaxy instance
    """
    try:
        # Get authentication handler
        auth = get_auth_handler(settings)
        success, message = auth.test_connection()
        
        return {
            'success': success,
            'message': message
        }
        
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return handle_galaxy_error(e, {'function': 'testConnection'})
