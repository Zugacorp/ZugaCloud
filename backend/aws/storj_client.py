import boto3
import logging
import os
from botocore.config import Config
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class StorjClient:
    def __init__(self, config=None):
        self.config = config
        self.client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Storj client with credentials"""
        try:
            # Check for Storj-specific environment variables first
            env_access_key = (os.environ.get('STORJ_ACCESS_KEY') or 
                            os.environ.get('AWS_ACCESS_KEY_ID'))
            
            env_secret_key = (os.environ.get('STORJ_SECRET_KEY') or 
                            os.environ.get('AWS_SECRET_ACCESS_KEY'))
            
            # Storj endpoint - default to EU1
            env_endpoint = (os.environ.get('STORJ_ENDPOINT') or 
                          'https://gateway.eu1.storjshare.io')
            
            logger.info(f"Environment variables present: Access Key: {bool(env_access_key)}, "
                       f"Secret Key: {bool(env_secret_key)}, Endpoint: {bool(env_endpoint)}")
            
            if self.config and self.config.get('prefer_env_vars', True):
                if not (env_access_key and env_secret_key):
                    logger.warning("Environment variables preferred but not found")
                    self.client = None
                    return
            
            # Use environment variables if available, otherwise use config values
            access_key = env_access_key or self.config.get('storj_access_key')
            secret_key = env_secret_key or self.config.get('storj_secret_key')
            endpoint = env_endpoint or self.config.get('storj_endpoint', 'https://gateway.eu1.storjshare.io')
            
            if access_key and secret_key:
                # Parse endpoint URL
                endpoint_url = urlparse(endpoint)
                region = 'us-east-1'  # Storj doesn't use regions, but boto3 requires one
                
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    endpoint_url=endpoint,
                    region_name=region,
                    config=Config(
                        s3={'addressing_style': 'path'},
                        signature_version='s3v4',
                        retries={'max_attempts': 3, 'mode': 'standard'}
                    )
                )
                logger.info("Storj client initialized successfully")
            else:
                logger.warning("No Storj credentials available")
                self.client = None

        except Exception as e:
            logger.error(f"Error initializing Storj client: {e}")
            self.client = None
            
    def generate_presigned_url(self, bucket_name, object_key, expiration=3600, content_type=None):
        """Generate a presigned URL for video streaming"""
        try:
            params = {
                'Bucket': bucket_name,
                'Key': object_key
            }
            if content_type:
                params['ResponseContentType'] = content_type
                
            url = self.client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
            
    def validate_bucket_access(self, bucket_name):
        """Validate access to the specified Storj bucket"""
        try:
            self.client.list_objects_v2(
                Bucket=bucket_name,
                MaxKeys=1
            )
            logger.info(f"Successfully validated access to bucket: {bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to validate bucket access for {bucket_name}: {e}")
            return False 