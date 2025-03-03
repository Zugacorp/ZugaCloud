import boto3
import os
import logging
from dotenv import load_dotenv
import shutil
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_caches():
    """Clear all cache directories"""
    try:
        logger.info("\n=== Clearing Caches ===")
        
        # Clear frontend caches
        frontend_cache = Path('frontend/.vite')
        if frontend_cache.exists():
            shutil.rmtree(frontend_cache)
            logger.info("Cleared Vite cache")
            
        # Clear electron caches
        electron_cache = Path('frontend/dist')
        if electron_cache.exists():
            shutil.rmtree(electron_cache)
            logger.info("Cleared Electron build cache")
            
        # Clear Python cache directories
        for root, dirs, files in os.walk('.'):
            for dir in dirs:
                if dir == '__pycache__':
                    cache_dir = Path(root) / dir
                    shutil.rmtree(cache_dir)
                    logger.info(f"Cleared Python cache: {cache_dir}")
                    
        logger.info("Cache clearing complete!")
        
    except Exception as e:
        logger.error(f"Error clearing caches: {str(e)}")
        raise

def verify_env_variables():
    """Verify all environment variables are set correctly"""
    try:
        logger.info("\n=== Verifying Environment Variables ===")
        
        # Get the project root directory
        current_dir = Path(__file__).parent  # Get the directory containing this script
        project_root = current_dir.parent.parent  # Go up two levels to project root
        backend_env = project_root / 'backend' / '.env.backend'
        
        logger.info(f"Looking for .env.backend at: {backend_env}")
        
        if not backend_env.exists():
            raise EnvironmentError(f"Backend .env file not found at {backend_env}!")
            
        # Load environment variables
        load_dotenv(backend_env)
        
        # Required variables grouped by category
        required_vars = {
            'AWS Credentials': [
                'AWS_REGION',
                'AWS_ACCESS_KEY_ID',
                'AWS_SECRET_ACCESS_KEY'
            ],
            'Cognito Configuration': [
                'COGNITO_USER_POOL_ID',
                'COGNITO_CLIENT_ID',
                'COGNITO_CLIENT_SECRET',
                'COGNITO_DOMAIN'
            ],
            'Flask Configuration': [
                'FLASK_SECRET_KEY',
                'FLASK_ENV'
            ],
            'URLs and Redirects': [
                'FRONTEND_URL',
                'REDIRECT_SIGN_IN',
                'REDIRECT_SIGN_OUT'
            ]
        }
        
        # Check each category of variables
        missing_vars = []
        logger.info("\nChecking environment variables by category:")
        
        for category, vars in required_vars.items():
            logger.info(f"\n{category}:")
            for var in vars:
                value = os.environ.get(var)
                if not value:
                    missing_vars.append(var)
                    logger.warning(f"  {var}: Missing")
                else:
                    # Log variable presence (without exposing sensitive values)
                    if any(secret in var.upper() for secret in ['SECRET', 'KEY', 'PASSWORD', 'ACCESS']):
                        logger.info(f"  {var}: [Set - {len(value)} chars]")
                    else:
                        logger.info(f"  {var}: {value}")
                        
                        # Validate URL formats
                        if var.endswith('_URL') or var.startswith('REDIRECT_'):
                            if not value.startswith(('http://', 'https://')):
                                logger.warning(f"  Warning: {var} should start with http:// or https://")
                        
                        # Validate Cognito domain format
                        if var == 'COGNITO_DOMAIN' and not value.endswith('.amazoncognito.com'):
                            logger.warning(f"  Warning: {var} should end with .amazoncognito.com")
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        # Verify URL consistency
        frontend_url = os.environ.get('FRONTEND_URL', '').rstrip('/')
        redirect_sign_in = os.environ.get('REDIRECT_SIGN_IN', '')
        redirect_sign_out = os.environ.get('REDIRECT_SIGN_OUT', '')
        
        if frontend_url:
            if not redirect_sign_in.startswith(frontend_url):
                logger.warning(f"REDIRECT_SIGN_IN should start with FRONTEND_URL")
            if not redirect_sign_out.startswith(frontend_url):
                logger.warning(f"REDIRECT_SIGN_OUT should start with FRONTEND_URL")
            
        logger.info("\nAll environment variables verified!")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying environment variables: {str(e)}")
        raise

def verify_cognito_client():
    """Verify Cognito client configuration"""
    try:
        logger.info("\n=== Verifying Cognito Client ===")
        
        # Create Cognito client
        client = boto3.client('cognito-idp',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        
        # Check user pool
        user_pool = client.describe_user_pool(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID')
        )
        logger.info(f"User Pool Name: {user_pool['UserPool']['Name']}")
        
        # Check app client
        client_id = os.environ.get('COGNITO_CLIENT_ID')
        client_details = client.describe_user_pool_client(
            UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
            ClientId=client_id
        )
        
        client_config = client_details['UserPoolClient']
        logger.info(f"Client Name: {client_config['ClientName']}")
        logger.info(f"Client ID: {client_config['ClientId']}")
        logger.info(f"Auth Flows: {client_config.get('ExplicitAuthFlows', [])}")
        
        # Verify the client matches our .env file
        if client_config['ClientId'] != os.environ.get('COGNITO_CLIENT_ID'):
            raise ValueError("Client ID mismatch between Cognito and .env file")
            
        logger.info("Cognito client verified!")
        
    except Exception as e:
        logger.error(f"Error verifying Cognito client: {str(e)}")
        raise

def verify_frontend_config():
    """Verify frontend configuration matches backend"""
    try:
        logger.info("\n=== Verifying Frontend Configuration ===")
        
        # Load frontend .env
        frontend_env = {}
        env_path = Path('frontend/.env.frontend')
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        frontend_env[key] = value
        
        # Check required variables
        required_mappings = {
            'VITE_COGNITO_USER_POOL_ID': 'COGNITO_USER_POOL_ID',
            'VITE_COGNITO_CLIENT_ID': 'COGNITO_CLIENT_ID',
            'VITE_AWS_REGION': 'AWS_REGION',
            'VITE_COGNITO_DOMAIN': 'COGNITO_DOMAIN'
        }
        
        updates_needed = False
        for frontend_key, backend_key in required_mappings.items():
            frontend_value = frontend_env.get(frontend_key, '').strip('"')
            backend_value = os.environ.get(backend_key, '')
            
            if frontend_value != backend_value:
                updates_needed = True
                logger.warning(f"Mismatch in {frontend_key}:")
                logger.warning(f"  Frontend: {frontend_value}")
                logger.warning(f"  Backend:  {backend_value}")
                frontend_env[frontend_key] = backend_value
        
        if updates_needed:
            logger.info("Updating frontend configuration...")
            with open(env_path, 'w') as f:
                for key, value in frontend_env.items():
                    f.write(f"{key}={value}\n")
            logger.info("Frontend configuration updated!")
        else:
            logger.info("Frontend configuration is in sync!")
            
    except Exception as e:
        logger.error(f"Error verifying frontend configuration: {str(e)}")
        raise

def run_startup_checks():
    """Run all startup checks"""
    try:
        logger.info("\n=== Running Startup Checks ===")
        
        # Run all checks
        clear_caches()
        verify_env_variables()
        verify_cognito_client()
        verify_frontend_config()
        
        logger.info("\n=== All Startup Checks Passed! ===")
        return True
        
    except Exception as e:
        logger.error(f"\n=== Startup Checks Failed! ===")
        logger.error(str(e))
        return False

if __name__ == '__main__':
    run_startup_checks() 