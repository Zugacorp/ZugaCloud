# File: backend/config_manager.py

import os
import json
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__), 'config')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.ensure_config_directory()

    def ensure_config_directory(self):
        """Ensure config directory exists"""
        os.makedirs(self.config_dir, exist_ok=True)

    def get_credentials_from_env(self):
        """Get AWS credentials from environment variables"""
        return {
            'aws_access_key': os.environ.get('AWS_ACCESS_KEY'),
            'aws_secret_key': os.environ.get('AWS_SECRET_KEY'),
            'region': os.environ.get('AWS_DEFAULT_REGION', 'us-east-2')
        }

    def load_config(self):
        """Load configuration from file or environment"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

            # Check environment variables
            env_credentials = self.get_credentials_from_env()
            
            # Use environment variables if they exist, otherwise keep file values
            if env_credentials['aws_access_key'] and env_credentials['aws_secret_key']:
                config.update(env_credentials)
                logger.info("Using AWS credentials from environment variables")
            
            # Set defaults if neither exists
            if not config.get('aws_access_key') and not config.get('aws_secret_key'):
                config.update({
                    'aws_access_key': '',
                    'aws_secret_key': '',
                    'region': 'us-east-2',
                    'bucket_name': 'zugaarchive',
                    'refresh_frequency': 300
                })
                logger.warning("No AWS credentials found in environment or config file")
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise

    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Configuration saved.")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise

    def update_config(self, key, value):
        config = self.load_config()
        config[key] = value
        self.save_config(config)
        logger.info(f"Configuration updated: {key} = {value}")

    def get_config_value(self, key, default=None):
        config = self.load_config()
        return config.get(key, default)

# Create a singleton instance
config_manager = ConfigManager()

# Export the instance