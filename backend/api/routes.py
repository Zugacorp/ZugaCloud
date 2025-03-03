from flask import Blueprint, jsonify, request
from ..aws.aws_integration import aws_integration
import logging
from urllib.parse import unquote
from ..api_requests import (
    ConfigHandler,
    FileHandler,
    SyncHandler,
    AuthHandler,
    HealthHandler,
    BucketHandler,
    APIException
)
from ..auth.auth import login_required

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

# Initialize handlers
config_handler = ConfigHandler(aws_integration)
file_handler = FileHandler(aws_integration)
sync_handler = SyncHandler(aws_integration)
auth_handler = AuthHandler(aws_integration)
health_handler = HealthHandler(aws_integration)
bucket_handler = BucketHandler(aws_integration)

@api_bp.route('/config', methods=['GET'])
def get_config():
    try:
        return config_handler.get_config()
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/config', methods=['POST'])
def update_config():
    try:
        return config_handler.update_config(request.json)
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/buckets', methods=['GET'])
def list_buckets():
    try:
        return bucket_handler.list_buckets()
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/files', methods=['GET'])
def list_files():
    try:
        path = request.args.get('path', '/')
        bucket = request.args.get('bucket')
        return file_handler.list_files(path, bucket)
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/sync/start', methods=['POST'])
def start_sync():
    try:
        data = request.json
        return sync_handler.start_sync(
            data.get('sync_folder'),
            data.get('bucket_name')
        )
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/validate-credentials', methods=['POST'])
def validate_credentials():
    try:
        return auth_handler.validate_credentials(request.json)
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/health', methods=['GET'])
def health_check():
    try:
        return health_handler.check_health()
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/check-credential-source', methods=['GET'])
def check_credential_source():
    try:
        return auth_handler.check_credential_source()
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/set-credential-source', methods=['POST'])
def set_credential_source():
    try:
        data = request.get_json()
        return auth_handler.set_credential_source(data.get('useEnvVars', False))
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/files/stream/<path:file_key>')
def stream_file(file_key):
    try:
        return file_handler.stream_file(file_key)
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/files/info', methods=['GET'])
def get_file_info():
    try:
        file_key = request.args.get('key')
        return file_handler.get_file_info(file_key)
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/files/local', methods=['DELETE'])
def delete_local_file():
    try:
        data = request.json
        if not data or 'path' not in data:
            return jsonify({'error': 'No path provided'}), 400
        return file_handler.delete_local_file(unquote(data['path']))
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/files/s3', methods=['DELETE'])
def delete_s3_file():
    try:
        data = request.json
        if not data or 'path' not in data:
            return jsonify({'error': 'No path provided'}), 400
        return file_handler.delete_s3_file(data['path'])
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code

@api_bp.route('/files/local/check', methods=['POST'])
def check_local_file():
    try:
        data = request.json
        if not data or 'path' not in data:
            return jsonify({'error': 'No path provided'}), 400
        return file_handler.check_local_file(data['path'])
    except APIException as e:
        return jsonify({'error': e.message}), e.status_code
# Add error handlers
@api_bp.errorhandler(APIException)
def handle_api_error(error):
    return jsonify({'error': error.message}), error.status_code

@api_bp.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {str(error)}")
    return jsonify({'error': str(error)}), 500

