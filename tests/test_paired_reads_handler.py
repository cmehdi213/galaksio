import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from servlets.PairedReadsHandler import PairedReadsHandler

class TestPairedReadsHandler(unittest.TestCase):
    def setUp(self):
        self.mock_galaxy_instance = Mock()

    @patch('servlets.GalaxyAPIVerifier.get_api_verifier')
    def test_detect_paired_reads_simple(self, mock_get_api_verifier):
        mock_verifier = Mock()
        mock_verifier.get_safe_history_contents.return_value = [
            {'id': '1', 'name': 'test_R1.fastq', 'file_size': 100, 'data_type': 'fastq'},
            {'id': '2', 'name': 'test_R2.fastq', 'file_size': 100, 'data_type': 'fastq'},
            {'id': '3', 'name': 'unpaired.fastq', 'file_size': 100, 'data_type': 'fastq'},
        ]
        mock_get_api_verifier.return_value = mock_verifier

        handler = PairedReadsHandler(self.mock_galaxy_instance)

        result = handler.detect_paired_reads('history_id')

        self.assertEqual(len(result['paired_groups']), 1)
        self.assertEqual(len(result['unpaired_files']), 1)
        self.assertEqual(result['paired_groups'][0]['suggested_name'], 'test_paired')

if __name__ == '__main__':
    unittest.main()
