from flask import Blueprint, jsonify, request, send_file, send_from_directory
from ..aws_integration import aws_integration
from ..sync_queue import sync_queue
import logging
import os
import json
import boto3
import asyncio
import queue
from urllib.parse import unquote
from ..requests import check_health, APIException

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)

@api.route('/config', methods=['GET'])
def get_config():
    try:
        config = aws_integration.config
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/buckets', methods=['GET'])
def list_buckets():
    try:
        if not aws_integration.s3:
            return jsonify({'error': 'AWS not initialized'}), 500
        
        response = aws_integration.s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return jsonify(buckets)
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/files', methods=['GET'])
def list_files():
    try:
        path = request.args.get('path', '/')
        bucket = request.args.get('bucket', aws_integration.bucket_name)
        
        logger.info(f"Listing files for path: {path} in bucket: {bucket}")
        
        if not aws_integration.s3:
            return jsonify({'files': [], 'error': 'AWS not initialized'})

        # First, list all objects to get both files and folder markers
        response = aws_integration.s3.list_objects_v2(
            Bucket=bucket,
            Prefix=path if path != '/' else '',
            Delimiter='/'
        )
        
        files = []
        
        # Handle folders (including empty ones)
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                folder_name = os.path.basename(prefix['Prefix'].rstrip('/'))
                total_size, file_count = aws_integration.calculate_folder_stats(bucket, prefix['Prefix'])
                files.append({
                    'Key': prefix['Prefix'],
                    'Type': 'folder',
                    'TotalSize': total_size,
                    'FileCount': file_count,
                    'Name': folder_name,
                    'LastModified': None
                })

        # Handle files
        if 'Contents' in response:
            for item in response['Contents']:
                # Skip the current directory marker
                if item['Key'].rstrip('/') == path.rstrip('/'):
                    continue
                
                # Skip items that represent folders (end with /)
                if item['Key'].endswith('/'):
                    continue
                    
                file_name = os.path.basename(item['Key'])
                file_data = {
                    'Key': item['Key'],
                    'Type': 'object',
                    'Size': item['Size'],
                    'LastModified': item['LastModified'].isoformat(),
                    'Name': file_name
                }
                
                # Add thumbnail and preview URLs for videos
                if aws_integration.is_video_file(item['Key']):
                    paths = aws_integration.thumbnail_manager.get_thumbnail_paths(item['Key'])
                    
                    if not os.path.exists(paths['static']):
                        aws_integration.thumbnail_manager.generate_thumbnail(item['Key'])
                    
                    if os.path.exists(paths['static']):
                        file_data['thumbnailUrl'] = f'/assets/thumbnails/static/{os.path.basename(paths["static"])}'
                    
                    file_data['previewUrl'] = aws_integration.generate_presigned_url(bucket, item['Key'])
                
                files.append(file_data)

        return jsonify({'files': files})
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'files': [], 'error': str(e)})

@api.route('/files/stream/<path:file_key>')
def stream_file(file_key):
    try:
        bucket_name = aws_integration.config.get('bucket_name')
        if not bucket_name:
            return jsonify({'error': 'No bucket configured'}), 400

        url = aws_integration.s3.generate_presigned_url(
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
        return jsonify({'error': str(e)}), 500

@api.route('/select-folder', methods=['POST'])
def select_folder():
    try:
        data = request.json
        folder_path = data.get('path')
        
        if not folder_path:
            return jsonify({'error': 'No folder path provided'}), 400
            
        # Update config with the new folder path
        aws_integration.config['sync_folder'] = folder_path
        
        # Save the updated config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
        with open(config_path, 'w') as f:
            json.dump(aws_integration.config, f, indent=4)
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error selecting folder: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/validate-credentials', methods=['POST'])
def validate_credentials():
    try:
        credentials = request.json
        
        # Create temporary client to test credentials
        test_client = boto3.client(
            's3',
            aws_access_key_id=credentials.get('aws_access_key'),
            aws_secret_access_key=credentials.get('aws_secret_key'),
            region_name=credentials.get('region', 'us-east-2')
        )
        
        # Test credentials by listing buckets
        test_client.list_buckets()
        
        # If successful, update config
        aws_integration.config.update({
            'aws_access_key': credentials.get('aws_access_key'),
            'aws_secret_key': credentials.get('aws_secret_key'),
            'region': credentials.get('region', 'us-east-2')
        })
        
        # Save updated config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
        with open(config_path, 'w') as f:
            json.dump(aws_integration.config, f, indent=4)
            
        # Reinitialize AWS client with new credentials
        aws_integration.initialize_s3_client()
        
        return jsonify({'valid': True, 'message': 'Credentials validated successfully'})
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        return jsonify({
            'valid': False,
            'message': str(e)
        }), 400

@api.route('/config', methods=['POST'])
def update_config():
    try:
        new_config = request.json
        current_config = aws_integration.config.copy()
        
        # Update config
        current_config.update(new_config)
        
        # Save to file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
        with open(config_path, 'w') as f:
            json.dump(current_config, f, indent=4)
            
        # Update AWS integration
        aws_integration.config = current_config
        aws_integration.initialize_s3_client()
        
        return jsonify(current_config)
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/assets/thumbnails/<type>/<path:filename>')
def serve_thumbnail(type, filename):
    """Serve thumbnail files"""
    try:
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'frontend',
            'assets',
            'thumbnails'
        )
        
        if type not in ['static', 'animated']:
            return jsonify({'error': 'Invalid thumbnail type'}), 400
            
        thumbnail_dir = os.path.join(base_dir, type)
        return send_from_directory(thumbnail_dir, filename)
    except Exception as e:
        logger.error(f"Error serving thumbnail {filename}: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/sync/start', methods=['POST'])
def start_sync():
    try:
        data = request.json
        sync_folder = data.get('sync_folder')
        bucket_name = data.get('bucket_name')

        if not sync_folder or not bucket_name:
            return jsonify({
                'error': 'Missing required sync_folder or bucket_name'
            }), 400

        # Use the global sync queue
        from ..file_sync import FileSync
        file_sync = FileSync(aws_integration)  # Remove sync_queue parameter

        # Update config
        file_sync.update_config({
            'aws_access_key': aws_integration.config.get('aws_access_key'),
            'aws_secret_key': aws_integration.config.get('aws_secret_key'),
            'region': aws_integration.config.get('region'),
            'sync_folder': sync_folder,
            'bucket_name': bucket_name,
            'no_delete': True
        })

        # Start sync in a background thread to not block the request
        import threading
        def run_sync():
            try:
                # Compare files without considering deletions
                to_upload, _ = aws_integration.compare_local_and_remote(sync_folder, bucket_name)
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
        return jsonify({'error': str(e)}), 500

@api.route('/sync/status', methods=['GET'])
def get_sync_status():
    try:
        status = {}
        completed_status = None
        
        try:
            while True:
                status_data = sync_queue.get_nowait()
                
                if isinstance(status_data, tuple):
                    status_type, status_content = status_data
                    if status_type == "status" and isinstance(status_content, dict):
                        if status_content.get("type") == "completed":
                            completed_status = status_content
                        status = status_content
                else:
                    status = {"type": "status", "message": str(status_data)}
                    
        except queue.Empty:
            if completed_status:
                logger.info("Returning completion status")
                return jsonify(completed_status)
            if not status:
                status = {"type": "status", "message": "Idle"}
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error in get_sync_status: {e}")
        return jsonify({
            "type": "error",
            "message": str(e)
        }), 500

@api.route('/files/info', methods=['GET'])
def get_file_info():
    """Get detailed file information including sync status."""
    try:
        file_key = request.args.get('key')
        if not file_key:
            return jsonify({'error': 'No file key provided'}), 400
            
        # Get file metadata from S3
        try:
            metadata = aws_integration.s3.head_object(
                Bucket=aws_integration.bucket_name,
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
            
        except aws_integration.s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return jsonify({'error': 'File not found'}), 404
            else:
                raise
                
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/sync/stop', methods=['POST'])
def stop_sync():
    try:
        # Initialize FileSync if needed
        from ..file_sync import FileSync
        sync_queue = queue.Queue()
        file_sync = FileSync(aws_integration, sync_queue)
        
        # Stop the sync process
        file_sync.stop_sync()
        
        return jsonify({
            "type": "status",
            "message": "Sync stopped"
        })
    except Exception as e:
        logger.error(f"Error stopping sync: {str(e)}")
        return jsonify({
            "type": "status",
            "message": f"Error: {str(e)}"
        }), 500

@api.route('/files/local', methods=['DELETE'])
def delete_local_file():
    try:
        data = request.json
        if not data or 'path' not in data:
            return jsonify({'error': 'No path provided'}), 400

        file_path = unquote(data['path'])  # Decode the URL-encoded path
        sync_folder = aws_integration.config.get('sync_folder')
        
        if not sync_folder:
            return jsonify({'error': 'No sync folder configured'}), 400

        # Construct absolute path and normalize it
        absolute_path = os.path.normpath(os.path.join(sync_folder, file_path))
        
        # Security check: ensure the path is within sync folder
        if not absolute_path.startswith(os.path.normpath(sync_folder)):
            return jsonify({'error': 'Invalid path'}), 403

        if os.path.exists(absolute_path):
            os.remove(absolute_path)
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        logger.error(f"Error deleting local file: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/files/s3', methods=['DELETE'])
def delete_s3_file():
    try:
        data = request.json
        if not data or 'path' not in data:
            return jsonify({'error': 'No path provided'}), 400

        bucket_name = aws_integration.bucket_name
        if not bucket_name:
            return jsonify({'error': 'No bucket configured'}), 400

        # Delete the object from S3
        try:
            aws_integration.s3.delete_object(
                Bucket=bucket_name,
                Key=data['path']
            )
            return jsonify({'success': True})
        except aws_integration.s3.exceptions.NoSuchKey:
            return jsonify({'error': 'File not found in S3'}), 404
        except aws_integration.s3.exceptions.ClientError as e:
            logger.error(f"AWS error deleting object: {e}")
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        logger.error(f"Error deleting S3 file: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/files/local/check', methods=['POST'])
def check_local_file():
    try:
        data = request.json
        if not data or 'path' not in data:
            return jsonify({'error': 'No path provided'}), 400

        sync_folder = aws_integration.config.get('sync_folder')
        if not sync_folder:
            return jsonify({'exists': False})

        # Construct the full local path
        local_path = os.path.join(sync_folder, data['path'].lstrip('/'))
        
        # Check if file exists
        exists = os.path.isfile(local_path)
        
        return jsonify({'exists': exists})
    except Exception as e:
        logger.error(f"Error checking local file: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/check-credential-source', methods=['GET'])
def check_credential_source():
    try:
        using_env_vars = bool(
            os.environ.get('AWS_ACCESS_KEY') and 
            os.environ.get('AWS_SECRET_KEY')
        )
        return jsonify({'usingEnvVars': using_env_vars})
    except Exception as e:
        logger.error(f"Error checking credential source: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/set-credential-source', methods=['POST'])
def set_credential_source():
    try:
        data = request.get_json()
        logger.info(f"Received credential source update request: {data}")
        
        use_env_vars = data.get('useEnvVars', False)
        logger.info(f"Checking environment variables: AWS_ACCESS_KEY={bool(os.environ.get('AWS_ACCESS_KEY'))}, "
                   f"VENV_AWS_ACCESS_KEY={bool(os.environ.get('VENV_AWS_ACCESS_KEY'))}")
        
        # Update config to reflect preference
        aws_integration.config['prefer_env_vars'] = use_env_vars
        
        # Save to config file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
        with open(config_path, 'w') as f:
            json.dump(aws_integration.config, f, indent=4)
            
        # Reinitialize AWS client
        aws_integration.initialize_s3_client()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error setting credential source: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return check_health()
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Add error handlers
@api.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {str(error)}")
    return jsonify({'error': str(error)}), 500
