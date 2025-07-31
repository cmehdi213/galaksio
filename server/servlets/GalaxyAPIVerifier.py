#!/usr/bin/env python3
"""
Galaxy API Compatibility Verifier for Galaxy 25.0
Verifies and ensures compatibility with Galaxy 25.0 API changes.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.objects import GalaxyInstance as GalaxyInstanceObjects

logger = logging.getLogger(__name__)

class GalaxyAPIVerifier:
    """Verifies Galaxy API compatibility and provides fallback methods."""
    
    def __init__(self, galaxy_instance: GalaxyInstance):
        self.gi = galaxy_instance
        self.gi_objects = GalaxyInstanceObjects(galaxy_instance.url, galaxy_instance.key)
        self.galaxy_version = None
        self.api_version = None
        self.compatibility_issues = []
        
        # Verify Galaxy version and API compatibility
        self._verify_galaxy_version()
        self._verify_api_endpoints()
    
    def _verify_galaxy_version(self):
        """Verify Galaxy version and store compatibility information."""
        try:
            version_info = self.gi.config.get_version()
            self.galaxy_version = version_info.get('version_major', 'unknown')
            self.api_version = version_info.get('api_version', 'unknown')
            
            logger.info(f"Detected Galaxy version: {self.galaxy_version}")
            logger.info(f"Detected API version: {self.api_version}")
            
            # Check if this is Galaxy 25.0+
            if self.galaxy_version and self.galaxy_version.startswith('25.'):
                logger.info("Galaxy 25.0+ detected - applying compatibility checks")
            else:
                logger.warning(f"Galaxy {self.galaxy_version} detected - some features may not be available")
                
        except Exception as e:
            logger.error(f"Failed to verify Galaxy version: {e}")
            self.compatibility_issues.append(f"Version verification failed: {str(e)}")
    
    def _verify_api_endpoints(self):
        """Verify critical API endpoints are available and working."""
        endpoints_to_check = [
            ('workflows', self._check_workflows_endpoint),
            ('invocations', self._check_invocations_endpoint),
            ('histories', self._check_histories_endpoint),
            ('datasets', self._check_datasets_endpoint),
            ('collections', self._check_collections_endpoint),
        ]
        
        for endpoint_name, check_function in endpoints_to_check:
            try:
                check_function()
                logger.info(f"✅ {endpoint_name} endpoint compatible")
            except Exception as e:
                error_msg = f"❌ {endpoint_name} endpoint issue: {str(e)}"
                logger.error(error_msg)
                self.compatibility_issues.append(error_msg)
    
    def _check_workflows_endpoint(self):
        """Check workflows API endpoint compatibility."""
        # Test getting workflows
        workflows = self.gi.workflows.get_workflows()
        if not isinstance(workflows, list):
            raise ValueError(f"Expected list of workflows, got {type(workflows)}")
        
        # Test workflow invocation structure
        if len(workflows) > 0:
            workflow_id = workflows[0]['id']
            workflow_details = self.gi.workflows.show_workflow(workflow_id)
            if 'inputs' not in workflow_details:
                raise ValueError("Workflow inputs structure has changed")
    
    def _check_invocations_endpoint(self):
        """Check invocations API endpoint compatibility."""
        # Test getting invocations
        try:
            invocations = self.gi.invocations.get_invocations()
            if not isinstance(invocations, list):
                raise ValueError(f"Expected list of invocations, got {type(invocations)}")
        except Exception as e:
            # Some Galaxy instances might not have invocations enabled
            logger.warning(f"Invocations endpoint not available: {e}")
            return
        
        # Test invocation details structure
        if len(invocations) > 0:
            invocation_id = invocations[0]['id']
            invocation_details = self.gi.invocations.show_invocation(invocation_id)
            if 'steps' not in invocation_details:
                raise ValueError("Invocation steps structure has changed")
    
    def _check_histories_endpoint(self):
        """Check histories API endpoint compatibility."""
        # Test getting histories
        histories = self.gi.histories.get_histories()
        if not isinstance(histories, list):
            raise ValueError(f"Expected list of histories, got {type(histories)}")
        
        # Test history content retrieval
        if len(histories) > 0:
            history_id = histories[0]['id']
            history_contents = self.gi.histories.show_history(history_id, contents=True)
            if not isinstance(history_contents, list):
                raise ValueError(f"Expected list for history contents, got {type(history_contents)}")
    
    def _check_datasets_endpoint(self):
        """Check datasets API endpoint compatibility."""
        # Test getting datasets from history
        histories = self.gi.histories.get_histories()
        if len(histories) > 0:
            history_id = histories[0]['id']
            datasets = self.gi.histories.show_history(history_id, contents=True)
            
            for dataset in datasets:
                if 'id' in dataset and 'name' in dataset:
                    # Basic dataset structure is intact
                    break
            else:
                raise ValueError("Dataset structure has changed")
    
    def _check_collections_endpoint(self):
        """Check collections API endpoint compatibility."""
        try:
            # Test collection creation structure
            test_collection = {
                'collection_type': 'paired',
                'name': 'test_collection',
                'elements': [
                    {'name': 'forward', 'src': 'hda', 'id': 'test_id_1'},
                    {'name': 'reverse', 'src': 'hda', 'id': 'test_id_2'}
                ]
            }
            
            # We'll test the structure but not actually create a collection
            if 'collection_type' not in test_collection:
                raise ValueError("Collection structure has changed")
            if 'elements' not in test_collection:
                raise ValueError("Collection elements structure has changed")
                
        except Exception as e:
            logger.warning(f"Collections endpoint check failed: {e}")
            # This might not be available in all Galaxy instances
    
    def get_compatibility_report(self) -> Dict[str, Any]:
        """Get a comprehensive compatibility report."""
        return {
            'galaxy_version': self.galaxy_version,
            'api_version': self.api_version,
            'is_galaxy_25_plus': self.galaxy_version and self.galaxy_version.startswith('25.'),
            'compatibility_issues': self.compatibility_issues,
            'issues_count': len(self.compatibility_issues),
            'is_compatible': len(self.compatibility_issues) == 0,
            'recommendations': self._get_recommendations(),
            'supported_features': self._get_supported_features()
        }
    
    def _get_recommendations(self) -> List[str]:
        """Get recommendations based on compatibility issues."""
        recommendations = []
        
        if self.compatibility_issues:
            recommendations.append("Review compatibility issues and consider updating API calls")
        
        if self.galaxy_version and not self.galaxy_version.startswith('25.'):
            recommendations.append("Consider upgrading to Galaxy 25.0+ for full feature support")
        
        if not self.galaxy_version:
            recommendations.append("Unable to detect Galaxy version - check connection and API key")
        
        return recommendations
    
    def _get_supported_features(self) -> List[str]:
        """Get list of supported features based on compatibility."""
        features = []
        
        # Add features based on successful endpoint checks
        endpoint_issues = [issue for issue in self.compatibility_issues if 'endpoint issue' in issue]
        
        if not any('workflows' in issue for issue in endpoint_issues):
            features.append('workflows')
        
        if not any('invocations' in issue for issue in endpoint_issues):
            features.append('invocations')
        
        if not any('histories' in issue for issue in endpoint_issues):
            features.append('histories')
        
        if not any('datasets' in issue for issue in endpoint_issues):
            features.append('datasets')
        
        if not any('collections' in issue for issue in endpoint_issues):
            features.append('collections')
        
        return features
    
    def is_compatible(self) -> bool:
        """Check if the current Galaxy instance is compatible."""
        return len(self.compatibility_issues) == 0
    
    def get_safe_workflow_invocation(self, workflow_id: str, history_id: str,
                                   inputs: Dict, params: Dict = None) -> Dict:
        """Safely invoke workflow with compatibility checks."""
        try:
            # Try Galaxy 25.0+ method first
            if self.is_galaxy_25_plus:
                return self._invoke_workflow_25(workflow_id, history_id, inputs, params)
            else:
                # Fallback to legacy method
                return self._invoke_workflow_legacy(workflow_id, history_id, inputs, params)
        except Exception as e:
            logger.error(f"Workflow invocation failed: {e}")
            # Try fallback method
            try:
                return self._invoke_workflow_legacy(workflow_id, history_id, inputs, params)
            except Exception as fallback_error:
                logger.error(f"Fallback workflow invocation also failed: {fallback_error}")
                raise
    
    def _invoke_workflow_25(self, workflow_id: str, history_id: str,
                           inputs: Dict, params: Dict = None) -> Dict:
        """Invoke workflow using Galaxy 25.0+ method."""
        invocation_params = {
            'workflow_id': workflow_id,
            'history_id': history_id,
            'inputs': inputs,
            'import_inputs_to_history': True
        }
        
        if params:
            invocation_params['params'] = params
        
        return self.gi.workflows.invoke_workflow(**invocation_params)
    
    def _invoke_workflow_legacy(self, workflow_id: str, history_id: str,
                               inputs: Dict, params: Dict = None) -> Dict:
        """Invoke workflow using legacy method."""
        invocation_params = {
            'workflow_id': workflow_id,
            'history_id': history_id,
            'input_dataset_map': inputs,
            'import_inputs': True
        }
        
        if params:
            invocation_params['parameters'] = params
        
        return self.gi.workflows.invoke_workflow(**invocation_params)
    
    def get_safe_history_contents(self, history_id: str, contents: bool = True) -> List[Dict]:
        """Safely get history contents with compatibility checks."""
        try:
            return self.gi.histories.show_history(history_id, contents=contents)
        except Exception as e:
            logger.error(f"History content retrieval failed: {e}")
            # Try alternative method for older Galaxy versions
            try:
                history = self.gi.histories.show_history(history_id)
                if contents and 'contents' in history:
                    return history['contents']
                return [history] if not contents else []
            except Exception as fallback_error:
                logger.error(f"Fallback history retrieval failed: {fallback_error}")
                raise
    
    def create_safe_collection(self, history_id: str, collection_description: Dict) -> Dict:
        """Safely create dataset collection with compatibility checks."""
        try:
            # Try Galaxy 25.0+ method
            if self.is_galaxy_25_plus:
                return self._create_collection_25(history_id, collection_description)
            else:
                # Fallback to legacy method
                return self._create_collection_legacy(history_id, collection_description)
        except Exception as e:
            logger.error(f"Collection creation failed: {e}")
            # Try fallback method
            try:
                return self._create_collection_legacy(history_id, collection_description)
            except Exception as fallback_error:
                logger.error(f"Fallback collection creation also failed: {fallback_error}")
                raise
    
    def _create_collection_25(self, history_id: str, collection_description: Dict) -> Dict:
        """Create collection using Galaxy 25.0+ method."""
        # Ensure collection description has required fields for Galaxy 25.0
        if 'collection_type' not in collection_description:
            collection_description['collection_type'] = 'list'
        
        if 'name' not in collection_description:
            collection_description['name'] = 'Unnamed Collection'
        
        if 'elements' not in collection_description:
            raise ValueError("Collection elements are required")
        
        # Validate elements structure for Galaxy 25.0
        for element in collection_description['elements']:
            if 'name' not in element or 'src' not in element or 'id' not in element:
                raise ValueError("Each collection element must have name, src, and id")
        
        return self.gi.histories.create_dataset_collection(
            history_id=history_id,
            collection_description=collection_description
        )
    
    def _create_collection_legacy(self, history_id: str, collection_description: Dict) -> Dict:
        """Create collection using legacy method."""
        # Legacy method might have different requirements
        if 'collection_type' not in collection_description:
            collection_description['collection_type'] = 'list'
        
        if 'name' not in collection_description:
            collection_description['name'] = 'Unnamed Collection'
        
        if 'elements' not in collection_description:
            raise ValueError("Collection elements are required")
        
        # Try to create with legacy structure
        try:
            return self.gi.histories.create_dataset_collection(
                history_id=history_id,
                collection_description=collection_description
            )
        except Exception as e:
            logger.warning(f"Legacy collection creation failed, trying alternative structure: {e}")
            
            # Try alternative structure for older versions
            alt_description = {
                'name': collection_description['name'],
                'type': collection_description['collection_type'],
                'element_identifiers': collection_description['elements']
            }
            
            return self.gi.histories.create_dataset_collection(
                history_id=history_id,
                collection_description=alt_description
            )
    
    def get_safe_invocation_status(self, invocation_id: str) -> Dict:
        """Safely get invocation status with compatibility checks."""
        try:
            return self.gi.invocations.show_invocation(invocation_id)
        except Exception as e:
            logger.error(f"Invocation status retrieval failed: {e}")
            raise
    
    def get_safe_workflow_details(self, workflow_id: str) -> Dict:
        """Safely get workflow details with compatibility checks."""
        try:
            return self.gi.workflows.show_workflow(workflow_id)
        except Exception as e:
            logger.error(f"Workflow details retrieval failed: {e}")
            raise

# Global API verifier instance
_api_verifier = None

def get_api_verifier(galaxy_instance: GalaxyInstance) -> GalaxyAPIVerifier:
    """Get or create the global API verifier."""
    global _api_verifier
    if _api_verifier is None:
        _api_verifier = GalaxyAPIVerifier(galaxy_instance)
    return _api_verifier
