# File: backend/aws_integration.py

import boto3
from botocore.exceptions import ClientError
import logging
import os

logger = logging.getLogger(__name__)

class AWSIntegration:
    def __init__(self, access_key=None, secret_key=None, region='us-east-2'):
        self.region = region
        self.s3 = None
        self.initialize_s3_client(access_key, secret_key)

    def initialize_s3_client(self, access_key=None, secret_key=None):
        try:
            if access_key and secret_key:
                # Remove any whitespace or newline characters
                access_key = access_key.strip()
                secret_key = secret_key.strip()
                self.s3 = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=self.region
                )
            else:
                self.s3 = boto3.client('s3', region_name=self.region)
            logger.info("S3 client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3 = None

    def is_initialized(self):
        return self.s3 is not None

    def update_credentials(self, access_key, secret_key, region):
        self.region = region
        self.initialize_s3_client(access_key, secret_key)

    def list_objects_paginated(self, bucket_name, prefix='', continuation_token=None):
        try:
            params = {
                'Bucket': bucket_name,
                'Prefix': prefix,
                'Delimiter': '/'
            }
            if continuation_token:
                params['ContinuationToken'] = continuation_token

            response = self.s3.list_objects_v2(**params)
            
            contents = []
            if 'CommonPrefixes' in response:
                for common_prefix in response['CommonPrefixes']:
                    contents.append({
                        'Key': common_prefix['Prefix'],
                        'Type': 'prefix'
                    })
            if 'Contents' in response:
                for item in response['Contents']:
                    if not item['Key'].endswith('/'):
                        contents.append({
                            'Key': item['Key'],
                            'Type': 'object',
                            'Size': item['Size'],
                            'LastModified': item['LastModified']
                        })
            
            next_token = response.get('NextContinuationToken')
            return contents, next_token
        except ClientError as e:
            logger.error(f"Error listing objects in bucket '{bucket_name}': {e}")
            return [], None

    def generate_presigned_url(self, bucket_name, object_key, expiration=3600):
        try:
            url = self.s3.generate_presigned_url('get_object',
                                                 Params={'Bucket': bucket_name, 'Key': object_key},
                                                 ExpiresIn=expiration)
            logger.info(f"Generated presigned URL for {object_key}")
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {object_key}: {e}")
            return None

    def get_object(self, bucket_name, object_key):
        try:
            response = self.s3.get_object(Bucket=bucket_name, Key=object_key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error getting object {object_key} from bucket {bucket_name}: {e}")
            return None

    def get_object_range(self, bucket_name, key, start, end):
        try:
            response = self.s3.get_object(Bucket=bucket_name, Key=key, Range=f'bytes={start}-{end}')
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error getting object range for {key}: {e}")
            return None

    def compare_local_and_remote(self, local_folder, bucket_name):
        local_files = set()
        for root, _, files in os.walk(local_folder):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, local_folder)
                local_files.add(relative_path.replace('\\', '/'))

        remote_files = set()
        paginator = self.s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name):
            for obj in page.get('Contents', []):
                remote_files.add(obj['Key'])

        to_upload = local_files - remote_files
        to_download = remote_files - local_files
        
        return to_upload, to_download
    
    def get_existing_buckets(self):
        try:
            if not self.s3:
                logger.error("S3 client not initialized")
                return []
            response = self.s3.list_buckets()
            buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
            logger.info(f"Retrieved buckets: {buckets}")
            return buckets
        except ClientError as e:
            logger.error(f"Error listing buckets: {e}")
            return []

    def create_s3_bucket(self, bucket_name):
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=bucket_name)
            else:
                location = {'LocationConstraint': self.region}
                self.s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
            logger.info(f"Bucket '{bucket_name}' created successfully.")
            return True
        except ClientError as e:
            logger.error(f"Failed to create bucket '{bucket_name}': {e}")
            return False

    def upload_file(self, file_path, bucket_name, object_name=None):
        if object_name is None:
            object_name = file_path

        try:
            self.s3.upload_file(file_path, bucket_name, object_name)
            logger.info(f"File {file_path} uploaded successfully to {bucket_name}/{object_name}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file {file_path} to {bucket_name}/{object_name}: {e}")
            return False

    def download_file(self, bucket_name, object_name, file_path):
        try:
            self.s3.download_file(bucket_name, object_name, file_path)
            logger.info(f"File {object_name} downloaded successfully from {bucket_name} to {file_path}")
            return True
        except ClientError as e:
            logger.error(f"Error downloading file {object_name} from {bucket_name} to {file_path}: {e}")
            return False