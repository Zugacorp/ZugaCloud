#!/usr/bin/env python3
"""
Test if a specific Storj bucket exists using head_bucket operation.
This script tests if a specific bucket exists without trying to list all buckets.
"""

import os
import sys
import logging
import boto3
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from botocore.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test-head-bucket")

# Add the backend directory to the path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR / 'backend'))

def load_env_vars():
    """Load environment variables from .env file"""
    # Find and load .env file
    backend_env = ROOT_DIR / 'backend' / '.env'
    if backend_env.exists():
        logger.info(f"Loading .env from {backend_env}")
        load_dotenv(backend_env)
    else:
        root_env = ROOT_DIR / '.env'
        if root_env.exists():
            logger.info(f"Loading .env from {root_env}")
            load_dotenv(root_env)
        else:
            logger.warning("No .env file found. Relying on existing environment variables.")
    
    # Log environment variables
    access_key = os.environ.get('STORJ_ACCESS_KEY')
    secret_key = os.environ.get('STORJ_SECRET_KEY')
    endpoint = os.environ.get('STORJ_ENDPOINT', 'https://gateway.us1.storjshare.io')
    
    logger.info(f"STORJ_ACCESS_KEY: {access_key[:4]}...{access_key[-4:] if access_key else 'Not set'}")
    logger.info(f"STORJ_SECRET_KEY: {'*' * 10 if secret_key else 'Not set'}")
    logger.info(f"STORJ_ENDPOINT: {endpoint}")
    
    return {
        'access_key': access_key,
        'secret_key': secret_key,
        'endpoint': endpoint
    }

def test_head_bucket(bucket_name="zugacloud"):
    """Test if a specific bucket exists using head_bucket operation"""
    logger.info(f"\n=== Testing if bucket '{bucket_name}' exists ===")
    
    # Load environment variables
    env_vars = load_env_vars()
    
    if not env_vars['access_key'] or not env_vars['secret_key']:
        logger.error("Missing Storj credentials")
        return False
    
    try:
        # Create boto3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env_vars['access_key'],
            aws_secret_access_key=env_vars['secret_key'],
            endpoint_url=env_vars['endpoint'],
            region_name='us-east-1'  # Storj doesn't use regions, but boto3 requires one
        )
        
        logger.info(f"Checking if bucket '{bucket_name}' exists...")
        
        try:
            # Use head_bucket to check if bucket exists
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"✓ Bucket '{bucket_name}' exists and is accessible")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                logger.error(f"✗ Bucket '{bucket_name}' does not exist")
            elif error_code == '403':
                logger.error(f"✗ Access denied to bucket '{bucket_name}'")
            else:
                logger.error(f"✗ Error checking bucket '{bucket_name}': {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        return False

def test_with_different_configs(bucket_name="zugacloud"):
    """Test with different client configurations"""
    logger.info("\n=== Testing with different client configurations ===")
    
    # Load environment variables
    env_vars = load_env_vars()
    
    if not env_vars['access_key'] or not env_vars['secret_key']:
        logger.error("Missing Storj credentials")
        return False
    
    # Test configurations
    configs = [
        {
            'name': 'Default configuration',
            'config': {}
        },
        {
            'name': 'Path-style addressing',
            'config': {'s3': {'addressing_style': 'path'}}
        },
        {
            'name': 'Virtual-hosted-style addressing',
            'config': {'s3': {'addressing_style': 'virtual'}}
        },
        {
            'name': 'Signature Version 2',
            'config': {'signature_version': 's3'}
        },
        {
            'name': 'Signature Version 4',
            'config': {'signature_version': 's3v4'}
        },
        {
            'name': 'EU1 endpoint',
            'endpoint': 'https://gateway.eu1.storjshare.io'
        }
    ]
    
    success = False
    
    for config_option in configs:
        logger.info(f"\nTesting with {config_option['name']}:")
        
        try:
            # Create boto3 client with specific configuration
            s3_client = boto3.client(
                's3',
                aws_access_key_id=env_vars['access_key'],
                aws_secret_access_key=env_vars['secret_key'],
                endpoint_url=config_option.get('endpoint', env_vars['endpoint']),
                region_name='us-east-1',
                config=Config(**config_option.get('config', {}))
            )
            
            try:
                # Use head_bucket to check if bucket exists
                s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"✓ Success with {config_option['name']}")
                success = True
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                if error_code == '404':
                    logger.error(f"✗ Bucket '{bucket_name}' does not exist")
                elif error_code == '403':
                    logger.error(f"✗ Access denied to bucket '{bucket_name}'")
                else:
                    logger.error(f"✗ Error: {e}")
                    
        except Exception as e:
            logger.error(f"Error creating S3 client with {config_option['name']}: {e}")
    
    return success

def main():
    """Run all tests"""
    logger.info("Starting head_bucket tests")
    
    # Test if bucket exists
    bucket_exists = test_head_bucket()
    
    # If basic test fails, try different configurations
    if not bucket_exists:
        logger.info("\nBasic test failed. Trying different configurations...")
        success = test_with_different_configs()
        
        if success:
            logger.info("\n✓ Found a working configuration!")
        else:
            logger.error("\n✗ All configurations failed")
            logger.info("\nPossible issues:")
            logger.info("1. The bucket 'zugacloud' might not exist")
            logger.info("2. The credentials might not have permission to access the bucket")
            logger.info("3. The endpoint might be incorrect")
            logger.info("\nSuggested actions:")
            logger.info("1. Verify the bucket name in the Storj web console")
            logger.info("2. Check if your credentials have the necessary permissions")
            logger.info("3. Try creating a new bucket in the Storj web console")
    
    logger.info("\nHead bucket tests completed")
    
if __name__ == "__main__":
    main() 