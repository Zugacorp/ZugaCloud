import boto3
import os
from dotenv import load_dotenv
import logging
from botocore.exceptions import ClientError
from pathlib import Path
from botocore.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if all required environment variables are set"""
    try:
        # Find and load the correct .env file
        current_dir = Path(__file__).parent  # Get the directory containing this test file
        project_root = current_dir.parent.parent  # Go up two levels to project root
        backend_env = project_root / 'backend' / '.env'
        
        logger.info(f"Looking for .env at: {backend_env}")
        
        if not backend_env.exists():
            raise EnvironmentError(f"Backend .env file not found at {backend_env}!")
            
        load_dotenv(backend_env)
        
        # Check required environment variables - fall back to AWS vars if Storj specific ones don't exist
        storj_access_key = os.environ.get('STORJ_ACCESS_KEY') or os.environ.get('AWS_ACCESS_KEY_ID')
        storj_secret_key = os.environ.get('STORJ_SECRET_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY')
        storj_endpoint = os.environ.get('STORJ_ENDPOINT') or 'https://gateway.eu1.storjshare.io'
        
        if not storj_access_key:
            raise EnvironmentError("Missing STORJ_ACCESS_KEY environment variable")
        if not storj_secret_key:
            raise EnvironmentError("Missing STORJ_SECRET_KEY environment variable")
        
        # Log configuration (without sensitive data)
        logger.info("\n=== Storj Configuration ===")
        logger.info(f"Endpoint: {storj_endpoint}")
        logger.info(f"Access Key: {storj_access_key[:4]}...{storj_access_key[-4:] if len(storj_access_key) > 8 else ''}")
        logger.info(f"Secret Key Length: {len(storj_secret_key)}")
        
        # Store for use by tests
        os.environ['EFFECTIVE_STORJ_ACCESS_KEY'] = storj_access_key
        os.environ['EFFECTIVE_STORJ_SECRET_KEY'] = storj_secret_key
        os.environ['EFFECTIVE_STORJ_ENDPOINT'] = storj_endpoint
        
        return True
        
    except Exception as e:
        logger.error(f"Environment check failed: {str(e)}")
        return False

def test_storj_connection():
    """Test Storj connection using boto3 with S3-compatible API"""
    try:
        # Create session with explicit credentials
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('EFFECTIVE_STORJ_ACCESS_KEY'),
            aws_secret_access_key=os.environ.get('EFFECTIVE_STORJ_SECRET_KEY'),
            endpoint_url=os.environ.get('EFFECTIVE_STORJ_ENDPOINT'),
            region_name='us-east-1',  # Storj doesn't use regions, but boto3 requires one
            config=Config(
                s3={'addressing_style': 'path'},
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        # List buckets to verify connection
        try:
            response = s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            logger.info(f"Successfully connected to Storj. Found {len(buckets)} buckets: {', '.join(buckets)}")
            
            # Check for zugacloud bucket specifically
            if 'zugacloud' in buckets:
                logger.info(f"The 'zugacloud' bucket was found in available buckets!")
                
                # Test access to zugacloud bucket
                logger.info(f"Testing access to 'zugacloud' bucket...")
                objects = s3_client.list_objects_v2(Bucket='zugacloud', MaxKeys=1)
                if 'Contents' in objects and len(objects['Contents']) > 0:
                    logger.info(f"Successfully accessed 'zugacloud' bucket. Found {len(objects['Contents'])} objects.")
                else:
                    logger.info(f"Successfully accessed 'zugacloud' bucket. The bucket is empty.")
            else:
                logger.warning("The 'zugacloud' bucket was NOT found in available buckets.")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                logger.error("Access denied when trying to list buckets. Please check your credentials.")
            else:
                logger.error(f"Error listing buckets: {str(e)}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to Storj: {str(e)}")
        return False

def test_storj_credentials():
    """Main test function for Storj credentials"""
    try:
        logger.info("\n=== Starting Storj Credentials Test ===")
        
        # Step 1: Check environment variables
        if not check_environment_variables():
            logger.error("Environment variable check failed!")
            return False
            
        # Step 2: Test Storj connection
        if not test_storj_connection():
            logger.error("Storj connection test failed!")
            return False
            
        logger.info("\n=== Storj Credentials Test Completed Successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"\n=== Storj Credentials Test Failed ===")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error message: {str(e)}")
        return False

if __name__ == "__main__":
    test_storj_credentials() 