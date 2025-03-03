#!/usr/bin/env python3
"""
Test direct access to a specific Storj bucket.
This script attempts to access the 'zugacloud' bucket directly
without listing all buckets first.
"""

import os
import sys
import logging
import boto3
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
logger = logging.getLogger("direct-bucket-test")

def load_env_vars():
    """Load environment variables from .env file"""
    root_dir = Path(__file__).parent.parent.parent
    backend_env = root_dir / 'backend' / '.env'
    
    if backend_env.exists():
        logger.info(f"Loading .env from {backend_env}")
        load_dotenv(backend_env)
    else:
        logger.warning(f"No .env file found at {backend_env}")
        
    # Log environment variables (without showing full secrets)
    storj_access_key = os.environ.get('STORJ_ACCESS_KEY')
    storj_secret_key = os.environ.get('STORJ_SECRET_KEY')
    storj_endpoint = os.environ.get('STORJ_ENDPOINT')
    
    logger.info("Environment variables:")
    if storj_access_key:
        logger.info(f"STORJ_ACCESS_KEY: {storj_access_key[:4]}...{storj_access_key[-4:]}")
    else:
        logger.info("STORJ_ACCESS_KEY: Not set")
        
    if storj_secret_key:
        logger.info(f"STORJ_SECRET_KEY: {len(storj_secret_key)} characters")
    else:
        logger.info("STORJ_SECRET_KEY: Not set")
        
    logger.info(f"STORJ_ENDPOINT: {storj_endpoint}")
    
    return {
        'access_key': storj_access_key,
        'secret_key': storj_secret_key,
        'endpoint': storj_endpoint or 'https://gateway.us1.storjshare.io'
    }

def test_direct_bucket_access(bucket_name="zugacloud"):
    """Test direct access to a specific bucket"""
    logger.info(f"\n=== Testing direct access to bucket: {bucket_name} ===")
    
    env = load_env_vars()
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env['access_key'],
            aws_secret_access_key=env['secret_key'],
            endpoint_url=env['endpoint'],
            region_name='us-east-1',
            config=Config(
                s3={'addressing_style': 'path'},
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        logger.info(f"Client created successfully, attempting to list objects in bucket: {bucket_name}...")
        
        try:
            # Try to list objects in the bucket
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                MaxKeys=10
            )
            
            objects = response.get('Contents', [])
            logger.info(f"Success! Found {len(objects)} objects in bucket '{bucket_name}':")
            for obj in objects:
                logger.info(f"- {obj['Key']} ({obj['Size']} bytes)")
                
            return True
        except Exception as e:
            logger.error(f"Error accessing bucket '{bucket_name}': {e}")
            
            # Try to check if bucket exists
            logger.info(f"Checking if bucket '{bucket_name}' exists...")
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"Bucket '{bucket_name}' exists but we can't list objects")
                return False
            except Exception as e2:
                logger.error(f"Error checking if bucket exists: {e2}")
                return False
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        return False

def test_create_bucket(bucket_name="zugacloud-test"):
    """Test creating a new bucket"""
    logger.info(f"\n=== Testing bucket creation: {bucket_name} ===")
    
    env = load_env_vars()
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env['access_key'],
            aws_secret_access_key=env['secret_key'],
            endpoint_url=env['endpoint'],
            region_name='us-east-1',
            config=Config(
                s3={'addressing_style': 'path'},
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        logger.info(f"Client created successfully, attempting to create bucket: {bucket_name}...")
        
        try:
            # Try to create a new bucket
            s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"Success! Created bucket '{bucket_name}'")
            return True
        except Exception as e:
            logger.error(f"Error creating bucket '{bucket_name}': {e}")
            return False
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting direct bucket access tests")
    
    # Test direct access to 'zugacloud' bucket
    zugacloud_result = test_direct_bucket_access("zugacloud")
    
    # Test direct access to 'zugacloud-test' bucket (might not exist)
    zugacloud_test_result = test_direct_bucket_access("zugacloud-test")
    
    # If we couldn't access either bucket, try creating a new one
    if not zugacloud_result and not zugacloud_test_result:
        logger.info("Could not access existing buckets, trying to create a new one...")
        create_result = test_create_bucket("zugacloud-test")
    else:
        create_result = False
    
    logger.info("\n=== Test Results Summary ===")
    logger.info(f"Access to 'zugacloud' bucket: {'SUCCESS' if zugacloud_result else 'FAILED'}")
    logger.info(f"Access to 'zugacloud-test' bucket: {'SUCCESS' if zugacloud_test_result else 'FAILED'}")
    logger.info(f"Create 'zugacloud-test' bucket: {'SUCCESS' if create_result else 'NOT ATTEMPTED' if zugacloud_result or zugacloud_test_result else 'FAILED'}")
    
    if zugacloud_result or zugacloud_test_result or create_result:
        logger.info("\nAt least one test succeeded! Check the logs to see which operation worked.")
    else:
        logger.error("\nAll tests failed. There might be an issue with the credentials or permissions.")
        logger.info("\nPossible issues:")
        logger.info("1. The access key and secret key might be incorrect")
        logger.info("2. The credentials might not have permission to access or create buckets")
        logger.info("3. The buckets might not exist or might be in a different region")
        logger.info("4. There might be network connectivity issues")
        logger.info("\nSuggested actions:")
        logger.info("1. Verify your Storj credentials in the Storj web console")
        logger.info("2. Check if the buckets exist in your Storj account")
        logger.info("3. Create a new bucket in the Storj web console and try accessing it")
        logger.info("4. Check if your credentials have the necessary permissions")
    
if __name__ == "__main__":
    main() 