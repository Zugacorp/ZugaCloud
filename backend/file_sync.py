# File: backend/file_sync.py
import ctypes
import sys
import subprocess
import tempfile
import shutil
import win32security
import win32api
import win32con
import os
import threading
import boto3
from botocore.exceptions import ClientError
import logging
import hashlib
from .sync_queue import sync_queue  # Import the shared queue

logger = logging.getLogger(__name__)

class FileSync:
    VERSION = "1.1.0"  # Version tracking for bat file

    def __init__(self, aws_integration, update_queue=None):
        self.aws_integration = aws_integration
        self.update_queue = update_queue or sync_queue  # Use provided queue or default to global queue
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
        """Initialize the S3 client with current credentials."""
        try:
            if self.aws_access_key and self.aws_secret_key and self.region:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.region
                )
            else:
                self.s3_client = self.aws_integration.s3
            
            if self.s3_client:
                logger.info("S3 client initialized successfully in FileSync.")
            else:
                logger.error("Failed to initialize S3 client in FileSync.")
        except Exception as e:
            logger.error(f"Error initializing S3 client in FileSync: {e}")

    def update_config(self, config):
        """Update configuration and reinitialize if necessary."""
        self.config = config
        self.aws_access_key = config.get('aws_access_key')
        self.aws_secret_key = config.get('aws_secret_key')
        self.region = config.get('region')
        self.sync_folder = config.get('sync_folder')
        self.bucket_name = config.get('bucket_name')
        self.initialize_s3_client()
        
        # Check and update batch file if needed
        if self.sync_folder:
            self.check_and_update_batch_file(self.sync_folder)

    def get_batch_file_version(self, content):
        """Extract version from batch file content."""
        try:
            for line in content.split('\n'):
                if line.startswith('rem Version:'):
                    return line.split(':')[1].strip()
        except:
            return None
        return None

    def generate_batch_content(self):
        """Generate the content for the batch file."""
        return f"""@echo off
rem Version: {self.VERSION}
setlocal EnableDelayedExpansion

set AWS_ACCESS_KEY_ID={self.aws_access_key}
set AWS_SECRET_ACCESS_KEY={self.aws_secret_key}
set AWS_DEFAULT_REGION={self.region}

:check_aws
where aws >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo AWS CLI is not installed or not in PATH
    echo Please install AWS CLI from: https://aws.amazon.com/cli/
    pause
    exit /b 1
)

:upload_files
echo.
echo Starting upload at %date% %time%
echo Uploading from "{self.sync_folder}" to "s3://{self.bucket_name}"

aws s3 sync "{self.sync_folder}" "s3://{self.bucket_name}" --size-only --progress

if !ERRORLEVEL! neq 0 (
    echo Upload failed with error code !ERRORLEVEL!
    exit /b !ERRORLEVEL!
)

echo Upload completed successfully at %date% %time%
exit /b 0
"""

    def check_and_update_batch_file(self, folder):
        """Check if batch file exists and has correct version, update if needed."""
        bat_path = os.path.join(folder, 'SynctoS3.bat')
        current_content = None
        current_version = None

        # Check existing file
        if os.path.exists(bat_path):
            try:
                with open(bat_path, 'r') as f:
                    current_content = f.read()
                current_version = self.get_batch_file_version(current_content)
            except Exception as e:
                logger.error(f"Error reading existing batch file: {e}")

        # Update if version mismatch or file doesn't exist
        if current_version != self.VERSION:
            self.manage_syncto_s3_bat(folder)

    def manage_syncto_s3_bat(self, folder):
        """Create or update the SynctoS3.bat file."""
        try:
            if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name, self.region]):
                logger.error("Missing required AWS credentials or configuration")
                return False

            bat_path = os.path.join(folder, 'SynctoS3.bat')
            bat_content = self.generate_batch_content()

            # Write the batch file
            with open(bat_path, 'w') as f:
                f.write(bat_content)

            # Make the file hidden on Windows
            if os.name == 'nt':
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(bat_path, FILE_ATTRIBUTE_HIDDEN)
                
            logger.info(f"Successfully created/updated SynctoS3.bat at {bat_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating SynctoS3.bat: {e}")
            return False
        
    def check_admin_privileges(self):
        """Check if the program has admin privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def elevate_privileges(self):
        """Restart the program with admin privileges."""
        if not self.check_admin_privileges():
            script = sys.argv[0]
            params = ' '.join(sys.argv[1:])
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
            if int(ret) <= 32:
                raise Exception("Failed to elevate privileges")
            sys.exit()

    def take_ownership_and_grant_permissions(self, path):
        """Take ownership of file/folder and grant full permissions."""
        try:
            # Get current process owner
            proc_owner = win32api.GetUserNameEx(win32con.NameSamCompatible)
            
            # Get security information
            sd = win32security.GetFileSecurity(
                path, win32security.OWNER_SECURITY_INFORMATION | 
                win32security.DACL_SECURITY_INFORMATION
            )
            
            # Get the SID for the current user
            username, domain, type = win32security.LookupAccountName(None, proc_owner)
            
            # Set the owner
            sd.SetSecurityDescriptorOwner(username, True)
            
            # Get the DACL
            dacl = sd.GetSecurityDescriptorDacl()
            if dacl is None:
                dacl = win32security.ACL()
            
            # Add full control permission for the current user
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION, 
                win32con.GENERIC_ALL, 
                username
            )
            
            # Set the modified DACL
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                path, 
                win32security.OWNER_SECURITY_INFORMATION | 
                win32security.DACL_SECURITY_INFORMATION, 
                sd
            )
            
            return True
        except Exception as e:
            logger.error(f"Error setting file permissions: {e}")
            return False

    def manage_syncto_s3_bat(self, folder):
        """Create or update the SynctoS3.bat file with proper permissions."""
        try:
            if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name, self.region]):
                logger.error("Missing required AWS credentials or configuration")
                return False

            bat_path = os.path.join(folder, 'SynctoS3.bat')
            temp_bat_path = None

            # Create content in a temporary file first
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.bat') as temp_file:
                temp_bat_path = temp_file.name
                temp_file.write(self.generate_batch_content())

            try:
                # If the target file exists, try to take ownership and set permissions
                if os.path.exists(bat_path):
                    try:
                        # Try to delete existing file
                        os.chmod(bat_path, 0o777)  # Give full permissions
                        os.remove(bat_path)
                    except PermissionError:
                        # If permission denied, try to take ownership
                        if not self.take_ownership_and_grant_permissions(bat_path):
                            # If taking ownership fails, try to run with elevated privileges
                            if not self.check_admin_privileges():
                                self.elevate_privileges()
                            os.remove(bat_path)

                # Copy the temporary file to the final location
                shutil.copy2(temp_bat_path, bat_path)

                # Set proper permissions on the new file
                if os.name == 'nt':
                    try:
                        # Make the file hidden
                        ctypes.windll.kernel32.SetFileAttributesW(bat_path, 0x02)
                        # Set file permissions
                        self.take_ownership_and_grant_permissions(bat_path)
                    except Exception as e:
                        logger.warning(f"Could not set file attributes: {e}")

                logger.info(f"Successfully created/updated SynctoS3.bat at {bat_path}")
                return True

            finally:
                # Clean up temporary file
                if temp_bat_path and os.path.exists(temp_bat_path):
                    try:
                        os.remove(temp_bat_path)
                    except:
                        pass

        except Exception as e:
            logger.error(f"Error creating SynctoS3.bat: {e}")
            return False

    def start_sync(self, sync_folder=None, bucket_name=None):
        """Start the synchronization process."""
        try:
            if sync_folder:
                self.sync_folder = sync_folder
            if bucket_name:
                self.bucket_name = bucket_name

            # Validate parameters
            if not self.sync_folder or not self.bucket_name:
                raise ValueError("Missing sync folder or bucket name")

            # Start AWS CLI sync process
            cmd = f'aws s3 sync "{self.sync_folder}" "s3://{self.bucket_name}" --size-only --progress'
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            # Track progress
            total_bytes = 0
            transferred_bytes = 0
            current_file = None

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    output = output.strip()
                    logger.debug(f"Sync output: {output}")

                    # Parse different types of AWS CLI output
                    if "Completed" in output:
                        try:
                            # Parse progress like "Completed 1.2 MB/4.5 MB (26.7%)"
                            parts = output.split()
                            progress_str = parts[-1].strip('()%')
                            progress = float(progress_str)
                            
                            self.update_queue.put(("status", {
                                "type": "progress",
                                "message": "Uploading files",
                                "progress": progress,
                                "details": {
                                    "currentFile": current_file,
                                    "progress": f"{progress:.1f}%",
                                    "size": f"{parts[1]} {parts[2].split('/')[0]}"
                                }
                            }))
                        except Exception as e:
                            logger.error(f"Error parsing progress: {e}")

                    elif "upload:" in output:
                        current_file = output.split("upload:")[1].strip()
                        self.update_queue.put(("status", {
                            "type": "progress",
                            "message": f"Uploading {current_file}",
                            "progress": transferred_bytes / total_bytes * 100 if total_bytes > 0 else 0,
                            "details": {
                                "currentFile": current_file
                            }
                        }))

            # Check final status
            return_code = process.poll()
            if return_code == 0:
                self.update_queue.put(("status", {
                    "type": "completed",
                    "message": "Sync completed successfully",
                    "progress": 100,
                    "details": {
                        "currentFile": None,
                        "progress": "100%",
                        "size": None
                    }
                }))
                return True
            else:
                error_msg = f"Upload failed with code {return_code}"
                self.update_queue.put(("status", {
                    "type": "error",
                    "message": error_msg
                }))
                return False

        except Exception as e:
            logger.error(f"Error during sync: {e}")
            self.update_queue.put(("status", {
                "type": "error",
                "message": str(e)
            }))
            return False

    def _format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def stop_sync(self):
        """Stop the synchronization process."""
        self.stop_event.set()

    def sync(self, to_upload):
        """Start the sync process."""
        try:
            if not to_upload:
                self.update_queue.put(("status", {
                    "type": "status",
                    "message": "No files to upload",
                    "progress": 100
                }))
                return True

            total_files = len(to_upload)
            total_size = sum(os.path.getsize(os.path.join(self.sync_folder, f)) for f in to_upload)
            
            self.update_queue.put(("status", {
                "type": "progress",
                "message": f"Found {total_files} files to upload",
                "progress": 0,
                "details": {
                    "totalFiles": total_files,
                    "totalSize": self._format_size(total_size)
                }
            }))

            for index, file_path in enumerate(to_upload, 1):
                if self.stop_event.is_set():
                    self.update_queue.put(("status", {
                        "type": "status",
                        "message": "Sync stopped by user"
                    }))
                    return False

                try:
                    self._upload_file_with_progress(
                        os.path.join(self.sync_folder, file_path),
                        self.bucket_name,
                        file_path,
                        index,
                        total_files
                    )
                except Exception as e:
                    logger.error(f"Error uploading {file_path}: {e}")
                    self.update_queue.put(("status", f"Error: {e}"))
                    return False

            self.update_queue.put(("status", {
                "type": "status",
                "message": f"Successfully synced {total_files} files ({self._format_size(total_size)})"
            }))
            return True

        except Exception as e:
            logger.error(f"Error during sync: {e}")
            self.update_queue.put(("status", f"Error: {e}"))
            return False

    def _upload_file_with_progress(self, file_path, bucket, key, index, total_files):
        """Upload a file with progress tracking."""
        file_size = os.path.getsize(file_path)
        transferred_bytes = 0

        def callback(bytes_transferred):
            nonlocal transferred_bytes
            transferred_bytes += bytes_transferred
            file_progress = (transferred_bytes / file_size) * 100
            
            self.update_queue.put(("status", {
                "type": "progress",
                "message": f"Uploading {os.path.basename(key)}",
                "progress": file_progress,
                "details": {
                    "currentFile": key,
                    "progress": f"{file_progress:.1f}%",
                    "size": self._format_size(file_size)
                }
            }))

        try:
            self.s3_client.upload_file(
                file_path, 
                bucket, 
                key, 
                Callback=callback
            )
            
            # Add completion message after successful upload
            self.update_queue.put(("status", {
                "type": "completed",
                "message": "Sync completed successfully",
                "progress": 100,
                "details": {
                    "currentFile": None,
                    "progress": "100%",
                    "size": None
                }
            }))
        except Exception as e:
            raise Exception(f"Failed to upload {key}: {str(e)}")

    def get_local_files(self, folder):
        """Get list of local files."""
        local_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, folder)
                local_files.append(relative_path.replace('\\', '/'))
        return local_files

    def get_s3_files(self, bucket):
        """Get list of files in S3 bucket."""
        s3_files = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get('Contents', []):
                s3_files.append(obj['Key'])
        return s3_files

    def compare_files(self, local_files, s3_files):
        """Compare local and S3 files."""
        to_upload = set(local_files) - set(s3_files)
        to_download = set(s3_files) - set(local_files)
        return list(to_upload), list(to_download)