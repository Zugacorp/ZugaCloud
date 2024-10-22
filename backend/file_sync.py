# File: backend/file_sync.py

import os
import threading
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class FileSync:
    def __init__(self, aws_integration, update_queue):
        self.aws_integration = aws_integration
        self.update_queue = update_queue
        self.stop_event = threading.Event()
        self.s3_client = None
        self.lock = threading.Lock()
        self.aws_access_key = None
        self.aws_secret_key = None
        self.region = None
        self.sync_folder = None
        self.bucket_name = None
        self.config = {}
        self.initialize_s3_client()

    def initialize_s3_client(self):
        try:
            if self.aws_access_key and self.aws_secret_key and self.region:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.region
                )
            else:
                # Use the AWS integration's S3 client if credentials are not set
                self.s3_client = self.aws_integration.s3
            
            if self.s3_client:
                logger.info("S3 client initialized successfully in FileSync.")
            else:
                logger.error("Failed to initialize S3 client in FileSync.")
        except Exception as e:
            logger.error(f"Error initializing S3 client in FileSync: {e}")

    def update_config(self, config):
        self.config = config
        self.aws_access_key = config.get('aws_access_key')
        self.aws_secret_key = config.get('aws_secret_key')
        self.region = config.get('region')
        self.sync_folder = config.get('sync_folder')
        self.bucket_name = config.get('bucket_name')
        self.initialize_s3_client()

    def start_sync(self, sync_folder, bucket_name):
        self.sync_folder = sync_folder
        self.bucket_name = bucket_name
        self.stop_event.clear()
        
        to_upload, _ = self.aws_integration.compare_local_and_remote(sync_folder, bucket_name)
        
        if not to_upload:
            self.update_queue.put(("status", "All contents are already synced."))
            return

        self.update_queue.put(("status", f"Files to upload: {len(to_upload)}"))
        self.sync(to_upload)

    def stop_sync(self):
        self.stop_event.set()

    def sync(self, to_upload):
        if not self.s3_client:
            logger.error("S3 client not initialized in FileSync")
            self.update_queue.put(("status", "Error: S3 client not initialized"))
            return

        self.update_queue.put(("status", "Starting synchronization..."))
        try:
            total_files = len(to_upload)
            for index, file_path in enumerate(to_upload, 1):
                if self.stop_event.is_set():
                    self.update_queue.put(("status", "Synchronization stopped."))
                    return

                local_path = os.path.join(self.sync_folder, file_path)
                s3_key = file_path.replace("\\", "/")

                try:
                    self.update_queue.put(("status", f"Uploading: {s3_key}"))
                    self._upload_file_with_progress(local_path, self.bucket_name, s3_key, index, total_files)
                    logger.info(f"Uploaded {s3_key} to bucket {self.bucket_name}.")
                except ClientError as e:
                    logger.error(f"Failed to upload {s3_key}: {e}")

            self.update_queue.put(("status", "Synchronization completed."))
        except Exception as e:
            self.update_queue.put(("status", f"Error during synchronization: {e}"))
            logger.error(f"Error during synchronization: {e}")

    def _upload_file_with_progress(self, file_path, bucket, key, file_index, total_files):
        file_size = os.path.getsize(file_path)
        
        def callback(bytes_transferred):
            if self.stop_event.is_set():
                raise Exception("Upload cancelled")
            file_progress = (bytes_transferred / file_size) * 100
            overall_progress = ((file_index - 1 + (bytes_transferred / file_size)) / total_files) * 100
            self.update_queue.put(("progress", overall_progress, f"{key} ({file_progress:.1f}%)"))

        self.s3_client.upload_file(
            file_path, 
            bucket, 
            key, 
            Callback=callback
        )

    def manage_syncto_s3_bat(self, folder):
        bat_path = os.path.join(folder, 'SynctoS3.bat')
        if not os.path.exists(bat_path):
            bat_content = f"""@echo off
aws s3 sync "{folder}" s3://{self.bucket_name} --region {self.region}
"""
            with open(bat_path, 'w') as f:
                f.write(bat_content)
            if os.name == 'nt':
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(bat_path, FILE_ATTRIBUTE_HIDDEN)
            logger.info(f"Created and hid SynctoS3.bat at {bat_path}")
        else:
            logger.info(f"SynctoS3.bat already exists at {bat_path}")

    def get_local_files(self, folder):
        local_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, folder)
                local_files.append(relative_path.replace('\\', '/'))
        return local_files

    def get_s3_files(self, bucket):
        s3_files = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get('Contents', []):
                s3_files.append(obj['Key'])
        return s3_files

    def compare_files(self, local_files, s3_files):
        to_upload = set(local_files) - set(s3_files)
        to_download = set(s3_files) - set(local_files)
        return list(to_upload), list(to_download)