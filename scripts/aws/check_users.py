import boto3
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_cognito_users():
    """List all users in the Cognito user pool"""
    try:
        # Find and load the correct .env file
        current_dir = Path(__file__).parent  # Get the directory containing this script
        project_root = current_dir.parent.parent  # Go up two levels to project root
        backend_env = project_root / 'backend' / '.env.backend'
        
        logger.info(f"\nLooking for .env.backend at: {backend_env}")
        
        if not backend_env.exists():
            raise EnvironmentError(f"Backend .env file not found at {backend_env}!")
            
        load_dotenv(backend_env)
        
        # Verify required environment variables
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'COGNITO_USER_POOL_ID'
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Create Cognito client
        client = boto3.client('cognito-idp',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        
        # List users
        logger.info("\nListing users in Cognito pool:")
        logger.info(f"User Pool ID: {os.environ.get('COGNITO_USER_POOL_ID')}")
        
        response = client.list_users(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID')
        )
        
        users = response.get('Users', [])
        logger.info(f"\nFound {len(users)} users:")
        
        for user in users:
            logger.info(f"\nUsername: {user.get('Username')}")
            logger.info(f"Status: {user.get('UserStatus')}")
            logger.info("Attributes:")
            for attr in user.get('Attributes', []):
                # Don't log sensitive information
                if attr.get('Name') not in ['password', 'email_verified']:
                    logger.info(f"  {attr.get('Name')}: {attr.get('Value')}")
            
            # Get additional user details
            try:
                user_details = client.admin_get_user(
                    UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                    Username=user.get('Username')
                )
                logger.info(f"Created: {user_details.get('UserCreateDate')}")
                logger.info(f"Last Modified: {user_details.get('UserLastModifiedDate')}")
                logger.info(f"Enabled: {user_details.get('Enabled', True)}")
                
            except ClientError as e:
                logger.warning(f"Could not get detailed information for user {user.get('Username')}: {str(e)}")
        
        return True
        
    except ClientError as e:
        logger.error(f"AWS Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return False

if __name__ == '__main__':
    list_cognito_users() 