from flask import Blueprint, jsonify, request, redirect, url_for
import os
import requests
import logging
from base64 import b64encode

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Return Cognito hosted UI login URL"""
    cognito_domain = os.environ.get('COGNITO_DOMAIN')
    client_id = os.environ.get('COGNITO_CLIENT_ID')
    redirect_uri = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

    if not all([cognito_domain, client_id]):
        return jsonify({'error': 'Missing Cognito configuration'}), 500

    # Construct the full Cognito domain URL
    cognito_url = f"https://{cognito_domain}"
    if not cognito_domain.startswith('https://'):
        cognito_url = f"https://{cognito_domain}"
    
    login_url = (
        f"{cognito_url}/oauth2/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"scope=email+openid+profile&"
        f"redirect_uri={redirect_uri}/auth/callback"
    )
    
    logger.info(f"Generated Cognito login URL: {login_url}")
    return jsonify({'login_url': login_url})

@auth_bp.route('/callback', methods=['POST'])
def auth_callback():
    """Handle the callback from Cognito hosted UI"""
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({'error': 'No authorization code provided'}), 400

        # Get Cognito configuration
        cognito_domain = os.environ.get('COGNITO_DOMAIN')
        client_id = os.environ.get('COGNITO_CLIENT_ID')
        client_secret = os.environ.get('COGNITO_CLIENT_SECRET')
        redirect_uri = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

        if not all([cognito_domain, client_id, client_secret]):
            return jsonify({'error': 'Missing Cognito configuration'}), 500

        # Create the authorization header
        auth = b64encode(f"{client_id}:{client_secret}".encode()).decode()

        # Construct the full Cognito domain URL
        cognito_url = f"https://{cognito_domain}"
        if not cognito_domain.startswith('https://'):
            cognito_url = f"https://{cognito_domain}"

        # Exchange the authorization code for tokens
        token_endpoint = f"{cognito_url}/oauth2/token"
        response = requests.post(
            token_endpoint,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {auth}'
            },
            data={
                'grant_type': 'authorization_code',
                'client_id': client_id,
                'code': code,
                'redirect_uri': f"{redirect_uri}/auth/callback"
            }
        )

        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            return jsonify({'error': 'Failed to exchange authorization code'}), response.status_code

        # Return the tokens to the client
        return jsonify(response.json())

    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """Redirect to Cognito hosted UI for registration"""
    cognito_domain = os.environ.get('COGNITO_DOMAIN')
    client_id = os.environ.get('COGNITO_CLIENT_ID')
    redirect_uri = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

    if not all([cognito_domain, client_id]):
        return jsonify({'error': 'Missing Cognito configuration'}), 500

    # Construct the full Cognito domain URL
    cognito_url = f"https://{cognito_domain}"
    if not cognito_domain.startswith('https://'):
        cognito_url = f"https://{cognito_domain}"
    
    signup_url = (
        f"{cognito_url}/signup?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"scope=email+openid+profile&"
        f"redirect_uri={redirect_uri}/auth/callback"
    )
    
    return redirect(signup_url) 