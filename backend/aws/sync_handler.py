import os
import logging
from .video_handler import VideoHandler

logger = logging.getLogger(__name__)

class SyncHandler:
    def __init__(self, s3_client):
        self.s3_client = s3_client
        self.video_handler = VideoHandler(s3_client)
        
    def compare_local_and_remote(self, local_folder, bucket_name):
        """Compare contents of local folder with S3 bucket for upload."""
        try:
            # Get list of local files with their sizes
            local_files = {}
            for root, _, files in os.walk(local_folder):
                for file in files:
                    if self.video_handler.is_video_file(file):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, local_folder)
                        s3_key = rel_path.replace('\\', '/')
                        local_files[s3_key] = {
                            'size': os.path.getsize(full_path)
                        }

            # Get list of files in S3
            s3_files = {}
            paginator = self.s3_client.client.get_paginator('list_objects_v2')
            try:
                for page in paginator.paginate(Bucket=bucket_name):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            if self.video_handler.is_video_file(obj['Key']):
                                s3_files[obj['Key']] = {
                                    'size': obj['Size']
                                }
            except Exception as e:
                logger.error(f"Error listing S3 objects: {e}")
                raise

            # Debug logging
            logger.info(f"Local files found: {list(local_files.keys())}")
            logger.info(f"S3 files found: {list(s3_files.keys())}")

            # Compare files and determine which need to be uploaded
            to_upload = []
            
            if not local_files:
                logger.info("No video files found in local folder")
                return [], []
            
            # Compare files
            for key, local_info in local_files.items():
                upload_needed = False
                if key not in s3_files:
                    logger.info(f"New file {key} will be uploaded")
                    upload_needed = True
                else:
                    s3_info = s3_files[key]
                    if local_info['size'] != s3_info['size']:
                        logger.info(f"Size mismatch for {key}: local={local_info['size']}, s3={s3_info['size']}")
                        upload_needed = True
                
                if upload_needed:
                    to_upload.append(key)

            logger.info(f"Found {len(to_upload)} files to upload out of {len(local_files)} local files")
            return to_upload, []

        except Exception as e:
            logger.error(f"Error comparing local and remote contents: {e}")
            raise
            
    def calculate_folder_stats(self, bucket: str, prefix: str) -> tuple[int, int]:
        """Calculate total size and file count for a folder prefix."""
        total_size = 0
        file_count = 0
        
        try:
            paginator = self.s3_client.client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if not obj['Key'].endswith('/'):  # Skip folder markers
                            total_size += obj['Size']
                            file_count += 1
            
            return total_size, file_count
        except Exception as e:
            logger.error(f"Error calculating folder stats for {prefix}: {e}")
            return 0, 0 