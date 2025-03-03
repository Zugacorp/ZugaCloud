"""
ZugaCloud Backend Package
"""

from flask import Flask
from flask_cors import CORS
from .auth import auth_bp, init_auth
from .api.routes import api_bp  # Import the API blueprint
import logging

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    try:
        app = Flask(__name__)
        CORS(app)
        
        # Initialize authentication
        oauth = init_auth(app)
        
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(api_bp, url_prefix='/api')  # Register the API blueprint
        
        return app
        
    except Exception as e:
        logger.error(f"Failed to create app: {str(e)}")
        raise
