import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_bunny():
    """Setup Bunny CDN configuration"""
    try:
        # Get the project root directory
        current_dir = Path(__file__).parent  # Get the directory containing this script
        project_root = current_dir.parent.parent  # Go up two levels to project root
        config_path = project_root / 'backend' / 'config' / 'config.json'
        
        logger.info("\n=== Bunny CDN Setup ===")
        logger.info("This script will help you configure Bunny CDN as your storage provider")
        
        # Load existing config if it exists
        config = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # Update config for Bunny CDN
        config['storage_provider'] = 'bunny'
        
        # Get Bunny CDN credentials from user
        print("\nPlease enter your Bunny CDN credentials:")
        api_key = input("Storage Zone API Key: ").strip()
        storage_zone = input("Storage Zone Name: ").strip()
        
        # Get region (with default)
        region = input("Storage Zone Region [Enter for default: de]: ").strip()
        if not region:
            region = "de"
            
        # Get sync folder
        sync_folder = input("Local Sync Folder Path [Enter for none]: ").strip()
        
        # Update config
        config.update({
            'bunny_api_key': api_key,
            'bunny_storage_zone': storage_zone,
            'bunny_region': region,
            'prefer_env_vars': False  # We're using config file
        })
        
        if sync_folder:
            config['sync_folder'] = sync_folder
            
        # Create config directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        # Create .env.backend with Bunny CDN environment variables
        env_path = project_root / 'backend' / '.env.backend'
        env_vars = [
            f"BUNNY_API_KEY={api_key}",
            f"BUNNY_STORAGE_ZONE={storage_zone}",
            f"BUNNY_REGION={region}",
            "STORAGE_PROVIDER=bunny"
        ]
        
        with open(env_path, 'w') as f:
            f.write('\n'.join(env_vars))
            
        logger.info("\nBunny CDN configuration completed successfully!")
        logger.info(f"Config saved to: {config_path}")
        logger.info(f"Environment variables saved to: {env_path}")
        logger.info("\nNext steps:")
        logger.info("1. Restart your application")
        logger.info("2. Your files will now be stored in Bunny CDN")
        logger.info("3. Use the sync functionality to upload existing files")
        logger.info("\nBenefits of Bunny CDN:")
        logger.info("- Global CDN distribution")
        logger.info("- Lower latency for video streaming")
        logger.info("- Better pricing for bandwidth")
        logger.info("- Built-in video optimization")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Bunny CDN: {str(e)}")
        return False

if __name__ == '__main__':
    setup_bunny() 