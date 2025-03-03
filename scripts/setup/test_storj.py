import boto3
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_storj_connection():
    """Test connection to Storj and bucket access"""
    try:
        # Load environment variables from .env.backend
        env_path = Path(__file__).parent.parent.parent / 'backend' / 'config' / '.env.backend'
        load_dotenv(env_path)
        
        logger.info("Testing Storj connection...")
        
        # Verify environment variables are loaded
        access_key = os.getenv('STORJ_ACCESS_KEY')
        secret_key = os.getenv('STORJ_SECRET_KEY')
        endpoint = os.getenv('STORJ_ENDPOINT')
        
        if not all([access_key, secret_key, endpoint]):
            raise ValueError("Missing required Storj credentials in .env.backend")
        
        logger.info("✅ Successfully loaded Storj credentials")
        
        # Create S3 client with Storj credentials
        s3_client = boto3.client('s3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Test bucket access
        bucket_name = 'zugacloud'
        logger.info(f"Testing access to bucket: {bucket_name}")
        
        # Try to list objects (limited to 1 to minimize data transfer)
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=1
        )
        
        logger.info("✅ Successfully connected to Storj!")
        logger.info("✅ Successfully accessed bucket!")
        
        # Show bucket contents
        if 'Contents' in response:
            logger.info(f"\nFound {response['KeyCount']} objects in bucket")
            for obj in response.get('Contents', []):
                logger.info(f"- {obj['Key']} ({obj['Size']} bytes)")
        else:
            logger.info("\nBucket is empty and ready for use!")
            
        # Test write permission with a small test file
        logger.info("\nTesting write permission...")
        test_content = "Storj test file"
        s3_client.put_object(
            Bucket=bucket_name,
            Key='test.txt',
            Body=test_content
        )
        logger.info("✅ Successfully tested write permission!")
        
        # Clean up test file
        s3_client.delete_object(
            Bucket=bucket_name,
            Key='test.txt'
        )
        logger.info("✅ Successfully cleaned up test file!")
        
        logger.info("\n🎉 Storj setup is complete and working perfectly!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing Storj connection: {str(e)}")
        return False

if __name__ == '__main__':
    test_storj_connection() 