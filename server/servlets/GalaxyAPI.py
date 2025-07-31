"""
Galaksio Galaxy API Integration
Updated for Galaxy 25.0 with enhanced compatibility layer and error handling
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
from .GalaxyAPIVerifier import get_api_verifier

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
        
        # Get API verifier for compatibility checks
        verifier = get_api_verifier(gi)
        
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
            'invocation': invocation,
            'compatibility_report': verifier.get_compatibility_report()
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
        inputs = request.json.get("inputs", {})
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Get API verifier for compatibility checks
        verifier = get_api_verifier(gi)
        
        # Use safe workflow invocation with compatibility layer
        invocation = verifier.get_safe_workflow_invocation(
            workflow_id=workflow_id,
            history_id=history_id,
            inputs=inputs,
            params=parameters
        )
        
        invocation_id = invocation.get("id")
        
        # Start tracking the workflow execution
        if invocation_id:
            tracker = get_workflow_tracker(gi)
            tracker.start_tracking(workflow_id, invocation_id)
        
        return {
            'success': True,
            'invocation_id': invocation_id,
            'message': 'Workflow execution started',
            'compatibility_report': verifier.get_compatibility_report()
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
            # Fallback to direct Galaxy API call with compatibility layer
            verifier = get_api_verifier(gi)
            try:
                invocation = gi.invocations.show_invocation(invocation_id)
                return {
                    'success': True,
                    'status': {
                        'invocation_id': invocation_id,
                        'state': invocation.get('state'),
                        'steps': invocation.get('steps', []),
                        'compatibility_report': verifier.get_compatibility_report()
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get invocation status: {e}")
                return handle_galaxy_error(e, {'function': 'getWorkflowStatus'})
        
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
        
        # Get API verifier for compatibility report
        verifier = get_api_verifier(auth.get_instance())
        compatibility_report = verifier.get_compatibility_report()
        
        return {
            'success': success,
            'message': message,
            'compatibility_report': compatibility_report
        }
        
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return handle_galaxy_error(e, {'function': 'testConnection'})

def getCompatibilityReport(request, settings):
    """
    Get Galaxy API compatibility report
    """
    try:
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Get API verifier
        verifier = get_api_verifier(gi)
        compatibility_report = verifier.get_compatibility_report()
        
        return {
            'success': True,
            'compatibility_report': compatibility_report
        }
        
    except Exception as e:
        logger.error(f"Error getting compatibility report: {e}")
        return handle_galaxy_error(e, {'function': 'getCompatibilityReport'})

def detectPairedReads(request, settings):
    """
    Detect paired-end reads in a Galaxy history.
    """
    try:
        history_id = request.json.get("history_id")
        
        if not history_id:
            return {
                'success': False,
                'error': 'History ID is required'
            }
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Get API verifier for compatibility checks
        verifier = get_api_verifier(gi)
        
        # Get paired reads handler
        from .PairedReadsHandler import get_paired_reads_handler
        paired_handler = get_paired_reads_handler(gi)
        
        # Detect paired reads
        result = paired_handler.detect_paired_reads(history_id)
        
        # Add compatibility report
        result['compatibility_report'] = verifier.get_compatibility_report()
        
        return result
        
    except Exception as e:
        logger.error(f"Error detecting paired reads: {e}")
        return handle_galaxy_error(e, {'function': 'detectPairedReads'})

def createPairedCollection(request, settings):
    """
    Create a paired collection from detected paired reads.
    """
    try:
        history_id = request.json.get("history_id")
        paired_group = request.json.get("paired_group")
        
        if not history_id or not paired_group:
            return {
                'success': False,
                'error': 'History ID and paired group are required'
            }
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Get API verifier for compatibility checks
        verifier = get_api_verifier(gi)
        
        # Get paired reads handler
        from .PairedReadsHandler import get_paired_reads_handler
        paired_handler = get_paired_reads_handler(gi)
        
        # Create paired collection using safe method
        collection_description = {
            'collection_type': 'paired',
            'name': paired_group.get('suggested_name', 'paired_collection'),
            'elements': [
                {
                    'name': 'forward',
                    'src': 'hda',
                    'id': paired_group['files'][0]['id']
                },
                {
                    'name': 'reverse',
                    'src': 'hda',
                    'id': paired_group['files'][1]['id']
                }
            ]
        }
        
        result = verifier.create_safe_collection(history_id, collection_description)
        
        return {
            'success': True,
            'collection_id': result.get('id'),
            'collection_name': paired_group.get('suggested_name', 'paired_collection'),
            'message': f'Created paired collection: {paired_group.get("suggested_name", "paired_collection")}',
            'compatibility_report': verifier.get_compatibility_report()
        }
        
    except Exception as e:
        logger.error(f"Error creating paired collection: {e}")
        return handle_galaxy_error(e, {'function': 'createPairedCollection'})

def autoPairAllReads(request, settings):
    """
    Automatically detect and pair all reads in a history.
    """
    try:
        history_id = request.json.get("history_id")
        create_collections = request.json.get("create_collections", True)
        
        if not history_id:
            return {
                'success': False,
                'error': 'History ID is required'
            }
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Get API verifier for compatibility checks
        verifier = get_api_verifier(gi)
        
        # Get paired reads handler
        from .PairedReadsHandler import get_paired_reads_handler
        paired_handler = get_paired_reads_handler(gi)
        
        # Auto-pair all reads
        result = paired_handler.auto_pair_all_reads(history_id, create_collections)
        
        # Add compatibility report
        result['compatibility_report'] = verifier.get_compatibility_report()
        
        return result
        
    except Exception as e:
        logger.error(f"Error in auto-pairing all reads: {e}")
        return handle_galaxy_error(e, {'function': 'autoPairAllReads'})

def getPairedReadPatterns(request, settings):
    """
    Get supported paired read patterns.
    """
    try:
        from .PairedReadsHandler import PairedReadsHandler
        
        patterns = []
        for pattern, replacement in PairedReadsHandler.PAIRED_READ_PATTERNS:
            patterns.append({
                'pattern': pattern,
                'replacement': replacement,
                'description': f"Files matching '{pattern}' will be paired with '{replacement}'"
            })
        
        return {
            'success': True,
            'patterns': patterns,
            'supported_extensions': list(PairedReadsHandler.SUPPORTED_EXTENSIONS)
        }
        
    except Exception as e:
        logger.error(f"Error getting paired read patterns: {e}")
        return handle_galaxy_error(e, {'function': 'getPairedReadPatterns'})

def getHistoryContents(request, settings):
    """
    Get history contents with Galaxy 25.0 compatibility
    """
    try:
        history_id = request.json.get("history_id")
        
        if not history_id:
            return {
                'success': False,
                'error': 'History ID is required'
            }
        
        # Get authenticated Galaxy instance
        gi = get_galaxy_instance(settings)
        
        # Get API verifier for compatibility checks
        verifier = get_api_verifier(gi)
        
        # Get history contents using safe method
        contents = verifier.get_safe_history_contents(history_id, contents=True)
        
        return {
            'success': True,
            'contents': contents,
            'count': len(contents),
            'compatibility_report': verifier.get_compatibility_report()
        }
        
    except Exception as e:
        logger.error(f"Error getting history contents: {e}")
        return handle_galaxy_error(e, {'function': 'getHistoryContents'})
