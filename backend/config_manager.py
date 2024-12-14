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
        """Ensure config directory exists and is writable"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            # Test if directory is writable
            test_file = os.path.join(self.config_dir, '.test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                logger.error(f"Config directory is not writable: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error ensuring config directory: {str(e)}")
            raise

    def get_credentials_from_env(self):
        """Get AWS credentials from environment variables"""
        access_key = os.environ.get('AWS_ACCESS_KEY')
        secret_key = os.environ.get('AWS_SECRET_KEY')
        region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-2')
        
        # Check if environment variables are actually set
        if access_key and secret_key:
            return {
                'aws_access_key': access_key,
                'aws_secret_key': secret_key,
                'region': region,
                'prefer_env_vars': True
            }
        return None

    def load_config(self):
        """Load config from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {}

            # Always set prefer_env_vars to True by default if not specified
            if 'prefer_env_vars' not in config:
                config['prefer_env_vars'] = True
                self.save_config(config)

            return config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}

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