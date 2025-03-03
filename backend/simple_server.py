from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import logging
import boto3
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('simple-server')

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load environment variables
load_dotenv('backend/.env')

# Configuration paths
CONFIG_PATH = 'backend/aws/config/config.json'

def get_storj_credentials():
    """Get Storj credentials from environment variables"""
    credentials = {
        'storj_access_key': os.environ.get('STORJ_ACCESS_KEY', ''),
        'storj_secret_key': os.environ.get('STORJ_SECRET_KEY', ''),
        'storj_endpoint': os.environ.get('STORJ_ENDPOINT', 'https://gateway.us1.storjshare.io'),
        'storage_provider': 'storj'
    }
    return credentials

def get_aws_credentials():
    """Get AWS credentials from environment variables"""
    credentials = {
        'aws_access_key': os.environ.get('AWS_ACCESS_KEY_ID', ''),
        'aws_secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
        'aws_region': os.environ.get('AWS_REGION', 'us-east-1'),
        'storage_provider': 'aws'
    }
    return credentials

def save_config(config):
    """Save configuration to config file"""
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        return False

def load_config():
    """Load configuration from config file"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        else:
            # Return default config with Storj credentials
            config = get_storj_credentials()
            save_config(config)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return get_storj_credentials()

def list_buckets(config):
    """List buckets using the provided configuration"""
    try:
        if config.get('storage_provider') == 'storj':
            # Use Storj credentials
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.get('storj_access_key'),
                aws_secret_access_key=config.get('storj_secret_key'),
                endpoint_url=config.get('storj_endpoint'),
                config=boto3.session.Config(
                    signature_version='s3v4',
                    s3={'addressing_style': 'virtual'}
                )
            )
        else:
            # Use AWS credentials
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.get('aws_access_key'),
                aws_secret_access_key=config.get('aws_secret_key'),
                region_name=config.get('aws_region')
            )
        
        response = s3_client.list_buckets()
        buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
        return buckets
    except Exception as e:
        logger.error(f"Error listing buckets: {str(e)}")
        return []

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config = load_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        data = request.json
        if data.get('storage_provider') == 'storj':
            config = {
                'storj_access_key': data.get('storj_access_key', ''),
                'storj_secret_key': data.get('storj_secret_key', ''),
                'storj_endpoint': data.get('storj_endpoint', 'https://gateway.us1.storjshare.io'),
                'storage_provider': 'storj'
            }
        else:
            config = {
                'aws_access_key': data.get('aws_access_key', ''),
                'aws_secret_key': data.get('aws_secret_key', ''),
                'aws_region': data.get('aws_region', 'us-east-1'),
                'storage_provider': 'aws'
            }
        
        save_config(config)
        return jsonify({'status': 'success', 'message': 'Configuration updated successfully'})
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/buckets', methods=['GET'])
def get_buckets():
    """Get list of available buckets"""
    config = load_config()
    buckets = list_buckets(config)
    return jsonify({'buckets': buckets})

if __name__ == '__main__':
    # Initialize with environment variables if config doesn't exist
    if not os.path.exists(CONFIG_PATH):
        initial_config = get_storj_credentials()
        save_config(initial_config)
        logger.info(f"Created initial config with Storj credentials")
    
    # Log the current configuration
    config = load_config()
    logger.info(f"Current storage provider: {config.get('storage_provider')}")
    
    # Start the server
    app.run(debug=True, host='0.0.0.0', port=5000) 