#!/usr/bin/env python3
"""
Utility script to check if Storj credentials are properly configured
in the environment variables.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("check-storj-env")

def main():
    """Check Storj environment variables"""
    try:
        # Find the backend .env file
        root_dir = Path(__file__).parent.parent.parent  # Go up to project root
        backend_env = root_dir / 'backend' / '.env'
        
        if not backend_env.exists():
            logger.error(f"Backend .env file not found at {backend_env}")
            logger.info("Checking for .env file in project root...")
            
            root_env = root_dir / '.env'
            if root_env.exists():
                logger.info(f"Found .env file in project root: {root_env}")
                load_dotenv(root_env)
            else:
                logger.error("No .env file found.")
        else:
            logger.info(f"Found backend .env file: {backend_env}")
            load_dotenv(backend_env)
        
        # Check Storj environment variables
        logger.info("\n=== Checking Storj Environment Variables ===")
        
        # Primary Storj variables
        storj_access_key = os.environ.get('STORJ_ACCESS_KEY')
        storj_secret_key = os.environ.get('STORJ_SECRET_KEY')
        storj_endpoint = os.environ.get('STORJ_ENDPOINT')
        
        # Fallback to AWS variables if Storj ones aren't set
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        # Check which variables are set
        logger.info(f"STORJ_ACCESS_KEY: {'✓ Set' if storj_access_key else '✗ Not set'}")
        logger.info(f"STORJ_SECRET_KEY: {'✓ Set' if storj_secret_key else '✗ Not set'}")
        logger.info(f"STORJ_ENDPOINT: {'✓ Set' if storj_endpoint else '✗ Not set (will use default)'}")
        
        logger.info(f"AWS_ACCESS_KEY_ID: {'✓ Set' if aws_access_key else '✗ Not set'}")
        logger.info(f"AWS_SECRET_ACCESS_KEY: {'✓ Set' if aws_secret_key else '✗ Not set'}")
        
        # Effective credentials (what would be used by the application)
        effective_access_key = storj_access_key or aws_access_key
        effective_secret_key = storj_secret_key or aws_secret_key
        effective_endpoint = storj_endpoint or 'https://gateway.eu1.storjshare.io'
        
        logger.info("\n=== Effective Storj Credentials ===")
        logger.info(f"Access Key: {'✓ Available' if effective_access_key else '✗ Missing'}")
        if effective_access_key:
            # Show first and last few characters for verification
            visible_part = effective_access_key[:4] + '...' + effective_access_key[-4:] if len(effective_access_key) > 8 else effective_access_key
            logger.info(f"  Value: {visible_part}")
            
        logger.info(f"Secret Key: {'✓ Available' if effective_secret_key else '✗ Missing'}")
        if effective_secret_key:
            logger.info(f"  Length: {len(effective_secret_key)} characters")
            
        logger.info(f"Endpoint: {effective_endpoint}")
        
        # Summary
        logger.info("\n=== Summary ===")
        if effective_access_key and effective_secret_key:
            logger.info("✓ Storj credentials are available")
            
            # Check config file
            config_path = root_dir / 'backend' / 'aws' / 'config' / 'config.json'
            if config_path.exists():
                logger.info(f"✓ Config file exists at {config_path}")
                
                # TODO: Consider reading and checking the config file content here
                # This would require importing json and parsing the file
                
            else:
                logger.error(f"✗ Config file not found at {config_path}")
                logger.info("Make sure to create a config file with 'storage_provider': 'storj'")
        else:
            logger.error("✗ Storj credentials are incomplete or missing")
            logger.info("Please set STORJ_ACCESS_KEY and STORJ_SECRET_KEY environment variables")
            logger.info("Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as fallbacks")
            
    except Exception as e:
        logger.error(f"Error checking Storj environment: {e}")
        return False
        
    return True

if __name__ == "__main__":
    if main():
        logger.info("Environment check completed successfully")
    else:
        logger.error("Environment check failed")
        sys.exit(1) 