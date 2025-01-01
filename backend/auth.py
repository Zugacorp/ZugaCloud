from flask import Flask, redirect, url_for, session, request, jsonify
from authlib.integrations.flask_client import OAuth
import os
from functools import wraps

def init_auth(app):
    """Initialize authentication with AWS Cognito"""
    # Use environment variable for secret key, fallback to random for development
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    oauth = OAuth(app)

    # Get Cognito configuration from environment variables
    COGNITO_DOMAIN = os.environ.get('COGNITO_DOMAIN', 'https://cognito-idp.us-east-2.amazonaws.com/us-east-2_0XE0zW4IF')
    COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID', '4cf4nga6s2jn7qfqvh029b1kug')
    COGNITO_CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')

    if not COGNITO_CLIENT_SECRET:
        raise ValueError("COGNITO_CLIENT_SECRET environment variable is not set")

    # Configure AWS Cognito OAuth
    oauth.register(
        name='cognito',
        server_metadata_url=f'{COGNITO_DOMAIN}/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'phone openid email'
        },
        client_id=COGNITO_CLIENT_ID,
        client_secret=COGNITO_CLIENT_SECRET
    )

    @app.route('/api/auth/status')
    def auth_status():
        user = session.get('user')
        return jsonify({
            'authenticated': bool(user),
            'user': user
        })

    @app.route('/login')
    def login():
        redirect_uri = url_for('auth_callback', _external=True)
        return oauth.cognito.authorize_redirect(redirect_uri)

    @app.route('/auth/callback')
    def auth_callback():
        token = oauth.cognito.authorize_access_token()
        user_info = oauth.cognito.parse_id_token(token)
        session['user'] = user_info
        return redirect('/')

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        return redirect('/')

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function

    return oauth, login_required 