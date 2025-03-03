#!/usr/bin/env python3
"""
Simple direct test of Storj connection using boto3.
This script attempts to connect to Storj using different configurations
to help diagnose connection issues.
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
logger = logging.getLogger("direct-storj-test")

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

def test_connection_with_path_style():
    """Test connection with path-style addressing"""
    logger.info("\n=== Testing with path-style addressing ===")
    
    env = load_env_vars()
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env['access_key'],
            aws_secret_access_key=env['secret_key'],
            endpoint_url=env['endpoint'],
            region_name='us-east-1',  # Required by boto3 but not used by Storj
            config=Config(
                s3={'addressing_style': 'path'},
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        logger.info("Client created successfully, attempting to list buckets...")
        response = s3_client.list_buckets()
        
        buckets = response.get('Buckets', [])
        logger.info(f"Success! Found {len(buckets)} buckets:")
        for bucket in buckets:
            logger.info(f"- {bucket['Name']}")
            
        return True
    except Exception as e:
        logger.error(f"Error with path-style addressing: {e}")
        return False

def test_connection_with_virtual_hosted_style():
    """Test connection with virtual-hosted-style addressing"""
    logger.info("\n=== Testing with virtual-hosted-style addressing ===")
    
    env = load_env_vars()
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env['access_key'],
            aws_secret_access_key=env['secret_key'],
            endpoint_url=env['endpoint'],
            region_name='us-east-1',
            config=Config(
                s3={'addressing_style': 'virtual'},
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        logger.info("Client created successfully, attempting to list buckets...")
        response = s3_client.list_buckets()
        
        buckets = response.get('Buckets', [])
        logger.info(f"Success! Found {len(buckets)} buckets:")
        for bucket in buckets:
            logger.info(f"- {bucket['Name']}")
            
        return True
    except Exception as e:
        logger.error(f"Error with virtual-hosted-style addressing: {e}")
        return False

def test_connection_with_auto_style():
    """Test connection with auto-style addressing"""
    logger.info("\n=== Testing with auto-style addressing ===")
    
    env = load_env_vars()
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env['access_key'],
            aws_secret_access_key=env['secret_key'],
            endpoint_url=env['endpoint'],
            region_name='us-east-1',
            config=Config(
                s3={'addressing_style': 'auto'},
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        logger.info("Client created successfully, attempting to list buckets...")
        response = s3_client.list_buckets()
        
        buckets = response.get('Buckets', [])
        logger.info(f"Success! Found {len(buckets)} buckets:")
        for bucket in buckets:
            logger.info(f"- {bucket['Name']}")
            
        return True
    except Exception as e:
        logger.error(f"Error with auto-style addressing: {e}")
        return False

def test_connection_with_different_signature():
    """Test connection with different signature version"""
    logger.info("\n=== Testing with different signature version ===")
    
    env = load_env_vars()
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env['access_key'],
            aws_secret_access_key=env['secret_key'],
            endpoint_url=env['endpoint'],
            region_name='us-east-1',
            config=Config(
                signature_version='s3',  # Try older signature version
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        logger.info("Client created successfully, attempting to list buckets...")
        response = s3_client.list_buckets()
        
        buckets = response.get('Buckets', [])
        logger.info(f"Success! Found {len(buckets)} buckets:")
        for bucket in buckets:
            logger.info(f"- {bucket['Name']}")
            
        return True
    except Exception as e:
        logger.error(f"Error with different signature version: {e}")
        return False

def test_connection_with_eu1_endpoint():
    """Test connection with EU1 endpoint"""
    logger.info("\n=== Testing with EU1 endpoint ===")
    
    env = load_env_vars()
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env['access_key'],
            aws_secret_access_key=env['secret_key'],
            endpoint_url='https://gateway.eu1.storjshare.io',  # Force EU1 endpoint
            region_name='us-east-1',
            config=Config(
                s3={'addressing_style': 'path'},
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        logger.info("Client created successfully, attempting to list buckets...")
        response = s3_client.list_buckets()
        
        buckets = response.get('Buckets', [])
        logger.info(f"Success! Found {len(buckets)} buckets:")
        for bucket in buckets:
            logger.info(f"- {bucket['Name']}")
            
        return True
    except Exception as e:
        logger.error(f"Error with EU1 endpoint: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting direct Storj connection tests")
    
    results = {
        "path_style": test_connection_with_path_style(),
        "virtual_hosted_style": test_connection_with_virtual_hosted_style(),
        "auto_style": test_connection_with_auto_style(),
        "different_signature": test_connection_with_different_signature(),
        "eu1_endpoint": test_connection_with_eu1_endpoint()
    }
    
    logger.info("\n=== Test Results Summary ===")
    for test_name, result in results.items():
        logger.info(f"{test_name}: {'SUCCESS' if result else 'FAILED'}")
    
    if any(results.values()):
        logger.info("\nAt least one test succeeded! Check the logs to see which configuration worked.")
    else:
        logger.error("\nAll tests failed. There might be an issue with the credentials or network connectivity.")
    
if __name__ == "__main__":
    main() 