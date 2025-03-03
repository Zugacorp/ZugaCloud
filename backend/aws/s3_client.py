import boto3
import logging
import os
from botocore.config import Config

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self, config=None):
        self.config = config
        self.client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize S3 client with credentials"""
        try:
            # Check all possible environment variable combinations
            env_access_key = (os.environ.get('AWS_ACCESS_KEY') or 
                            os.environ.get('VENV_AWS_ACCESS_KEY') or 
                            os.environ.get('AWS_ACCESS_KEY_ID'))
            
            env_secret_key = (os.environ.get('AWS_SECRET_KEY') or 
                            os.environ.get('VENV_AWS_SECRET_KEY') or 
                            os.environ.get('AWS_SECRET_ACCESS_KEY'))
            
            env_region = (os.environ.get('AWS_DEFAULT_REGION') or 
                         os.environ.get('VENV_AWS_DEFAULT_REGION') or 
                         'us-east-2')
            
            logger.info(f"Environment variables present: Access Key: {bool(env_access_key)}, "
                       f"Secret Key: {bool(env_secret_key)}, Region: {bool(env_region)}")
            
            if self.config and self.config.get('prefer_env_vars', True):
                if not (env_access_key and env_secret_key):
                    logger.warning("Environment variables preferred but not found")
                    self.client = None
                    return
            
            # Use environment variables if available, otherwise use config values
            access_key = env_access_key or self.config.get('aws_access_key')
            secret_key = env_secret_key or self.config.get('aws_secret_key')
            region = env_region or self.config.get('region', 'us-east-2')
            
            if access_key and secret_key:
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region,
                    config=Config(
                        region_name=region,
                        signature_version='v4',
                        retries={'max_attempts': 3, 'mode': 'standard'}
                    )
                )
                logger.info("AWS S3 client initialized successfully")
            else:
                logger.warning("No AWS credentials available")
                self.client = None

        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
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
        """Validate access to the specified S3 bucket"""
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