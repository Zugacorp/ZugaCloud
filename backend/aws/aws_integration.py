# File: backend/aws/aws_integration.py

import logging
import os
import json
from pathlib import Path
from .s3_client import S3Client
from .storj_client import StorjClient
from .video_handler import VideoHandler
from .sync_handler import SyncHandler
from ..managers.thumbnail_manager import ThumbnailManager

logger = logging.getLogger(__name__)

class AWSIntegration:
    def __init__(self, config=None):
        """Initialize storage integration with optional config"""
        self.config = config if config is not None else self.load_config()
        self._bucket_name = self.config.get('bucket_name')
        
        # Auto-detect and prioritize Storj credentials if available
        self._check_and_prioritize_storj()
        
        # Determine storage provider
        self.storage_provider = self.config.get('storage_provider', 'aws').lower()
        
        # Initialize appropriate client
        if self.storage_provider == 'storj':
            self.s3_client = StorjClient(self.config)
        else:
            self.s3_client = S3Client(self.config)
            
        self.s3 = self.s3_client.client  # For backward compatibility
        
        # Initialize handlers
        self.video = VideoHandler(self.s3_client)
        self.sync = SyncHandler(self.s3_client)
        self.thumbnail_manager = ThumbnailManager(self)

    def _check_and_prioritize_storj(self):
        """Check for Storj credentials and automatically set as provider if valid"""
        # Check for Storj credentials in config or environment
        has_storj_credentials = self._has_valid_storj_credentials()
        current_provider = self.config.get('storage_provider', 'aws').lower()
        
        # If Storj credentials exist and provider isn't already set to storj
        if has_storj_credentials and current_provider != 'storj':
            logger.info("Valid Storj credentials detected. Setting storage provider to 'storj'")
            self.config['storage_provider'] = 'storj'
            self.save_config()
    
    def _has_valid_storj_credentials(self):
        """Check if valid Storj credentials are available"""
        # Check environment variables first
        env_access_key = os.environ.get('STORJ_ACCESS_KEY') or os.environ.get('AWS_ACCESS_KEY_ID')
        env_secret_key = os.environ.get('STORJ_SECRET_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        # Then check config
        config_access_key = self.config.get('storj_access_key')
        config_secret_key = self.config.get('storj_secret_key')
        
        # Return True if either source has both keys
        return (env_access_key and env_secret_key) or (config_access_key and config_secret_key)

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
        """Re-initialize storage client"""
        # Check for Storj credentials before reinitializing
        self._check_and_prioritize_storj()
        
        if self.storage_provider == 'storj':
            self.s3_client = StorjClient(self.config)
        else:
            self.s3_client = S3Client(self.config)
        self.s3 = self.s3_client.client

    def set_storage_provider(self, provider: str):
        """Change storage provider (aws/storj)"""
        provider = provider.lower()
        if provider not in ['aws', 'storj']:
            raise ValueError("Invalid storage provider. Must be 'aws' or 'storj'")
            
        self.storage_provider = provider
        self.config['storage_provider'] = provider
        self.save_config()
        self.initialize_s3_client()

    async def initialize(self):
        """Async initialization of storage integration"""
        try:
            if not self.s3:
                self.initialize_s3_client()
            return True
        except Exception as e:
            logger.error(f"Error in async initialization: {e}")
            return False

    # Delegate methods to appropriate handlers
    def is_video_file(self, file_path):
        return self.video.is_video_file(file_path)

    def generate_presigned_url(self, bucket_name, object_key, expiration=3600):
        return self.video.generate_streaming_url(bucket_name, object_key, expiration)

    def compare_local_and_remote(self, local_folder, bucket_name):
        return self.sync.compare_local_and_remote(local_folder, bucket_name)

    def calculate_folder_stats(self, bucket, prefix):
        return self.sync.calculate_folder_stats(bucket, prefix)

# Create a single instance
aws_integration = AWSIntegration()