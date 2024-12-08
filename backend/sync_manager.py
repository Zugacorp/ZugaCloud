from pathlib import Path
import logging
import threading
import queue
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, config_manager, aws_client):
        self.config_manager = config_manager
        self.aws_client = aws_client
        self.sync_folders: Dict[str, Path] = {}
        self.sync_queue = queue.Queue()
        self.sync_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def add_sync_folder(self, folder_path: str, bucket_name: str) -> bool:
        """Add a new folder to sync with S3."""
        try:
            path = Path(folder_path)
            if not path.exists():
                logger.error(f"Folder does not exist: {folder_path}")
                return False

            self.sync_folders[str(path)] = {
                'path': path,
                'bucket': bucket_name,
                'status': 'pending'
            }
            
            # Save to config
            self.config_manager.update_sync_folders(self.sync_folders)
            return True

        except Exception as e:
            logger.error(f"Error adding sync folder: {e}")
            return False

    def remove_sync_folder(self, folder_path: str) -> bool:
        """Remove a folder from sync list."""
        try:
            if folder_path in self.sync_folders:
                del self.sync_folders[folder_path]
                self.config_manager.update_sync_folders(self.sync_folders)
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing sync folder: {e}")
            return False

    def start_sync(self, sync_folder=None, bucket_name=None):
        """Start the synchronization process with enhanced status updates."""
        try:
            # Initial status update
            self.update_queue.put({
                "state": "scanning",
                "message": "Scanning for changes...",
                "progress": 0
            })

            # Compare local and S3 contents
            to_upload, to_delete = self._compare_contents(sync_folder, bucket_name)

            if not to_upload and not to_delete:
                self.update_queue.put({
                    "state": "no_changes",
                    "message": "No new files to sync",
                    "progress": 100
                })
                return True

            total_files = len(to_upload) + len(to_delete)
            self.update_queue.put({
                "state": "syncing",
                "message": f"Starting sync: Found {total_files} files to process",
                "progress": 0,
                "details": {
                    "filesToSync": total_files,
                    "filesScanned": total_files
                }
            })
            return True

        except Exception as e:
            logger.error(f"Error during sync process: {e}")
            self.update_queue.put({
                "state": "error",
                "message": f"Sync failed: {str(e)}",
                "progress": 0
            })
            return False

        finally:
            # Clean up resources and ensure status is updated even if there's an error
            if not self.stop_event.is_set():
                self.update_queue.put({
                    "state": "idle",
                    "message": "Sync process completed",
                    "progress": 100
                })

    def stop_sync(self):
        """Stop the sync process."""
        self.stop_event.set()
        if self.sync_thread:
            self.sync_thread.join(timeout=5.0)

    def _sync_worker(self):
        """Worker thread for handling sync operations."""
        while not self.stop_event.is_set():
            try:
                for folder_info in self.sync_folders.values():
                    if self.stop_event.is_set():
                        break

                    folder_path = folder_info['path']
                    bucket_name = folder_info['bucket']
                    
                    # Compare local and S3 contents
                    to_upload = self._compare_contents(folder_path, bucket_name)
                    
                    # Upload new/modified files
                    for file_path in to_upload:
                        if self.stop_event.is_set():
                            break
                        self._upload_file(file_path, bucket_name)

                # Wait before next sync cycle
                self.stop_event.wait(timeout=300)  # 5 minutes between syncs

            except Exception as e:
                logger.error(f"Error in sync worker: {e}")
                self.stop_event.wait(timeout=60)  # Wait 1 minute on error 