#!/usr/bin/env python3
"""
Simple Flask server for testing the bucket selector.
This server provides the minimal API endpoints needed for the bucket selector to work.
"""

import os
import sys
import json
import logging
import boto3
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv
from botocore.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("simple-server")

# Create Flask app
app = Flask(__name__)
CORS(app)

# Load environment variables
root_dir = Path(__file__).parent.parent
backend_env = root_dir / 'backend' / '.env'
if backend_env.exists():
    logger.info(f"Loading .env from {backend_env}")
    load_dotenv(backend_env)
else:
    logger.warning(f"No .env file found at {backend_env}")

# Load config
config_path = root_dir / 'backend' / 'aws' / 'config' / 'config.json'
if config_path.exists():
    with open(config_path, 'r') as f:
        config = json.load(f)
    logger.info(f"Loaded config from {config_path}")
else:
    config = {}
    logger.warning(f"No config file found at {config_path}")

# API endpoints
@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    logger.info("GET /api/config")
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    logger.info("POST /api/config")
    new_config = request.json
    config.update(new_config)
    
    # Save config
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    return jsonify(config)

@app.route('/api/buckets', methods=['GET'])
def list_buckets():
    """List all available S3 buckets"""
    logger.info("GET /api/buckets")
    
    # Check if a specific provider is requested
    provider = request.args.get('provider', config.get('storage_provider', 'storj'))
    logger.info(f"Provider: {provider}")
    
    try:
        # Get credentials
        if provider == 'storj':
            access_key = config.get('storj_access_key') or os.environ.get('STORJ_ACCESS_KEY')
            secret_key = config.get('storj_secret_key') or os.environ.get('STORJ_SECRET_KEY')
            endpoint = config.get('storj_endpoint') or os.environ.get('STORJ_ENDPOINT') or 'https://gateway.us1.storjshare.io'
        else:
            access_key = config.get('aws_access_key') or os.environ.get('AWS_ACCESS_KEY_ID')
            secret_key = config.get('aws_secret_key') or os.environ.get('AWS_SECRET_ACCESS_KEY')
            endpoint = None
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint,
            region_name='us-east-1',
            config=Config(
                s3={'addressing_style': 'path'},
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        # List buckets
        response = s3_client.list_buckets()
        buckets = []
        
        # Format bucket list
        for bucket in response.get('Buckets', []):
            bucket_info = {
                'name': bucket['Name'],
                'creation_date': bucket['CreationDate'].isoformat() if 'CreationDate' in bucket else None,
            }
            
            # Mark zugacloud bucket as recommended for Storj
            if provider == 'storj' and bucket['Name'] == 'zugacloud':
                bucket_info['recommended'] = True
                bucket_info['description'] = 'Recommended Storj bucket'
            
            buckets.append(bucket_info)
        
        return jsonify(buckets)
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting simple server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 