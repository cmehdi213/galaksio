#!/usr/bin/env python3
"""
Paired Reads Handler for Galaxy 25.0
Automatically detects and handles paired-end sequencing reads.
"""

import os
import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from bioblend.galaxy import GalaxyInstance

logger = logging.getLogger(__name__)

class PairedReadsHandler:
    """Handler for detecting and managing paired-end sequencing reads."""
    
    # Common patterns for paired-end read files
    PAIRED_READ_PATTERNS = [
        # Standard Illumina patterns
        (r'(.+)_R1(_001)?\.(\w+)$', r'\1_R2\2.\3'),  # file_R1.fastq -> file_R2.fastq
        (r'(.+)_R2(_001)?\.(\w+)$', r'\1_R1\2.\3'),  # file_R2.fastq -> file_R1.fastq
        (r'(.+)_1(_001)?\.(\w+)$', r'\1_2\2.\3'),    # file_1.fastq -> file_2.fastq
        (r'(.+)_2(_001)?\.(\w+)$', r'\1_1\2.\3'),    # file_2.fastq -> file_1.fastq
        
        # Alternative patterns
        (r'(.+)_read1\.(\w+)$', r'\1_read2.\2'),      # file_read1.fastq -> file_read2.fastq
        (r'(.+)_read2\.(\w+)$', r'\1_read1.\2'),      # file_read2.fastq -> file_read1.fastq
        (r'(.+)\.R1\.(\w+)$', r'\1.R2.\2'),          # file.R1.fastq -> file.R2.fastq
        (r'(.+)\.R2\.(\w+)$', r'\1.R1.\2'),          # file.R2.fastq -> file.R1.fastq
        
        # PacBio/ONT patterns
        (r'(.+)_forward\.(\w+)$', r'\1_reverse.\2'),  # file_forward.fastq -> file_reverse.fastq
        (r'(.+)_reverse\.(\w+)$', r'\1_forward.\2'),  # file_reverse.fastq -> file_forward.fastq
    ]
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        '.fastq', '.fq', '.fasta', '.fa', '.fas', 
        '.fastq.gz', '.fq.gz', '.fasta.gz', '.fa.gz', '.fas.gz',
        '.bam', '.sam'
    }
    
    def __init__(self, galaxy_instance: GalaxyInstance):
        self.gi = galaxy_instance
        
    def detect_paired_reads(self, history_id: str) -> Dict[str, List[Dict]]:
        """
        Detect paired-end reads in a Galaxy history.
        """
        try:
            # Import here to avoid circular imports
            from .GalaxyAPIVerifier import get_api_verifier
            
            # Get API verifier for compatibility checks
            verifier = get_api_verifier(self.gi)
            
            # Get history contents using safe method
            datasets = verifier.get_safe_history_contents(history_id, contents=True)
            
            # Filter for sequencing files
            sequencing_files = []
            for dataset in datasets:
                if self._is_sequencing_file(dataset):
                    sequencing_files.append(dataset)
            
            # Detect pairs
            paired_groups = self._group_paired_files(sequencing_files)
            
            # Build result
            result = {
                'success': True,
                'paired_groups': paired_groups,
                'unpaired_files': self._get_unpaired_files(sequencing_files, paired_groups),
                'total_pairs': len(paired_groups),
                'total_unpaired': len(sequencing_files) - sum(len(group['files']) for group in paired_groups),
                'compatibility_report': verifier.get_compatibility_report()
            }
            
            logger.info(f"Detected {result['total_pairs']} paired groups and {result['total_unpaired']} unpaired files")
            return result
            
        except Exception as e:
            logger.error(f"Error detecting paired reads: {e}")
            return {
                'success': False,
                'error': str(e),
                'paired_groups': [],
                'unpaired_files': []
            }
    
    def _is_sequencing_file(self, dataset: Dict) -> bool:
        """Check if a dataset is a sequencing file."""
        try:
            # Check file extension
            name = dataset.get('name', '').lower()
            return any(name.endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)
        except Exception:
            return False
    
    def _group_paired_files(self, files: List[Dict]) -> List[Dict]:
        """Group files into paired sets."""
        paired_groups = []
        processed_files = set()
        
        for file1 in files:
            if file1['id'] in processed_files:
                continue
                
            # Find potential pair
            file2 = self._find_pair(file1, files)
            
            if file2:
                # Create paired group
                pair_group = {
                    'group_id': f"pair_{len(paired_groups) + 1}",
                    'files': [file1, file2],
                    'pair_type': self._determine_pair_type(file1, file2),
                    'confidence': self._calculate_pair_confidence(file1, file2),
                    'suggested_name': self._generate_suggested_name(file1, file2)
                }
                paired_groups.append(pair_group)
                processed_files.add(file1['id'])
                processed_files.add(file2['id'])
            else:
                # Mark as processed (will be added to unpaired)
                processed_files.add(file1['id'])
        
        return paired_groups
    
    def _find_pair(self, file1: Dict, files: List[Dict]) -> Optional[Dict]:
        """Find the paired file for the given file."""
        file1_name = file1.get('name', '')
        
        for pattern, replacement in self.PAIRED_READ_PATTERNS:
            # Try to find expected pair name
            expected_pair_name = re.sub(pattern, replacement, file1_name, flags=re.IGNORECASE)
            
            if expected_pair_name != file1_name:  # Pattern matched
                # Look for file with expected name
                for file2 in files:
                    if file2['id'] != file1['id']:
                        file2_name = file2.get('name', '')
                        if self._names_match(file2_name, expected_pair_name):
                            return file2
        
        return None
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two file names match (case-insensitive)."""
        return name1.lower() == name2.lower()
    
    def _determine_pair_type(self, file1: Dict, file2: Dict) -> str:
        """Determine the type of paired reads."""
        name1 = file1.get('name', '').lower()
        name2 = file2.get('name', '').lower()
        
        if '_r1' in name1 and '_r2' in name2:
            return 'illumina_r1_r2'
        elif '_r2' in name1 and '_r1' in name2:
            return 'illumina_r2_r1'
        elif '_1' in name1 and '_2' in name2:
            return 'illumina_1_2'
        elif '_2' in name1 and '_1' in name2:
            return 'illumina_2_1'
        elif 'forward' in name1 and 'reverse' in name2:
            return 'forward_reverse'
        elif 'reverse' in name1 and 'forward' in name2:
            return 'reverse_forward'
        else:
            return 'unknown'
    
    def _calculate_pair_confidence(self, file1: Dict, file2: Dict) -> float:
        """Calculate confidence score for the pair (0.0 to 1.0)."""
        confidence = 0.0
        
        name1 = file1.get('name', '').lower()
        name2 = file2.get('name', '').lower()
        
        # Check for standard patterns
        if ('_r1' in name1 and '_r2' in name2) or ('_r2' in name1 and '_r1' in name2):
            confidence += 0.4
        elif ('_1' in name1 and '_2' in name2) or ('_2' in name1 and '_1' in name2):
            confidence += 0.3
        
        # Check file sizes (should be similar for paired reads)
        size1 = file1.get('file_size', 0)
        size2 = file2.get('file_size', 0)
        if size1 > 0 and size2 > 0:
            size_ratio = min(size1, size2) / max(size1, size2)
            confidence += size_ratio * 0.3
        
        # Check data types
        data_type1 = file1.get('data_type', '')
        data_type2 = file2.get('data_type', '')
        if data_type1 == data_type2:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _generate_suggested_name(self, file1: Dict, file2: Dict) -> str:
        """Generate a suggested name for the paired group."""
        name1 = file1.get('name', '')
        name2 = file2.get('name', '')
        
        # Extract base name by removing pair indicators
        base_name1 = re.sub(r'(_R1|_R2|_1|_2|_read1|_read2|\.R1|\.R2|_forward|_reverse).*$', '', name1, flags=re.IGNORECASE)
        base_name2 = re.sub(r'(_R1|_R2|_1|_2|_read1|_read2|\.R1|\.R2|_forward|_reverse).*$', '', name2, flags=re.IGNORECASE)
        
        # Use the shorter base name
        suggested_base = min(base_name1, base_name2, key=len)
        
        return f"{suggested_base}_paired"
    
    def _get_unpaired_files(self, all_files: List[Dict], paired_groups: List[Dict]) -> List[Dict]:
        """Get files that are not part of any pair."""
        paired_file_ids = set()
        for group in paired_groups:
            for file_info in group['files']:
                paired_file_ids.add(file_info['id'])
        
        return [file_info for file_info in all_files if file_info['id'] not in paired_file_ids]
    
    def create_paired_collection(self, history_id: str, paired_group: Dict) -> Dict:
        """
        Create a paired collection in Galaxy from detected paired reads.
        """
        try:
            if len(paired_group['files']) != 2:
                return {
                    'success': False,
                    'error': 'Paired group must contain exactly 2 files'
                }
            
            file1, file2 = paired_group['files']
            collection_name = paired_group.get('suggested_name', 'paired_collection')
            
            # Import here to avoid circular imports
            from .GalaxyAPIVerifier import get_api_verifier
            
            # Get API verifier for compatibility checks
            verifier = get_api_verifier(self.gi)
            
            # Create dataset collection description
            collection_description = {
                'collection_type': 'paired',
                'name': collection_name,
                'elements': [
                    {
                        'name': 'forward',
                        'src': 'hda',
                        'id': file1['id']
                    },
                    {
                        'name': 'reverse',
                        'src': 'hda',
                        'id': file2['id']
                    }
                ]
            }
            
            # Create the collection using safe method
            collection = verifier.create_safe_collection(history_id, collection_description)
            
            return {
                'success': True,
                'collection_id': collection.get('id'),
                'collection_name': collection_name,
                'message': f'Created paired collection: {collection_name}'
            }
            
        except Exception as e:
            logger.error(f"Error creating paired collection: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def auto_pair_all_reads(self, history_id: str, create_collections: bool = True) -> Dict:
        """
        Automatically detect and pair all reads in a history.
        """
        try:
            # Detect paired reads
            detection_result = self.detect_paired_reads(history_id)
            
            if not detection_result['success']:
                return detection_result
            
            paired_groups = detection_result['paired_groups']
            created_collections = []
            
            if create_collections:
                # Create collections for high-confidence pairs
                for group in paired_groups:
                    if group['confidence'] >= 0.7:  # High confidence threshold
                        collection_result = self.create_paired_collection(history_id, group)
                        if collection_result['success']:
                            created_collections.append(collection_result)
            
            return {
                'success': True,
                'paired_groups': paired_groups,
                'created_collections': created_collections,
                'unpaired_files': detection_result['unpaired_files'],
                'summary': {
                    'total_pairs': len(paired_groups),
                    'high_confidence_pairs': len([g for g in paired_groups if g['confidence'] >= 0.7]),
                    'collections_created': len(created_collections),
                    'unpaired_count': len(detection_result['unpaired_files'])
                },
                'compatibility_report': detection_result.get('compatibility_report', {})
            }
            
        except Exception as e:
            logger.error(f"Error in auto-pairing: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_supported_patterns(self) -> Dict:
        """Get supported paired read patterns and file extensions."""
        patterns = []
        for pattern, replacement in self.PAIRED_READ_PATTERNS:
            patterns.append({
                'pattern': pattern,
                'replacement': replacement,
                'description': f"Files matching '{pattern}' will be paired with '{replacement}'"
            })
        
        return {
            'success': True,
            'patterns': patterns,
            'supported_extensions': list(self.SUPPORTED_EXTENSIONS)
        }

def get_paired_reads_handler(galaxy_instance: GalaxyInstance) -> PairedReadsHandler:
    """Get a paired reads handler instance."""
    return PairedReadsHandler(galaxy_instance)
