import boto3
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_admin_clients():
    """Delete admin clients from the Cognito user pool"""
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
        
        # List all clients
        logger.info("\nListing app clients:")
        response = client.list_user_pool_clients(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
            MaxResults=10
        )
        
        # Delete admin clients
        admin_clients_found = False
        for app_client in response.get('UserPoolClients', []):
            if app_client['ClientName'] == 'zugacloud-admin':
                admin_clients_found = True
                client_id = app_client['ClientId']
                logger.info(f"\nDeleting admin client: {client_id}")
                
                try:
                    client.delete_user_pool_client(
                        UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                        ClientId=client_id
                    )
                    logger.info(f"Successfully deleted client {client_id}")
                except ClientError as e:
                    logger.error(f"Failed to delete client {client_id}: {str(e)}")
        
        if not admin_clients_found:
            logger.info("\nNo admin clients found to delete")
        
        logger.info("\nCleanup complete!")
        return True
        
    except ClientError as e:
        logger.error(f"AWS Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error deleting admin clients: {str(e)}")
        return False

if __name__ == '__main__':
    delete_admin_clients() 