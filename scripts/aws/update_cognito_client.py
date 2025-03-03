import boto3
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the backend env path
BACKEND_ENV = None

def load_environment():
    """Load and validate environment variables"""
    try:
        global BACKEND_ENV
        # Find and load the correct .env file
        current_dir = Path(__file__).parent  # Get the directory containing this script
        project_root = current_dir.parent.parent  # Go up two levels to project root
        BACKEND_ENV = project_root / 'backend' / '.env.backend'
        
        logger.info(f"\nLooking for .env.backend at: {BACKEND_ENV}")
        
        if not BACKEND_ENV.exists():
            raise EnvironmentError(f"Backend .env file not found at {BACKEND_ENV}!")
            
        load_dotenv(BACKEND_ENV)
        
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
            
        return True
        
    except Exception as e:
        logger.error(f"Environment setup failed: {str(e)}")
        return False

def create_app_client():
    """Create a new app client with proper configuration"""
    try:
        if not load_environment():
            return False
            
        logger.info("\n=== Creating New App Client ===")
        
        # Create Cognito client
        client = boto3.client('cognito-idp',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        
        # Create new app client with proper configuration
        response = client.create_user_pool_client(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
            ClientName='zugacloud-client',
            GenerateSecret=True,
            ExplicitAuthFlows=[
                'ALLOW_USER_PASSWORD_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH'
            ],
            PreventUserExistenceErrors='ENABLED',
            EnableTokenRevocation=True,
            AllowedOAuthFlows=['code'],
            AllowedOAuthFlowsUserPoolClient=True,
            AllowedOAuthScopes=[
                'email',
                'openid',
                'profile'
            ],
            CallbackURLs=[
                'http://localhost:3001/auth/callback'
            ],
            LogoutURLs=[
                'http://localhost:3001'
            ],
            SupportedIdentityProviders=['COGNITO'],
            AccessTokenValidity=24,
            IdTokenValidity=24,
            RefreshTokenValidity=30,
            TokenValidityUnits={
                'AccessToken': 'hours',
                'IdToken': 'hours',
                'RefreshToken': 'days'
            }
        )
        
        # Get the new client details
        client_config = response.get('UserPoolClient', {})
        
        # Update .env with new client details
        try:
            with open(BACKEND_ENV, 'r') as f:
                lines = f.readlines()
            
            updated_lines = []
            client_id_updated = False
            client_secret_updated = False
            vite_client_id_updated = False
            
            for line in lines:
                if line.startswith('COGNITO_CLIENT_ID='):
                    updated_lines.append(f"COGNITO_CLIENT_ID={client_config.get('ClientId')}\n")
                    client_id_updated = True
                elif line.startswith('COGNITO_CLIENT_SECRET='):
                    updated_lines.append(f"COGNITO_CLIENT_SECRET={client_config.get('ClientSecret')}\n")
                    client_secret_updated = True
                elif line.startswith('VITE_COGNITO_CLIENT_ID='):
                    updated_lines.append(f"VITE_COGNITO_CLIENT_ID={client_config.get('ClientId')}\n")
                    vite_client_id_updated = True
                else:
                    updated_lines.append(line)
            
            # Add any missing variables
            if not client_id_updated:
                updated_lines.append(f"COGNITO_CLIENT_ID={client_config.get('ClientId')}\n")
            if not client_secret_updated:
                updated_lines.append(f"COGNITO_CLIENT_SECRET={client_config.get('ClientSecret')}\n")
            if not vite_client_id_updated:
                updated_lines.append(f"VITE_COGNITO_CLIENT_ID={client_config.get('ClientId')}\n")
            
            with open(BACKEND_ENV, 'w') as f:
                f.writelines(updated_lines)
            
            logger.info("\nApp client created successfully!")
            logger.info(f"Client ID: {client_config.get('ClientId')}")
            logger.info("Client Secret: [Generated and saved to .env.backend]")
            logger.info(f"Auth Flows: {client_config.get('ExplicitAuthFlows', [])}")
            logger.info(f"OAuth Scopes: {client_config.get('AllowedOAuthScopes', [])}")
            logger.info(f"Callback URLs: {client_config.get('CallbackURLs', [])}")
            
            return client_config.get('ClientId')
            
        except Exception as e:
            logger.error(f"Failed to update .env file: {str(e)}")
            return False
            
    except ClientError as e:
        logger.error(f"AWS Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error creating app client: {str(e)}")
        return False

def create_admin_client():
    """Create a new app client specifically for admin operations"""
    try:
        if not load_environment():
            return False
            
        logger.info("\n=== Creating Admin App Client ===")
        
        # Create Cognito client
        client = boto3.client('cognito-idp',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        
        # Create new app client
        response = client.create_user_pool_client(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
            ClientName='zugacloud-admin',
            GenerateSecret=False,  # No client secret for admin operations
            ExplicitAuthFlows=[
                'ALLOW_ADMIN_USER_PASSWORD_AUTH',  # Allow admin auth
                'ALLOW_REFRESH_TOKEN_AUTH'  # Allow refresh tokens
            ],
            PreventUserExistenceErrors='ENABLED',
            EnableTokenRevocation=True
        )
        
        client_config = response.get('UserPoolClient', {})
        logger.info("\nAdmin Client Created Successfully!")
        logger.info(f"Client ID: {client_config.get('ClientId')}")
        logger.info(f"Auth Flows: {client_config.get('ExplicitAuthFlows', [])}")
        
        # Save the new client ID to a separate .env file for admin operations
        admin_env_file = BACKEND_ENV.parent / '.env.backend.admin'
        try:
            with open(admin_env_file, 'w') as f:
                f.write(f"COGNITO_ADMIN_CLIENT_ID={client_config.get('ClientId')}\n")
            
            logger.info(f"\nAdmin client ID saved to {admin_env_file}")
            logger.info("=== Admin Client Creation Complete ===\n")
            
            return client_config.get('ClientId')
            
        except Exception as e:
            logger.error(f"Failed to create admin environment file: {str(e)}")
            return False
        
    except ClientError as e:
        logger.error(f"AWS Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error creating admin client: {str(e)}")
        return False

if __name__ == '__main__':
    create_app_client()
    create_admin_client() 