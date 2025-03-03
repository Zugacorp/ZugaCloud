from flask import jsonify, request, send_from_directory
import logging
import os
import json
import boto3
import queue
from urllib.parse import unquote
from .exceptions import (
    ConfigurationError,
    CredentialsError,
    ResourceNotFoundError,
    FileOperationError,
    BucketOperationError,
    SyncError,
    ValidationError
)
from ..aws.s3_client import S3Client  # Import for temporary client creation
from ..aws.storj_client import StorjClient  # Import for temporary client creation

logger = logging.getLogger(__name__)

class BaseHandler:
    """Base class for all request handlers"""
    def __init__(self, aws_integration):
        self.aws_integration = aws_integration

class ConfigHandler(BaseHandler):
    """Handler for configuration-related requests"""
    
    def get_config(self):
        """Get current configuration"""
        try:
            return jsonify(self.aws_integration.config)
        except Exception as e:
            logger.error(f"Error getting config: {str(e)}")
            raise ConfigurationError(str(e))

    def update_config(self, new_config):
        """Update configuration"""
        try:
            current_config = self.aws_integration.config.copy()
            current_config.update(new_config)
            
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
            with open(config_path, 'w') as f:
                json.dump(current_config, f, indent=4)
                
            self.aws_integration.config = current_config
            self.aws_integration.initialize_s3_client()
            
            return jsonify(current_config)
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            raise ConfigurationError(str(e))

class BucketHandler(BaseHandler):
    """Handler for S3 bucket operations"""
    
    def list_buckets(self):
        """List all available S3 buckets"""
        try:
            if not self.aws_integration.s3:
                raise BucketOperationError('AWS not initialized')
            
            # Check if a specific provider is requested
            provider = request.args.get('provider')
            
            # If provider is specified, temporarily switch to it
            current_provider = self.aws_integration.storage_provider
            original_client = self.aws_integration.s3_client
            temp_client = None
            
            try:
                # If a specific provider is requested and it's different from current
                if provider and provider != current_provider:
                    logger.debug(f"Temporarily switching to {provider} provider for bucket listing")
                    
                    if provider == 'storj':
                        temp_client = StorjClient(self.aws_integration.config)
                    elif provider == 'aws':
                        temp_client = S3Client(self.aws_integration.config)
                    
                    # Use the temporary client if it was successfully created
                    s3_client = temp_client.client if temp_client and temp_client.client else self.aws_integration.s3
                else:
                    # Use the current client
                    s3_client = self.aws_integration.s3
                
                # List buckets using the selected client
                response = s3_client.list_buckets()
                buckets = []
                
                # Format bucket list with additional metadata
                for bucket in response.get('Buckets', []):
                    bucket_info = {
                        'name': bucket['Name'],
                        'creation_date': bucket['CreationDate'].isoformat() if 'CreationDate' in bucket else None,
                    }
                    
                    # Mark zugacloud bucket as recommended for Storj
                    if (provider == 'storj' or current_provider == 'storj') and bucket['Name'] == 'zugacloud':
                        bucket_info['recommended'] = True
                        bucket_info['description'] = 'Recommended Storj bucket'
                    
                    buckets.append(bucket_info)
                
                return jsonify(buckets)
                
            finally:
                # Clean up temporary client if one was created
                if temp_client:
                    del temp_client
            
        except Exception as e:
            logger.error(f"Error listing buckets: {e}")
            raise BucketOperationError(str(e))

class FileHandler(BaseHandler):
    """Handler for file operations"""
    
    def list_files(self, path='/', bucket=None):
        """List files in S3 bucket"""
        try:
            if not self.aws_integration.s3:
                return jsonify({'files': [], 'error': 'AWS not initialized'})

            bucket = bucket or self.aws_integration.bucket_name
            return self.aws_integration.list_files(path, bucket)
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise FileOperationError(str(e))

    def delete_local_file(self, file_path):
        """Delete a file from local storage"""
        try:
            sync_folder = self.aws_integration.config.get('sync_folder')
            if not sync_folder:
                raise FileOperationError('No sync folder configured')

            absolute_path = os.path.normpath(os.path.join(sync_folder, file_path))
            if not absolute_path.startswith(os.path.normpath(sync_folder)):
                raise FileOperationError('Invalid path')

            if os.path.exists(absolute_path):
                os.remove(absolute_path)
                return jsonify({'success': True})
            else:
                raise ResourceNotFoundError('File not found')
        except Exception as e:
            logger.error(f"Error deleting local file: {e}")
            raise FileOperationError(str(e))

    def delete_s3_file(self, file_path):
        """Delete a file from S3"""
        try:
            bucket_name = self.aws_integration.bucket_name
            if not bucket_name:
                raise FileOperationError('No bucket configured')

            try:
                self.aws_integration.s3.delete_object(
                    Bucket=bucket_name,
                    Key=file_path
                )
                return jsonify({'success': True})
            except self.aws_integration.s3.exceptions.NoSuchKey:
                raise ResourceNotFoundError('File not found in S3')
            except self.aws_integration.s3.exceptions.ClientError as e:
                logger.error(f"AWS error deleting object: {e}")
                raise FileOperationError(str(e))
        except Exception as e:
            logger.error(f"Error deleting S3 file: {e}")
            raise FileOperationError(str(e))

    def check_local_file(self, file_path):
        """Check if a file exists locally"""
        try:
            sync_folder = self.aws_integration.config.get('sync_folder')
            if not sync_folder:
                return jsonify({'exists': False})

            local_path = os.path.join(sync_folder, file_path.lstrip('/'))
            exists = os.path.isfile(local_path)
            
            return jsonify({'exists': exists})
        except Exception as e:
            logger.error(f"Error checking local file: {e}")
            raise FileOperationError(str(e))

    def get_file_info(self, file_key):
        """Get detailed file information including sync status"""
        try:
            if not file_key:
                raise ValidationError('No file key provided')
                
            try:
                metadata = self.aws_integration.s3.head_object(
                    Bucket=self.aws_integration.bucket_name,
                    Key=file_key
                )
                
                file_info = {
                    'key': file_key,
                    'size': metadata['ContentLength'],
                    'lastModified': metadata['LastModified'].isoformat(),
                    'metadata': metadata.get('Metadata', {}),
                    'originalName': metadata.get('Metadata', {}).get('OriginalName'),
                    'uploadDate': metadata.get('Metadata', {}).get('UploadDate'),
                    'videoHash': metadata.get('Metadata', {}).get('VideoHash')
                }
                
                return jsonify(file_info)
                
            except self.aws_integration.s3.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise ResourceNotFoundError('File not found')
                raise FileOperationError(str(e))
                    
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            raise FileOperationError(str(e))

    def stream_file(self, file_key):
        """Generate streaming URL for a file"""
        try:
            bucket_name = self.aws_integration.config.get('bucket_name')
            if not bucket_name:
                raise FileOperationError('No bucket configured')

            url = self.aws_integration.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': file_key
                },
                ExpiresIn=3600
            )
            
            return jsonify({'url': url})
        except Exception as e:
            logger.error(f"Error generating streaming URL: {str(e)}")
            raise FileOperationError(str(e))

class SyncHandler(BaseHandler):
    """Handler for synchronization operations"""
    
    def start_sync(self, sync_folder, bucket_name):
        """Start synchronization process"""
        try:
            if not sync_folder or not bucket_name:
                raise SyncError('Missing required sync_folder or bucket_name')

            from ..sync.file_sync import FileSync
            file_sync = FileSync(self.aws_integration)

            file_sync.update_config({
                'aws_access_key': self.aws_integration.config.get('aws_access_key'),
                'aws_secret_key': self.aws_integration.config.get('aws_secret_key'),
                'region': self.aws_integration.config.get('region'),
                'sync_folder': sync_folder,
                'bucket_name': bucket_name,
                'no_delete': True
            })

            # Start sync in background thread
            import threading
            def run_sync():
                try:
                    to_upload, _ = self.aws_integration.compare_local_and_remote(sync_folder, bucket_name)
                    file_sync.sync(to_upload)
                except Exception as e:
                    logger.error(f"Error in sync thread: {e}")

            sync_thread = threading.Thread(target=run_sync)
            sync_thread.start()

            return jsonify({
                'status': 'started',
                'message': 'Upload process started successfully'
            })
        except Exception as e:
            logger.error(f"Error starting sync: {str(e)}")
            raise SyncError(str(e))

class AuthHandler(BaseHandler):
    """Handler for authentication-related requests"""
    
    def validate_credentials(self, credentials):
        """Validate AWS credentials"""
        try:
            test_client = boto3.client(
                's3',
                aws_access_key_id=credentials.get('aws_access_key'),
                aws_secret_access_key=credentials.get('aws_secret_key'),
                region_name=credentials.get('region', 'us-east-2')
            )
            
            test_client.list_buckets()
            
            # Update config with validated credentials
            self.aws_integration.config.update({
                'aws_access_key': credentials.get('aws_access_key'),
                'aws_secret_key': credentials.get('aws_secret_key'),
                'region': credentials.get('region', 'us-east-2')
            })
            
            # Save updated config
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
            with open(config_path, 'w') as f:
                json.dump(self.aws_integration.config, f, indent=4)
            
            # Reinitialize AWS client
            self.aws_integration.initialize_s3_client()
            
            return jsonify({'valid': True, 'message': 'Credentials validated successfully'})
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            raise CredentialsError(str(e))

    def check_credential_source(self):
        """Check if using environment variables for credentials"""
        try:
            using_env_vars = bool(
                os.environ.get('AWS_ACCESS_KEY') and 
                os.environ.get('AWS_SECRET_KEY')
            )
            return jsonify({'usingEnvVars': using_env_vars})
        except Exception as e:
            logger.error(f"Error checking credential source: {e}")
            raise CredentialsError(str(e))

    def set_credential_source(self, use_env_vars):
        """Set whether to use environment variables for credentials"""
        try:
            # Update config to reflect preference
            self.aws_integration.config['prefer_env_vars'] = use_env_vars
            
            # Save to config file
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
            with open(config_path, 'w') as f:
                json.dump(self.aws_integration.config, f, indent=4)
            
            # Reinitialize AWS client
            self.aws_integration.initialize_s3_client()
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Error setting credential source: {e}")
            raise CredentialsError(str(e))

class HealthHandler(BaseHandler):
    """Handler for health check requests"""
    
    def check_health(self):
        """Check system health"""
        try:
            components = {
                'api': 'healthy',
                'aws': 'healthy' if self.aws_integration.s3 else 'unhealthy',
                'sync': 'healthy'
            }
            
            return jsonify({
                'status': 'ok',
                'components': components
            })
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise ConnectionError(f"Health check failed: {str(e)}") 