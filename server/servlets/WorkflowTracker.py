#!/usr/bin/env python3
"""
Enhanced Workflow Tracker for Galaxy 25.0
Provides real-time workflow execution state tracking.
"""

import logging
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from bioblend.galaxy import GalaxyInstance

logger = logging.getLogger(__name__)

class WorkflowTracker:
    """Enhanced workflow execution tracker."""
    
    def __init__(self, galaxy_instance: GalaxyInstance):
        self.gi = galaxy_instance
        self.active_workflows = {}
        self.lock = threading.Lock()
        self.tracking_thread = None
        self.running = False
        self.max_retries = 3
        self.retry_delay = 1
    
    def start_tracking(self, workflow_id: str, invocation_id: str):
        """Start tracking a workflow execution."""
        with self.lock:
            self.active_workflows[invocation_id] = {
                'workflow_id': workflow_id,
                'invocation_id': invocation_id,
                'start_time': datetime.now(),
                'last_update': datetime.now(),
                'state': 'running',
                'steps': {},
                'progress': 0.0,
                'errors': [],
                'retry_count': 0
            }
        
        if not self.running:
            self._start_background_tracking()
    
    def stop_tracking(self, invocation_id: str):
        """Stop tracking a workflow execution."""
        with self.lock:
            if invocation_id in self.active_workflows:
                self.active_workflows[invocation_id]['state'] = 'completed'
                self.active_workflows[invocation_id]['end_time'] = datetime.now()
    
    def get_workflow_status(self, invocation_id: str) -> Optional[Dict]:
        """Get current status of a workflow execution."""
        with self.lock:
            return self.active_workflows.get(invocation_id)
    
    def get_all_active_workflows(self) -> List[Dict]:
        """Get all active workflow executions."""
        with self.lock:
            return list(self.active_workflows.values())
    
    def _start_background_tracking(self):
        """Start background thread for tracking workflow states."""
        self.running = True
        self.tracking_thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self.tracking_thread.start()
    
    def _tracking_loop(self):
        """Background loop for updating workflow states."""
        while self.running:
            try:
                self._update_workflow_states()
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _update_workflow_states(self):
        """Update states of all active workflows."""
        with self.lock:
            active_invocations = list(self.active_workflows.keys())
        
        for invocation_id in active_invocations:
            try:
                self._update_single_workflow(invocation_id)
            except Exception as e:
                logger.error(f"Error updating workflow {invocation_id}: {e}")
    
    def _update_single_workflow(self, invocation_id: str):
        """Update state of a single workflow execution."""
        try:
            # Get invocation details from Galaxy with retry logic
            invocation = self._get_invocation_with_retry(invocation_id)
            if not invocation:
                return
            
            workflow_state = invocation.get('state', 'unknown')
            
            with self.lock:
                if invocation_id in self.active_workflows:
                    workflow_info = self.active_workflows[invocation_id]
                    workflow_info['state'] = workflow_state
                    workflow_info['last_update'] = datetime.now()
                    workflow_info['retry_count'] = 0  # Reset retry count on success
                    
                    # Update step information
                    steps = invocation.get('steps', [])
                    workflow_info['steps'] = self._process_steps(steps)
                    
                    # Calculate progress
                    workflow_info['progress'] = self._calculate_progress(steps)
                    
                    # Check for errors
                    self._check_for_errors(steps, workflow_info)
                    
                    # Stop tracking if completed
                    if workflow_state in ['ok', 'error', 'deleted']:
                        workflow_info['end_time'] = datetime.now()
                        if workflow_state == 'error':
                            workflow_info['errors'].append("Workflow execution failed")
        
        except Exception as e:
            logger.error(f"Error updating workflow {invocation_id}: {e}")
            self._handle_update_error(invocation_id, e)
    
    def _get_invocation_with_retry(self, invocation_id: str) -> Optional[Dict]:
        """Get invocation details with retry logic."""
        for attempt in range(self.max_retries):
            try:
                return self.gi.invocations.show_invocation(invocation_id)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Retry {attempt + 1}/{self.max_retries} for invocation {invocation_id} after {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to get invocation {invocation_id} after {self.max_retries} attempts")
                    raise
        return None
    
    def _handle_update_error(self, invocation_id: str, error: Exception):
        """Handle errors in workflow update."""
        with self.lock:
            if invocation_id in self.active_workflows:
                workflow_info = self.active_workflows[invocation_id]
                workflow_info['retry_count'] += 1
                
                if workflow_info['retry_count'] >= self.max_retries:
                    workflow_info['state'] = 'error'
                    workflow_info['end_time'] = datetime.now()
                    workflow_info['errors'].append(f"Failed to update workflow status: {str(error)}")
    
    def _process_steps(self, steps: List[Dict]) -> Dict:
        """Process workflow steps and return structured information."""
        processed_steps = {}
        
        for step in steps:
            step_id = step.get('id')
            if step_id:
                processed_steps[step_id] = {
                    'id': step_id,
                    'name': step.get('workflow_step_label', step.get('id')),
                    'state': step.get('state', 'unknown'),
                    'job_id': step.get('job_id'),
                    'start_time': step.get('update_time'),
                    'end_time': None,
                    'error': None
                }
        
        return processed_steps
    
    def _calculate_progress(self, steps: List[Dict]) -> float:
        """Calculate workflow progress percentage."""
        if not steps:
            return 0.0
        
        completed = 0
        total = len(steps)
        
        for step in steps:
            state = step.get('state', '')
            if state in ['ok', 'error', 'deleted']:
                completed += 1
        
        return (completed / total) * 100 if total > 0 else 0.0
    
    def _check_for_errors(self, steps: List[Dict], workflow_info: Dict):
        """Check for errors in workflow steps."""
        for step in steps:
            state = step.get('state', '')
            if state == 'error':
                step_id = step.get('id')
                step_name = step.get('workflow_step_label', step_id)
                error_msg = f"Step '{step_name}' failed"
                
                if error_msg not in workflow_info['errors']:
                    workflow_info['errors'].append(error_msg)
    
    def cleanup_old_workflows(self, max_age_hours: int = 24):
        """Clean up old completed workflows."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            to_remove = []
            for invocation_id, workflow_info in self.active_workflows.items():
                if workflow_info['state'] in ['ok', 'error', 'deleted']:
                    end_time = workflow_info.get('end_time')
                    if end_time and end_time.timestamp() < cutoff_time:
                        to_remove.append(invocation_id)
            
            for invocation_id in to_remove:
                del self.active_workflows[invocation_id]
                logger.info(f"Cleaned up old workflow: {invocation_id}")

    def get_workflow_statistics(self) -> Dict:
        """Get workflow tracking statistics."""
        with self.lock:
            total_workflows = len(self.active_workflows)
            running_workflows = len([w for w in self.active_workflows.values() if w['state'] == 'running'])
            completed_workflows = len([w for w in self.active_workflows.values() if w['state'] in ['ok', 'error', 'deleted']])
            failed_workflows = len([w for w in self.active_workflows.values() if w['state'] == 'error'])
            
            return {
                'total_workflows': total_workflows,
                'running_workflows': running_workflows,
                'completed_workflows': completed_workflows,
                'failed_workflows': failed_workflows,
                'success_rate': (completed_workflows - failed_workflows) / max(completed_workflows, 1) * 100
            }

# Global workflow tracker instance
workflow_tracker = None

def get_workflow_tracker(galaxy_instance: GalaxyInstance) -> WorkflowTracker:
    """Get or create the global workflow tracker instance."""
    global workflow_tracker
    
    if workflow_tracker is None:
        workflow_tracker = WorkflowTracker(galaxy_instance)
    
    return workflow_tracker

def track_workflow_execution(galaxy_instance: GalaxyInstance, workflow_id: str, invocation_id: str):
    """Start tracking a workflow execution."""
    tracker = get_workflow_tracker(galaxy_instance)
    tracker.start_tracking(workflow_id, invocation_id)
    return tracker
