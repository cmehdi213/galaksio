#!/usr/bin/env python3
"""
Galaxy API Compatibility Test Suite
Tests compatibility with different Galaxy versions, especially 25.0+
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from servlets.GalaxyAPIVerifier import GalaxyAPIVerifier
from servlets.GalaxyAPI import get_galaxy_instance, get_auth_handler
from servlets.AuthHandler import authenticate_galaxy
from resources.galaxy_settings import settings

class TestGalaxyCompatibility(unittest.TestCase):
    """Test Galaxy API compatibility across versions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_galaxy_instance = Mock()
        self.mock_galaxy_instance.url = "https://test.galaxy.org"
        self.mock_galaxy_instance.key = "test_api_key"
        
    def test_verifier_initialization(self):
        """Test Galaxy API verifier initialization."""
        with patch.object(self.mock_galaxy_instance, 'config') as mock_config, \
             patch.object(self.mock_galaxy_instance, 'workflows') as mock_workflows, \
             patch.object(self.mock_galaxy_instance, 'invocations') as mock_invocations, \
             patch.object(self.mock_galaxy_instance, 'histories') as mock_histories:
            mock_config.get_version.return_value = {
                'version_major': '25.0',
                'api_version': 'v2'
            }
            mock_workflows.get_workflows.return_value = []
            mock_invocations.get_invocations.return_value = []
            mock_histories.get_histories.return_value = []
            mock_histories.show_history.return_value = []
            
            verifier = GalaxyAPIVerifier(self.mock_galaxy_instance)
            
            self.assertEqual(verifier.galaxy_version, '25.0')
            self.assertEqual(verifier.api_version, 'v2')
            self.assertTrue(verifier.is_galaxy_25_plus)
    
    def test_galaxy_25_compatibility(self):
        """Test Galaxy 25.0 specific compatibility."""
        with patch.object(self.mock_galaxy_instance, 'config') as mock_config, \
             patch.object(self.mock_galaxy_instance, 'workflows') as mock_workflows, \
             patch.object(self.mock_galaxy_instance, 'invocations') as mock_invocations, \
             patch.object(self.mock_galaxy_instance, 'histories') as mock_histories:
            
            # Mock version info
            mock_config.get_version.return_value = {
                'version_major': '25.0',
                'api_version': 'v2'
            }
            
            # Mock workflows
            mock_workflows.get_workflows.return_value = [
                {'id': 'test_workflow', 'name': 'Test Workflow'}
            ]
            mock_workflows.show_workflow.return_value = {
                'id': 'test_workflow',
                'inputs': {'input1': {'type': 'data'}}
            }
            
            # Mock invocations
            mock_invocations.get_invocations.return_value = []
            
            # Mock histories
            mock_histories.get_histories.return_value = [
                {'id': 'test_history', 'name': 'Test History'}
            ]
            mock_histories.show_history.return_value = [{'id': 'd1', 'name': 'd1'}]
            
            verifier = GalaxyAPIVerifier(self.mock_galaxy_instance)
            
            # Should be compatible
            self.assertTrue(verifier.is_compatible())
            self.assertEqual(len(verifier.compatibility_issues), 0)
    
    def test_legacy_galaxy_compatibility(self):
        """Test compatibility with older Galaxy versions."""
        with patch.object(self.mock_galaxy_instance, 'config') as mock_config, \
             patch.object(self.mock_galaxy_instance, 'workflows') as mock_workflows, \
             patch.object(self.mock_galaxy_instance, 'invocations') as mock_invocations, \
             patch.object(self.mock_galaxy_instance, 'histories') as mock_histories:
            
            # Mock older version info
            mock_config.get_version.return_value = {
                'version_major': '21.09',
                'api_version': 'v1'
            }
            
            # Mock basic endpoints
            mock_workflows.get_workflows.return_value = [
                {'id': 'test_workflow', 'name': 'Test Workflow'}
            ]
            mock_workflows.show_workflow.return_value = {
                'id': 'test_workflow',
                'inputs': {'input1': {'type': 'data'}}
            }
            
            mock_invocations.get_invocations.return_value = []

            mock_histories.get_histories.return_value = [
                {'id': 'test_history', 'name': 'Test History'}
            ]
            mock_histories.show_history.return_value = [{'id': 'd1', 'name': 'd1'}]
            
            verifier = GalaxyAPIVerifier(self.mock_galaxy_instance)
            
            # Should still be compatible with basic features
            self.assertTrue(verifier.is_compatible())
            self.assertFalse(verifier.is_galaxy_25_plus)
    
    def test_workflow_invocation_compatibility(self):
        """Test workflow invocation compatibility."""
        with patch.object(self.mock_galaxy_instance, 'config') as mock_config, \
             patch.object(self.mock_galaxy_instance, 'workflows') as mock_workflows, \
             patch.object(self.mock_galaxy_instance, 'invocations') as mock_invocations, \
             patch.object(self.mock_galaxy_instance, 'histories') as mock_histories:
            mock_config.get_version.return_value = {
                'version_major': '25.0',
                'api_version': 'v2'
            }
            mock_workflows.get_workflows.return_value = []
            mock_invocations.get_invocations.return_value = []
            mock_histories.get_histories.return_value = []
            mock_histories.show_history.return_value = []
            
            verifier = GalaxyAPIVerifier(self.mock_galaxy_instance)
            
            # Test Galaxy 25.0+ method
            with patch.object(self.mock_galaxy_instance.workflows, 'invoke_workflow') as mock_invoke:
                mock_invoke.return_value = {'id': 'test_invocation'}
                
                result = verifier.get_safe_workflow_invocation(
                    'test_workflow',
                    'test_history',
                    {'input1': 'test_input'},
                    {'param1': 'test_param'}
                )
                
                self.assertEqual(result['id'], 'test_invocation')
                mock_invoke.assert_called_once_with(
                    workflow_id='test_workflow',
                    history_id='test_history',
                    inputs={'input1': 'test_input'},
                    params={'param1': 'test_param'},
                    import_inputs_to_history=True
                )
    
    def test_collection_creation_compatibility(self):
        """Test collection creation compatibility."""
        with patch.object(self.mock_galaxy_instance, 'config') as mock_config, \
             patch.object(self.mock_galaxy_instance, 'workflows') as mock_workflows, \
             patch.object(self.mock_galaxy_instance, 'invocations') as mock_invocations, \
             patch.object(self.mock_galaxy_instance, 'histories') as mock_histories:
            mock_config.get_version.return_value = {
                'version_major': '25.0',
                'api_version': 'v2'
            }
            mock_workflows.get_workflows.return_value = []
            mock_invocations.get_invocations.return_value = []
            mock_histories.get_histories.return_value = []
            mock_histories.show_history.return_value = []
            
            verifier = GalaxyAPIVerifier(self.mock_galaxy_instance)
            
            collection_description = {
                'collection_type': 'paired',
                'name': 'test_collection',
                'elements': [
                    {'name': 'forward', 'src': 'hda', 'id': 'test_id_1'},
                    {'name': 'reverse', 'src': 'hda', 'id': 'test_id_2'}
                ]
            }
            
            # Test Galaxy 25.0+ method
            with patch.object(self.mock_galaxy_instance.histories, 'create_dataset_collection') as mock_create:
                mock_create.return_value = {'id': 'test_collection'}
                
                result = verifier.create_safe_collection('test_history', collection_description)
                
                self.assertEqual(result['id'], 'test_collection')
                mock_create.assert_called_once()
    
    def test_history_contents_compatibility(self):
        """Test history contents retrieval compatibility."""
        with patch.object(self.mock_galaxy_instance, 'config') as mock_config, \
             patch.object(self.mock_galaxy_instance, 'workflows') as mock_workflows, \
             patch.object(self.mock_galaxy_instance, 'invocations') as mock_invocations, \
             patch.object(self.mock_galaxy_instance, 'histories') as mock_histories:
            mock_config.get_version.return_value = {
                'version_major': '25.0',
                'api_version': 'v2'
            }
            mock_workflows.get_workflows.return_value = []
            mock_invocations.get_invocations.return_value = []
            mock_histories.get_histories.return_value = []
            
            verifier = GalaxyAPIVerifier(self.mock_galaxy_instance)
            
            # Test safe history contents retrieval
            with patch.object(self.mock_galaxy_instance.histories, 'show_history') as mock_show:
                mock_show.return_value = [
                    {'id': 'dataset1', 'name': 'Test Dataset 1'},
                    {'id': 'dataset2', 'name': 'Test Dataset 2'}
                ]
                
                result = verifier.get_safe_history_contents('test_history', contents=True)
                
                self.assertEqual(len(result), 2)
                self.assertEqual(result[0]['id'], 'dataset1')
                mock_show.assert_called_once_with('test_history', contents=True)

class TestGalaxyAPIIntegration(unittest.TestCase):
    """Test Galaxy API integration with compatibility layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_settings = Mock()
        self.test_settings.GALAXY_SERVER = "https://test.galaxy.org"
    
    @patch('servlets.GalaxyAPI.get_auth_handler')
    @patch('servlets.GalaxyAPI.authenticate_galaxy')
    def test_get_galaxy_instance_compatibility(self, mock_auth, mock_get_handler):
        """Test Galaxy instance retrieval with compatibility."""
        # Mock authentication
        mock_auth.return_value = (Mock(), True, "Success")
        mock_handler = Mock()
        mock_handler.get_instance.return_value = Mock()
        mock_get_handler.return_value = mock_handler
        
        # Import and test
        from servlets.GalaxyAPI import get_galaxy_instance
        
        result = get_galaxy_instance(self.test_settings)
        
        self.assertIsNotNone(result)
        mock_get_handler.assert_called_once()
        mock_handler.get_instance.assert_called_once()

if __name__ == '__main__':
    unittest.main()
