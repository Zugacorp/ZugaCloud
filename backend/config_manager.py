# File: backend/config_manager.py

import os
import json
import logging
import sys

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_path='config/config.json'):
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the pyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        self.config_path = os.path.join(application_path, config_path)
        if not os.path.exists(os.path.dirname(self.config_path)):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        if not os.path.isfile(self.config_path):
            self.create_default_config()

    def create_default_config(self):
        default_config = {
            "aws_access_key": "",
            "aws_secret_key": "",
            "region": "us-east-2",
            "sync_folder": "",
            "bucket_name": "",
            "refresh_frequency": 300
        }
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        logger.info("Default configuration file created.")

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info("Configuration loaded.")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self.create_default_config()

    def save_config(self, config):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Configuration saved.")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def update_config(self, key, value):
        config = self.load_config()
        config[key] = value
        self.save_config(config)
        logger.info(f"Configuration updated: {key} = {value}")

    def get_config_value(self, key, default=None):
        config = self.load_config()
        return config.get(key, default)