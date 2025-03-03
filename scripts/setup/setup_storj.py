import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_storj():
    """Setup Storj configuration"""
    try:
        # Get the project root directory
        current_dir = Path(__file__).parent  # Get the directory containing this script
        project_root = current_dir.parent.parent  # Go up two levels to project root
        config_path = project_root / 'backend' / 'config' / 'config.json'
        
        logger.info("\n=== Storj Setup ===")
        logger.info("This script will help you configure Storj as your storage provider")
        
        # Load existing config if it exists
        config = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # Update config for Storj
        config['storage_provider'] = 'storj'
        
        # Get Storj credentials from user
        print("\nPlease enter your Storj credentials:")
        access_key = input("Access Key: ").strip()
        secret_key = input("Secret Key: ").strip()
        bucket_name = input("Bucket Name: ").strip()
        
        # Get endpoint (with default)
        endpoint = input("Storj Gateway Endpoint [Enter for default: https://gateway.eu1.storjshare.io]: ").strip()
        if not endpoint:
            endpoint = "https://gateway.eu1.storjshare.io"
            
        # Get sync folder
        sync_folder = input("Local Sync Folder Path [Enter for none]: ").strip()
        
        # Update config
        config.update({
            'storj_access_key': access_key,
            'storj_secret_key': secret_key,
            'storj_endpoint': endpoint,
            'bucket_name': bucket_name,
            'prefer_env_vars': False  # We're using config file
        })
        
        if sync_folder:
            config['sync_folder'] = sync_folder
            
        # Create config directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        # Create .env.backend with Storj environment variables
        env_path = project_root / 'backend' / '.env.backend'
        env_vars = [
            f"STORJ_ACCESS_KEY={access_key}",
            f"STORJ_SECRET_KEY={secret_key}",
            f"STORJ_ENDPOINT={endpoint}",
            "STORAGE_PROVIDER=storj"
        ]
        
        with open(env_path, 'w') as f:
            f.write('\n'.join(env_vars))
            
        logger.info("\nStorj configuration completed successfully!")
        logger.info(f"Config saved to: {config_path}")
        logger.info(f"Environment variables saved to: {env_path}")
        logger.info("\nNext steps:")
        logger.info("1. Restart your application")
        logger.info("2. Your files will now be stored in Storj")
        logger.info("3. Use the sync functionality to upload existing files")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Storj: {str(e)}")
        return False

if __name__ == '__main__':
    setup_storj() 