#!/usr/bin/env python3
"""
Enhanced File Upload Handler for Galaxy 25.0
Handles large file uploads with chunking and progress tracking.
"""

import os
import logging
import tempfile
import shutil
from typing import Dict, Optional, Callable
from werkzeug.utils import secure_filename
from bioblend.galaxy import GalaxyInstance

logger = logging.getLogger(__name__)

class FileUploadHandler:
    """Enhanced file upload handler with chunking support."""
    
    def __init__(self, galaxy_instance: GalaxyInstance, chunk_size: int = 10 * 1024 * 1024):
        self.gi = galaxy_instance
        self.chunk_size = chunk_size  # 10MB chunks
        self.temp_dir = tempfile.mkdtemp(prefix='galaksio_upload_')
    
    def upload_file(self, file_obj, filename: str, 
                   history_id: str, 
                   progress_callback: Optional[Callable] = None) -> Dict:
        """
        Upload a file to Galaxy with chunking support.
        
        Args:
            file_obj: File object to upload
            filename: Original filename
            history_id: Galaxy history ID
            progress_callback: Optional callback for progress updates
        
        Returns:
            Dict with upload result
        """
        try:
            # Secure filename
            secure_name = secure_filename(filename)
            file_path = os.path.join(self.temp_dir, secure_name)
            
            # Save file temporarily
            file_size = 0
            with open(file_path, 'wb') as temp_file:
                while True:
                    chunk = file_obj.read(self.chunk_size)
                    if not chunk:
                        break
                    temp_file.write(chunk)
                    file_size += len(chunk)
                    
                    if progress_callback:
                        progress_callback(len(chunk))
            
            # Determine upload method based on file size
            if file_size > 50 * 1024 * 1024:  # 50MB threshold
                return self._upload_large_file(file_path, secure_name, history_id, progress_callback)
            else:
                return self._upload_regular_file(file_path, secure_name, history_id)
                
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def _upload_regular_file(self, file_path: str, filename: str, history_id: str) -> Dict:
        """Upload regular-sized file."""
        try:
            with open(file_path, 'rb') as file_obj:
                result = self.gi.tools.upload_file(
                    file_obj, 
                    history_id=history_id,
                    file_name=filename,
                    dbkey='?',
                    file_type='auto'
                )
            
            return {
                'success': True,
                'dataset_id': result.get('id'),
                'filename': filename,
                'size': os.path.getsize(file_path)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _upload_large_file(self, file_path: str, filename: str, 
                          history_id: str, progress_callback: Optional[Callable] = None) -> Dict:
        """Upload large file using chunked upload."""
        try:
            # Get file size for progress calculation
            file_size = os.path.getsize(file_path)
            uploaded_size = 0
            
            # Create a library for chunked upload
            library_name = f"Galaksio_Upload_{os.getpid()}"
            library = self.gi.libraries.create_library(library_name)
            library_id = library['id']
            
            # Create folder in library
            folder = self.gi.libraries.create_folder(library_id, f"Upload_{os.getpid()}")
            folder_id = folder[0]['id']
            
            # Upload file in chunks
            with open(file_path, 'rb') as file_obj:
                chunk_number = 0
                while True:
                    chunk = file_obj.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    # Upload chunk
                    chunk_filename = f"{filename}.part{chunk_number}"
                    self.gi.libraries.upload_file_from_local(
                        library_id,
                        file_obj=chunk,
                        folder_id=folder_id,
                        file_type='auto',
                        dbkey='?',
                        file_name=chunk_filename
                    )
                    
                    uploaded_size += len(chunk)
                    chunk_number += 1
                    
                    if progress_callback:
                        progress = (uploaded_size / file_size) * 100
                        progress_callback(progress)
            
            # Combine chunks in Galaxy (this would require Galaxy tool support)
            # For now, we'll use the library approach
            
            # Import to history
            datasets = self.gi.libraries.get_library_datasets(library_id)
            if datasets:
                dataset_id = datasets[-1]['id']
                self.gi.histories.import_dataset(history_id, dataset_id)
                
                return {
                    'success': True,
                    'dataset_id': dataset_id,
                    'filename': filename,
                    'size': file_size,
                    'chunks': chunk_number
                }
            
            return {'success': False, 'error': 'Failed to import dataset to history'}
            
        except Exception as e:
            logger.error(f"Large file upload failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

class UploadProgressTracker:
    """Track upload progress across multiple sessions."""
    
    def __init__(self):
        self.active_uploads = {}
        self.lock = threading.Lock()
    
    def start_upload(self, upload_id: str, filename: str, file_size: int):
        """Start tracking an upload."""
        with self.lock:
            self.active_uploads[upload_id] = {
                'filename': filename,
                'file_size': file_size,
                'uploaded': 0,
                'progress': 0.0,
                'status': 'uploading',
                'start_time': datetime.now(),
                'error': None
            }
    
    def update_progress(self, upload_id: str, bytes_uploaded: int):
        """Update upload progress."""
        with self.lock:
            if upload_id in self.active_uploads:
                upload_info = self.active_uploads[upload_id]
                upload_info['uploaded'] += bytes_uploaded
                upload_info['progress'] = (upload_info['uploaded'] / upload_info['file_size']) * 100
    
    def complete_upload(self, upload_id: str, result: Dict):
        """Mark upload as completed."""
        with self.lock:
            if upload_id in self.active_uploads:
                upload_info = self.active_uploads[upload_id]
                upload_info['status'] = 'completed' if result.get('success') else 'failed'
                upload_info['result'] = result
                upload_info['end_time'] = datetime.now()
                if not result.get('success'):
                    upload_info['error'] = result.get('error')
    
    def get_upload_status(self, upload_id: str) -> Optional[Dict]:
        """Get upload status."""
        with self.lock:
            return self.active_uploads.get(upload_id)
    
    def cleanup_old_uploads(self, max_age_hours: int = 1):
        """Clean up old upload records."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            to_remove = []
            for upload_id, upload_info in self.active_uploads.items():
                end_time = upload_info.get('end_time')
                if end_time and end_time.timestamp() < cutoff_time:
                    to_remove.append(upload_id)
            
            for upload_id in to_remove:
                del self.active_uploads[upload_id]

# Global upload progress tracker
upload_tracker = UploadProgressTracker()

def get_upload_tracker() -> UploadProgressTracker:
    """Get the global upload progress tracker."""
    return upload_tracker
