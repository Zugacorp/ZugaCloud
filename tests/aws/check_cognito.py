import boto3
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_cognito_config():
    """Check and validate Cognito configuration"""
    try:
        # Find and load the correct .env file
        current_dir = Path(__file__).parent  # Get the directory containing this test file
        project_root = current_dir.parent.parent  # Go up two levels to project root
        backend_env = project_root / 'backend' / '.env'
        
        logger.info(f"\nLooking for .env at: {backend_env}")
        
        if not backend_env.exists():
            raise EnvironmentError(f"Backend .env file not found at {backend_env}!")
            
        load_dotenv(backend_env)
        
        # Verify required environment variables
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'COGNITO_USER_POOL_ID',
            'COGNITO_CLIENT_ID'
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Print current environment settings
        logger.info("\nCurrent Environment Settings:")
        logger.info(f"Region: {os.environ.get('AWS_REGION')}")
        logger.info(f"User Pool ID: {os.environ.get('COGNITO_USER_POOL_ID')}")
        logger.info(f"Client ID: {os.environ.get('COGNITO_CLIENT_ID')}")
        
        # Create Cognito client with explicit credentials
        client = boto3.client('cognito-idp',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        
        # Get user pool details
        logger.info("\nChecking User Pool Configuration:")
        user_pool = client.describe_user_pool(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID')
        )
        user_pool_details = user_pool.get('UserPool', {})
        
        logger.info(f"User Pool Name: {user_pool_details.get('Name', 'N/A')}")
        logger.info(f"Creation Date: {user_pool_details.get('CreationDate', 'N/A')}")
        logger.info(f"MFA Configuration: {user_pool_details.get('MfaConfiguration', 'OFF')}")
        logger.info(f"Schema Attributes: {len(user_pool_details.get('SchemaAttributes', []))}")
        logger.info(f"Estimated Number of Users: {user_pool_details.get('EstimatedNumberOfUsers', 'N/A')}")
        
        # List and check app clients
        logger.info("\nChecking App Clients:")
        response = client.list_user_pool_clients(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
            MaxResults=10
        )
        
        found_configured_client = False
        for app_client in response.get('UserPoolClients', []):
            logger.info(f"\nClient Name: {app_client.get('ClientName', 'N/A')}")
            logger.info(f"Client ID: {app_client.get('ClientId', 'N/A')}")
            
            if app_client.get('ClientId') == os.environ.get('COGNITO_CLIENT_ID'):
                found_configured_client = True
                try:
                    # Get detailed client configuration
                    client_details = client.describe_user_pool_client(
                        UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                        ClientId=app_client.get('ClientId')
                    )
                    client_config = client_details.get('UserPoolClient', {})
                    
                    logger.info("\nConfigured Client Details:")
                    logger.info("Auth Flows:")
                    for flow in client_config.get('ExplicitAuthFlows', []):
                        logger.info(f"  - {flow}")
                    
                    logger.info("\nOAuth Configuration:")
                    logger.info(f"OAuth Flows: {client_config.get('AllowedOAuthFlows', [])}")
                    logger.info(f"OAuth Scopes: {client_config.get('AllowedOAuthScopes', [])}")
                    logger.info(f"Callback URLs: {client_config.get('CallbackURLs', [])}")
                    logger.info(f"Logout URLs: {client_config.get('LogoutURLs', [])}")
                    
                    logger.info("\nSecurity Configuration:")
                    logger.info(f"Prevent User Existence Errors: {client_config.get('PreventUserExistenceErrors', 'N/A')}")
                    logger.info(f"Enable Token Revocation: {client_config.get('EnableTokenRevocation', 'N/A')}")
                    logger.info(f"Token Validity (Access Token): {client_config.get('AccessTokenValidity', 'N/A')} {client_config.get('TokenValidityUnits', {}).get('AccessToken', 'hours')}")
                    logger.info(f"Token Validity (ID Token): {client_config.get('IdTokenValidity', 'N/A')} {client_config.get('TokenValidityUnits', {}).get('IdToken', 'hours')}")
                    logger.info(f"Token Validity (Refresh Token): {client_config.get('RefreshTokenValidity', 'N/A')} {client_config.get('TokenValidityUnits', {}).get('RefreshToken', 'days')}")
                    
                except ClientError as e:
                    logger.error(f"Error getting client details: {str(e)}")
        
        if not found_configured_client:
            raise ValueError(f"Configured client ID {os.environ.get('COGNITO_CLIENT_ID')} not found in user pool")
        
        # Check domain configuration
        logger.info("\nChecking Domain Configuration:")
        try:
            domain_info = client.describe_user_pool_domain(
                Domain=os.environ.get('COGNITO_DOMAIN').split('.')[0]
            )
            domain_desc = domain_info.get('DomainDescription', {})
            logger.info(f"Domain Status: {domain_desc.get('Status', 'UNKNOWN')}")
            logger.info(f"CloudFront Distribution: {domain_desc.get('CloudFrontDistribution', 'N/A')}")
            logger.info(f"Domain: {domain_desc.get('Domain', 'N/A')}")
        except ClientError as e:
            logger.warning(f"Could not check domain configuration: {str(e)}")
        
        # Check IAM permissions
        logger.info("\nChecking IAM Permissions:")
        try:
            iam = boto3.client('iam',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_REGION')
            )
            
            # Get current user
            user = iam.get_user()
            user_info = user.get('User', {})
            logger.info(f"\nIAM User: {user_info.get('UserName', 'N/A')}")
            logger.info(f"User ARN: {user_info.get('Arn', 'N/A')}")
            
            # List user policies
            policies = iam.list_attached_user_policies(
                UserName=user_info.get('UserName')
            )
            
            logger.info("\nAttached Policies:")
            for policy in policies.get('AttachedPolicies', []):
                logger.info(f"  - {policy.get('PolicyName', 'N/A')}")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                logger.warning("Limited IAM permissions - this is normal for restricted users")
            else:
                logger.error(f"Error checking IAM permissions: {str(e)}")
        
        logger.info("\nCognito configuration check completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error checking Cognito config: {str(e)}")
        raise

if __name__ == '__main__':
    check_cognito_config() 