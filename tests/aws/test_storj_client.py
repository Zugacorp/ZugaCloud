#!/usr/bin/env python3
"""
Test Storj client functionality.
This script tests the ability to connect to Storj, list buckets,
and verify access to the "zugacloud" bucket.
"""

import os
import sys
import logging
import boto3
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to the path so we can import the StorjClient
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR / 'backend'))

try:
    from aws.storj_client import StorjClient
except ImportError:
    logging.error("Could not import StorjClient from aws.storj_client")
    logging.info("Make sure the backend directory is in the Python path")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test-storj-client")

def load_credentials():
    """Load Storj credentials from environment variables"""
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
    
    # Check for Storj credentials
    credentials = {
        'storj_access_key': os.environ.get('STORJ_ACCESS_KEY'),
        'storj_secret_key': os.environ.get('STORJ_SECRET_KEY'),
        'storj_endpoint': os.environ.get('STORJ_ENDPOINT', 'https://gateway.eu1.storjshare.io'),
        # Fallbacks
        'aws_access_key': os.environ.get('AWS_ACCESS_KEY_ID'),
        'aws_secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
    }
    
    # Log credential availability
    logger.info("Credential availability:")
    logger.info(f"STORJ_ACCESS_KEY: {'Available' if credentials['storj_access_key'] else 'Missing'}")
    logger.info(f"STORJ_SECRET_KEY: {'Available' if credentials['storj_secret_key'] else 'Missing'}")
    logger.info(f"STORJ_ENDPOINT: {credentials['storj_endpoint']}")
    logger.info(f"AWS_ACCESS_KEY_ID (fallback): {'Available' if credentials['aws_access_key'] else 'Missing'}")
    logger.info(f"AWS_SECRET_ACCESS_KEY (fallback): {'Available' if credentials['aws_secret_key'] else 'Missing'}")
    
    return credentials

def test_storj_client_direct():
    """Test the StorjClient class directly"""
    logger.info("\n=== Testing StorjClient class directly ===")
    
    try:
        # Create StorjClient instance
        storj_client = StorjClient()
        logger.info("Successfully created StorjClient instance")
        
        # Check if client initialization worked
        if storj_client.s3_client:
            logger.info("✓ StorjClient initialized S3 client successfully")
        else:
            logger.error("✗ StorjClient failed to initialize S3 client")
            return False
        
        # Test bucket access validation
        logger.info("\nTesting bucket access validation:")
        bucket_name = "zugacloud"
        
        try:
            logger.info(f"Checking access to bucket: {bucket_name}")
            is_valid = storj_client.validate_bucket_access(bucket_name)
            if is_valid:
                logger.info(f"✓ Access to bucket '{bucket_name}' is valid")
            else:
                logger.error(f"✗ Access to bucket '{bucket_name}' is invalid")
                return False
        except Exception as e:
            logger.error(f"Error validating bucket access: {e}")
            return False
        
        # Try to generate a presigned URL
        logger.info("\nTesting presigned URL generation:")
        try:
            test_key = "test_object.txt"
            logger.info(f"Generating presigned URL for {test_key} in {bucket_name}")
            url = storj_client.generate_presigned_url(bucket_name, test_key, "put_object")
            if url:
                logger.info(f"✓ Successfully generated presigned URL: {url[:60]}...")
            else:
                logger.error("✗ Failed to generate presigned URL")
                return False
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error testing StorjClient: {e}")
        return False

def test_boto3_direct():
    """Test direct boto3 connection to Storj"""
    logger.info("\n=== Testing direct boto3 connection to Storj ===")
    
    credentials = load_credentials()
    
    # Use Storj credentials with fallback to AWS
    access_key = credentials['storj_access_key'] or credentials['aws_access_key']
    secret_key = credentials['storj_secret_key'] or credentials['aws_secret_key']
    endpoint = credentials['storj_endpoint']
    
    if not access_key or not secret_key:
        logger.error("Missing access key or secret key")
        return False
    
    try:
        # Create boto3 client for S3
        logger.info(f"Creating boto3 S3 client with endpoint: {endpoint}")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint
        )
        logger.info("Successfully created boto3 S3 client")
        
        # List buckets
        logger.info("Listing buckets:")
        response = s3_client.list_buckets()
        buckets = response.get('Buckets', [])
        
        if not buckets:
            logger.warning("No buckets found")
        else:
            logger.info(f"Found {len(buckets)} buckets:")
            for bucket in buckets:
                logger.info(f"- {bucket['Name']}")
                
            # Check if zugacloud bucket exists
            zugacloud_exists = any(bucket['Name'] == 'zugacloud' for bucket in buckets)
            if zugacloud_exists:
                logger.info("✓ 'zugacloud' bucket found")
            else:
                logger.warning("✗ 'zugacloud' bucket not found")
        
        # Try to list objects in a bucket
        target_bucket = 'zugacloud'
        try:
            logger.info(f"Listing objects in '{target_bucket}' bucket (first 10):")
            response = s3_client.list_objects_v2(Bucket=target_bucket, MaxKeys=10)
            
            objects = response.get('Contents', [])
            if not objects:
                logger.info(f"No objects found in '{target_bucket}' bucket")
            else:
                logger.info(f"Found {len(objects)} objects:")
                for obj in objects:
                    logger.info(f"- {obj['Key']} ({obj['Size']} bytes)")
                    
            logger.info(f"✓ Successfully accessed '{target_bucket}' bucket")
            
        except Exception as e:
            logger.error(f"Error listing objects in '{target_bucket}' bucket: {e}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error testing boto3 connection: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting Storj client tests")
    
    # Test boto3 direct connection
    if test_boto3_direct():
        logger.info("✓ Direct boto3 connection test passed")
    else:
        logger.error("✗ Direct boto3 connection test failed")
        
    # Test StorjClient class
    if test_storj_client_direct():
        logger.info("✓ StorjClient test passed")
    else:
        logger.error("✗ StorjClient test failed")
    
    logger.info("Storj client tests completed")
    
if __name__ == "__main__":
    main() 