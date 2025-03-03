import boto3
import os
from dotenv import load_dotenv
import logging
from botocore.exceptions import ClientError
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if all required environment variables are set"""
    try:
        # Find and load the correct .env file
        current_dir = Path(__file__).parent  # Get the directory containing this test file
        project_root = current_dir.parent.parent  # Go up two levels to project root
        backend_env = project_root / 'backend' / '.env.backend'
        
        logger.info(f"Looking for .env.backend at: {backend_env}")
        
        if not backend_env.exists():
            raise EnvironmentError(f"Backend .env file not found at {backend_env}!")
            
        load_dotenv(backend_env)
        
        # Check required environment variables
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'COGNITO_USER_POOL_ID',
            'COGNITO_CLIENT_ID',
            'COGNITO_CLIENT_SECRET'
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
        # Log configuration (without sensitive data)
        logger.info("\n=== AWS Configuration ===")
        logger.info(f"Region: {os.environ.get('AWS_REGION')}")
        logger.info(f"Access Key ID: {os.environ.get('AWS_ACCESS_KEY_ID')}")
        logger.info(f"Secret Key Length: {len(os.environ.get('AWS_SECRET_ACCESS_KEY', ''))}")
        logger.info(f"User Pool ID: {os.environ.get('COGNITO_USER_POOL_ID')}")
        logger.info(f"Client ID: {os.environ.get('COGNITO_CLIENT_ID')}")
        logger.info(f"Client Secret Length: {len(os.environ.get('COGNITO_CLIENT_SECRET', ''))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Environment check failed: {str(e)}")
        return False

def test_aws_connection():
    """Test AWS connection using boto3"""
    try:
        # Create session with explicit credentials
        session = boto3.Session(
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        
        # Test Cognito connection
        cognito = session.client('cognito-idp')
        response = cognito.list_user_pools(MaxResults=10)
        logger.info(f"Successfully connected to Cognito. Found {len(response['UserPools'])} user pools.")
        
        # Test specific user pool access
        user_pool = cognito.describe_user_pool(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID')
        )
        logger.info(f"Successfully accessed user pool: {user_pool['UserPool']['Name']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to AWS: {str(e)}")
        return False

def test_aws_credentials():
    """Main test function for AWS credentials"""
    try:
        logger.info("\n=== Starting AWS Credentials Test ===")
        
        # Step 1: Check environment variables
        if not check_environment_variables():
            logger.error("Environment variable check failed!")
            return False
            
        # Step 2: Test AWS connection
        if not test_aws_connection():
            logger.error("AWS connection test failed!")
            return False
            
        logger.info("\n=== AWS Credentials Test Completed Successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"\n=== AWS Credentials Test Failed ===")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error message: {str(e)}")
        return False

if __name__ == "__main__":
    test_aws_credentials() 