from flask import Blueprint, jsonify, request, redirect, url_for, session, Flask
import os
import requests
import logging
import boto3
import botocore
from botocore.config import Config
import hmac
import hashlib
import base64
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from pathlib import Path
from functools import wraps

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

def init_auth(app):
    """Initialize authentication with AWS Cognito"""
    try:
        # Load environment variables from .env in backend root
        current_dir = Path(__file__).parent.parent
        backend_env = current_dir / '.env'
        
        logger.info(f"Loading environment from: {backend_env}")
        
        if not backend_env.exists():
            raise ValueError(f"Environment file not found at {backend_env}")
            
        load_dotenv(backend_env)
        
        # Required environment variables
        required_vars = [
            'FLASK_SECRET_KEY',
            'COGNITO_DOMAIN',
            'COGNITO_CLIENT_ID',
            'COGNITO_CLIENT_SECRET',
            'AWS_REGION',
            'COGNITO_USER_POOL_ID',
            'COGNITO_IDENTITY_POOL_ID'
        ]
        
        # Verify all required variables are present
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Use environment variables with no fallbacks to ensure proper configuration
        app.secret_key = os.environ['FLASK_SECRET_KEY']
        oauth = OAuth(app)
        
        # Get Cognito configuration from environment
        COGNITO_DOMAIN = os.environ['COGNITO_DOMAIN']
        COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
        COGNITO_CLIENT_SECRET = os.environ['COGNITO_CLIENT_SECRET']
        COGNITO_IDENTITY_POOL_ID = os.environ['COGNITO_IDENTITY_POOL_ID']
        
        logger.info("Configuring OAuth with Cognito...")
        logger.info(f"Domain: {COGNITO_DOMAIN}")
        logger.info(f"Client ID: {COGNITO_CLIENT_ID}")
        logger.info("Client Secret: [Set]")
        logger.info(f"Identity Pool ID: {COGNITO_IDENTITY_POOL_ID}")

        # Configure AWS Cognito OAuth
        oauth.register(
            name='cognito',
            server_metadata_url=f'https://{COGNITO_DOMAIN}/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'phone openid email'
            },
            client_id=COGNITO_CLIENT_ID,
            client_secret=COGNITO_CLIENT_SECRET
        )
        
        # Initialize identity pool client
        identity_client = boto3.client('cognito-identity',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION')
        )
        
        # Verify identity pool exists
        try:
            identity_pool = identity_client.describe_identity_pool(
                IdentityPoolId=COGNITO_IDENTITY_POOL_ID
            )
            logger.info(f"Successfully verified identity pool: {identity_pool['IdentityPoolName']}")
        except Exception as e:
            logger.error(f"Failed to verify identity pool: {str(e)}")
            raise
        
        logger.info("OAuth configuration completed successfully")
        return oauth

    except Exception as e:
        logger.error(f"Failed to initialize authentication: {str(e)}")
        raise

def get_cognito_client():
    """Create a Cognito client with credentials"""
    try:
        # Create client with explicit configuration
        client = boto3.client('cognito-idp',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION'),
            config=Config(
                region_name=os.environ.get('AWS_REGION'),
                signature_version='v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
        )
        
        # Verify client by listing user pools
        client.list_user_pools(MaxResults=1)
        logger.info("Successfully created and verified Cognito client")
        
        return client
    except Exception as e:
        logger.error(f"Failed to create Cognito client: {str(e)}")
        raise

def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            logger.warning("Unauthorized access attempt")
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def calculate_secret_hash(username):
    """Calculate secret hash for Cognito authentication"""
    try:
        # Get client configuration
        client_id = os.environ.get('COGNITO_CLIENT_ID')
        client_secret = os.environ.get('COGNITO_CLIENT_SECRET')
        
        if not all([username, client_id, client_secret]):
            raise ValueError("Missing required credentials")
            
        # Clean inputs
        username = username.strip()
        client_id = client_id.strip()
        client_secret = client_secret.strip()
        
        # Create message string
        message = (username + client_id).encode('utf-8')
        key = client_secret.encode('utf-8')
        
        # Calculate HMAC SHA256
        dig = hmac.new(key, message, digestmod=hashlib.sha256).digest()
        
        # Base64 encode
        return base64.b64encode(dig).decode()
        
    except Exception as e:
        logger.error(f"Error calculating secret hash: {str(e)}")
        raise

# Route handlers
@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user in Cognito user pool"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Password validation
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        if not any(c.isupper() for c in password):
            return jsonify({'error': 'Password must contain uppercase letters'}), 400
        if not any(c.islower() for c in password):
            return jsonify({'error': 'Password must contain lowercase letters'}), 400
        if not any(c.isdigit() for c in password):
            return jsonify({'error': 'Password must contain numbers'}), 400
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return jsonify({'error': 'Password must contain special characters'}), 400

        # Get Cognito client
        client = get_cognito_client()
        
        try:
            # Check if user exists
            try:
                client.admin_get_user(
                    UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                    Username=email
                )
                return jsonify({'error': 'An account with this email already exists'}), 400
            except client.exceptions.UserNotFoundException:
                pass  # User doesn't exist, continue with creation
            
            # Create user
            create_response = client.admin_create_user(
                UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                Username=email,
                TemporaryPassword=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'}
                ],
                MessageAction='SUPPRESS'
            )
            
            # Set permanent password
            client.admin_set_user_password(
                UserPoolId=os.environ.get('COGNITO_USER_POOL_ID'),
                Username=email,
                Password=password,
                Permanent=True
            )
            
            user_details = create_response.get('User', {})
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'user': {
                    'email': email,
                    'id': next((attr['Value'] for attr in user_details.get('Attributes', []) 
                              if attr['Name'] == 'sub'), None),
                    'status': user_details.get('UserStatus', 'CONFIRMED')
                }
            })
            
        except client.exceptions.InvalidPasswordException as e:
            return jsonify({'error': str(e)}), 400
        except client.exceptions.UsernameExistsException:
            return jsonify({'error': 'An account with this email already exists'}), 400
        except client.exceptions.InvalidParameterException as e:
            return jsonify({'error': str(e)}), 400
        except client.exceptions.NotAuthorizedException:
            return jsonify({'error': 'Not authorized to perform this operation'}), 403
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return jsonify({'error': 'Failed to create account'}), 500
            
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login using Cognito user pool credentials"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
            
        # Create Cognito client
        client = get_cognito_client()
        
        # Calculate secret hash
        secret_hash = calculate_secret_hash(email)
        
        # Log the authentication attempt
        logger.info(f"Attempting login for user: {email}")
        
        try:
            # Initiate auth using USER_PASSWORD_AUTH flow
            auth_response = client.initiate_auth(
                ClientId=os.environ.get('COGNITO_CLIENT_ID'),
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password,
                    'SECRET_HASH': secret_hash
                }
            )
            
            # Get tokens from successful auth
            tokens = auth_response.get('AuthenticationResult', {})
            
            if not tokens:
                return jsonify({'error': 'Authentication failed'}), 401
            
            # Get temporary credentials from identity pool
            identity_client = boto3.client('cognito-identity',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_REGION')
            )
            
            # Get identity ID and credentials
            identity_response = identity_client.get_id(
                IdentityPoolId=os.environ.get('COGNITO_IDENTITY_POOL_ID'),
                Logins={
                    f"cognito-idp.{os.environ.get('AWS_REGION')}.amazonaws.com/{os.environ.get('COGNITO_USER_POOL_ID')}": tokens['IdToken']
                }
            )
            
            credentials_response = identity_client.get_credentials_for_identity(
                IdentityId=identity_response['IdentityId'],
                Logins={
                    f"cognito-idp.{os.environ.get('AWS_REGION')}.amazonaws.com/{os.environ.get('COGNITO_USER_POOL_ID')}": tokens['IdToken']
                }
            )
                
            # Store user info in session
            session['user'] = {
                'email': email,
                'access_token': tokens['AccessToken'],
                'identity_id': identity_response['IdentityId']
            }
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'tokens': {
                    'access_token': tokens['AccessToken'],
                    'id_token': tokens['IdToken'],
                    'refresh_token': tokens.get('RefreshToken')
                },
                'credentials': {
                    'identity_id': identity_response['IdentityId'],
                    'access_key_id': credentials_response['Credentials']['AccessKeyId'],
                    'secret_key': credentials_response['Credentials']['SecretKey'],
                    'session_token': credentials_response['Credentials']['SessionToken'],
                    'expiration': credentials_response['Credentials']['Expiration'].isoformat()
                },
                'user': {
                    'email': email
                }
            })
            
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['NotAuthorizedException', 'UserNotFoundException']:
                return jsonify({'error': 'Invalid email or password'}), 401
            raise
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/logout')
def logout():
    """Log out the current user"""
    session.pop('user', None)
    logger.info("User logged out")
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@auth_bp.route('/status', methods=['GET'])
def check_auth_status():
    """Check authentication status and return user info"""
    try:
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'isAuthenticated': False,
                'error': 'No valid authorization token'
            }), 401

        access_token = auth_header.split(' ')[1]
        
        try:
            # Create identity client
            identity_client = boto3.client('cognito-identity',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_REGION')
            )
            
            # Get identity ID using the access token
            identity_response = identity_client.get_id(
                IdentityPoolId=os.environ.get('COGNITO_IDENTITY_POOL_ID'),
                Logins={
                    f"cognito-idp.{os.environ.get('AWS_REGION')}.amazonaws.com/{os.environ.get('COGNITO_USER_POOL_ID')}": access_token
                }
            )
            
            # If we get here, the token is valid
            # Create Cognito client
            client = get_cognito_client()
            
            # Get user information using the access token
            user_info = client.get_user(
                AccessToken=access_token
            )
            
            # Extract user attributes
            user_attrs = {attr['Name']: attr['Value'] for attr in user_info['UserAttributes']}
            
            return jsonify({
                'isAuthenticated': True,
                'user': {
                    'sub': user_attrs.get('sub'),
                    'email': user_attrs.get('email'),
                    'email_verified': user_attrs.get('email_verified') == 'true',
                    'tier': user_attrs.get('custom:tier', 'free')
                }
            })
            
        except (client.exceptions.NotAuthorizedException, identity_client.exceptions.NotAuthorizedException):
            return jsonify({
                'isAuthenticated': False,
                'error': 'Token expired or invalid'
            }), 401
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return jsonify({
                'isAuthenticated': False,
                'error': 'Failed to validate token'
            }), 500
            
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({
            'isAuthenticated': False,
            'error': str(e)
        }), 500 