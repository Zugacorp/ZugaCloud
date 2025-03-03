from flask import Flask
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv
from ..auth import auth_bp

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Set the secret key from environment or generate a secure one
    app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)
    
    # Enable CORS
    CORS(app, supports_credentials=True)

    # Configure Cognito settings
    try:
        # Log all environment variables for debugging
        logger.info("Environment Variables:")
        logger.info(f"AWS_REGION: {os.environ.get('AWS_REGION')}")
        logger.info(f"COGNITO_USER_POOL_ID: {os.environ.get('COGNITO_USER_POOL_ID')}")
        logger.info(f"COGNITO_CLIENT_ID: {os.environ.get('COGNITO_CLIENT_ID')}")
        logger.info(f"COGNITO_CLIENT_SECRET: {bool(os.environ.get('COGNITO_CLIENT_SECRET'))}")

        # Verify required environment variables
        required_vars = [
            'AWS_REGION',
            'COGNITO_USER_POOL_ID',
            'COGNITO_CLIENT_ID',
            'COGNITO_CLIENT_SECRET',
            'COGNITO_DOMAIN'
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        logger.info("Successfully configured Cognito settings")
        
    except Exception as e:
        logger.error(f"Failed to configure Cognito: {str(e)}")
        raise

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app
