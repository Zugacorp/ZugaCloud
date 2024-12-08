# File: backend/aws_integration.py

import boto3
import logging
import os
import json
from .thumbnail_manager import ThumbnailManager

logger = logging.getLogger(__name__)

class AWSIntegration:
    def __init__(self):
        self.s3 = None
        self.config = self.load_config()
        self._bucket_name = self.config.get('bucket_name')
        self.initialize_s3_client()
        self.thumbnail_manager = ThumbnailManager(self)

    @property
    def bucket_name(self):
        """Get the current bucket name"""
        if not self._bucket_name:
            self._bucket_name = self.config.get('bucket_name')
        return self._bucket_name

    @bucket_name.setter
    def bucket_name(self, value):
        """Set the bucket name"""
        self._bucket_name = value
        self.config['bucket_name'] = value
        self.save_config()

    def load_config(self):
        """Load configuration from file"""
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def save_config(self):
        """Save current configuration to file"""
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def initialize_s3_client(self):
        try:
            # Check for environment variables first
            env_access_key = os.environ.get('AWS_ACCESS_KEY')
            env_secret_key = os.environ.get('AWS_SECRET_KEY')
            
            # Use environment variables if available, otherwise use config values
            access_key = env_access_key or self.config.get('aws_access_key')
            secret_key = env_secret_key or self.config.get('aws_secret_key')
            region = self.config.get('region', 'us-east-2')
            
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Store whether we're using environment variables
            self.using_env_vars = bool(env_access_key and env_secret_key)
            
        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
            self.s3 = None

    def is_video_file(self, file_path: str) -> bool:
        """Check if a file is a video based on its extension"""
        video_extensions = {
            '.mp4', '.mkv', '.avi', '.mov', '.wmv',
            '.m4v', '.webm', '.flv', '.mpeg', '.mpg', '.3gp'
        }
        ext = os.path.splitext(file_path)[1].lower()
        return ext in video_extensions

    def generate_presigned_url(self, bucket_name, object_key, expiration=3600):
        """Generate a presigned URL for video streaming"""
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': object_key,
                    'ResponseContentType': self.get_content_type(object_key)
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def get_content_type(self, file_path: str) -> str:
        """Get the appropriate content type based on file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.mp4': 'video/mp4',
            '.mkv': 'video/x-matroska',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.m4v': 'video/x-m4v',
            '.webm': 'video/webm',
            '.flv': 'video/x-flv',
            '.mpeg': 'video/mpeg',
            '.mpg': 'video/mpeg',
            '.3gp': 'video/3gpp'
        }
        return content_types.get(ext, 'application/octet-stream')

    def validate_bucket_access(self, bucket_name):
        """Validate access to the specified S3 bucket"""
        try:
            # Try to list objects (with max 1 result) to verify access
            self.s3.list_objects_v2(
                Bucket=bucket_name,
                MaxKeys=1
            )
            logger.info(f"Successfully validated access to bucket: {bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to validate bucket access for {bucket_name}: {e}")
            return False

    def compare_local_and_remote(self, local_folder, bucket_name):
        """Compare contents of local folder with S3 bucket for upload."""
        try:
            # Get list of local files with their sizes
            local_files = {}
            for root, _, files in os.walk(local_folder):
                for file in files:
                    if self.is_video_file(file):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, local_folder)
                        s3_key = rel_path.replace('\\', '/')
                        local_files[s3_key] = {
                            'size': os.path.getsize(full_path)
                        }

            # Get list of files in S3
            s3_files = {}
            paginator = self.s3.get_paginator('list_objects_v2')
            try:
                for page in paginator.paginate(Bucket=bucket_name):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            if self.is_video_file(obj['Key']):
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

# Create a single instance
aws_integration = AWSIntegration()