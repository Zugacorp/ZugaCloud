import os
import pytest
import boto3
from botocore.exceptions import ClientError
from backend.auth.auth import init_auth, get_cognito_client
from backend.auth.validators import CognitoValidator
from unittest.mock import patch, MagicMock
from flask import Flask
from pathlib import Path

class TestCognitoConfiguration:
    @pytest.fixture
    def mock_env_vars(self):
        """Fixture to set up test environment variables"""
        env_vars = {
            'AWS_REGION': 'us-east-1',
            'COGNITO_USER_POOL_ID': 'us-east-1_testpool',
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_CLIENT_SECRET': 'test_client_secret',
            'COGNITO_IDENTITY_POOL_ID': 'us-east-1:test-identity-pool',
            'AWS_ACCESS_KEY_ID': 'test_access_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
            'FLASK_SECRET_KEY': 'test_secret_key',
            'COGNITO_DOMAIN': 'test.auth.us-east-1.amazoncognito.com'
        }
        with patch.dict(os.environ, env_vars):
            yield env_vars

    @pytest.fixture
    def app(self):
        """Create a Flask application for testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    def test_cognito_validator(self, mock_env_vars):
        """Test the Cognito configuration validator"""
        config = {
            'user_pool_id': mock_env_vars['COGNITO_USER_POOL_ID'],
            'client_id': mock_env_vars['COGNITO_CLIENT_ID'],
            'client_secret': mock_env_vars['COGNITO_CLIENT_SECRET'],
            'region': mock_env_vars['AWS_REGION']
        }
        is_valid, error = CognitoValidator.validate_cognito_config(config)
        assert is_valid
        assert error == ""

    @patch('boto3.client')
    def test_cognito_client_creation(self, mock_boto3_client, mock_env_vars):
        """Test Cognito client creation and configuration"""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # Mock successful user pool listing
        mock_client.list_user_pools.return_value = {
            'UserPools': [{
                'Id': mock_env_vars['COGNITO_USER_POOL_ID'],
                'Name': 'TestPool'
            }]
        }
        
        client = get_cognito_client()
        
        # Verify client creation with correct parameters
        mock_boto3_client.assert_called_once_with(
            'cognito-idp',
            aws_access_key_id=mock_env_vars['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=mock_env_vars['AWS_SECRET_ACCESS_KEY'],
            region_name=mock_env_vars['AWS_REGION'],
            config=mock_boto3_client.call_args[1]['config']  # Just verify the config is passed
        )
        
        # Verify client functionality
        mock_client.list_user_pools.assert_called_once_with(MaxResults=1)

    @patch('boto3.client')
    def test_identity_pool_configuration(self, mock_boto3_client, mock_env_vars):
        """Test identity pool configuration and access"""
        mock_cognito_client = MagicMock()
        mock_identity_client = MagicMock()
        
        # Configure mock clients
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'cognito-idp': mock_cognito_client,
            'cognito-identity': mock_identity_client
        }[service]
        
        # Mock identity pool response
        mock_identity_client.describe_identity_pool.return_value = {
            'IdentityPoolId': mock_env_vars['COGNITO_IDENTITY_POOL_ID'],
            'IdentityPoolName': 'TestIdentityPool',
            'AllowUnauthenticatedIdentities': False,
            'CognitoIdentityProviders': [{
                'ProviderName': f"cognito-idp.{mock_env_vars['AWS_REGION']}.amazonaws.com/{mock_env_vars['COGNITO_USER_POOL_ID']}",
                'ClientId': mock_env_vars['COGNITO_CLIENT_ID'],
                'ServerSideTokenCheck': True
            }]
        }
        
        # Create identity client
        identity_client = boto3.client('cognito-identity',
            aws_access_key_id=mock_env_vars['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=mock_env_vars['AWS_SECRET_ACCESS_KEY'],
            region_name=mock_env_vars['AWS_REGION']
        )
        
        # Verify identity pool configuration
        response = identity_client.describe_identity_pool(
            IdentityPoolId=mock_env_vars['COGNITO_IDENTITY_POOL_ID']
        )
        assert response['IdentityPoolId'] == mock_env_vars['COGNITO_IDENTITY_POOL_ID']
        assert not response['AllowUnauthenticatedIdentities']
        
        # Verify Cognito provider configuration
        provider = response['CognitoIdentityProviders'][0]
        assert provider['ClientId'] == mock_env_vars['COGNITO_CLIENT_ID']
        assert provider['ServerSideTokenCheck']

    @patch('boto3.client')
    @patch('pathlib.Path')
    def test_missing_identity_pool_id(self, mock_path, mock_boto3_client, mock_env_vars, app):
        """Test handling of missing identity pool ID"""
        # Mock the path resolution
        mock_file_path = MagicMock()
        mock_parent = MagicMock()
        mock_parent.parent = 'backend'
        mock_file_path.parent = mock_parent
        mock_file_path.exists.return_value = True
        mock_path.return_value = mock_file_path
        
        mock_cognito_client = MagicMock()
        mock_identity_client = MagicMock()
        
        # Configure mock clients
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'cognito-idp': mock_cognito_client,
            'cognito-identity': mock_identity_client
        }[service]
        
        # Create a clean environment without any variables
        clean_env = {}
        
        with patch.dict(os.environ, clean_env, clear=True):
            with pytest.raises(ValueError) as exc_info:
                init_auth(app)
            
            assert "Missing required environment variables" in str(exc_info.value)

    @patch('boto3.client')
    def test_auth_flow_with_identity_pool(self, mock_boto3_client, mock_env_vars, app):
        """Test complete authentication flow including identity pool access"""
        # Configure Flask app for testing
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['TESTING'] = True
        
        mock_cognito_client = MagicMock()
        mock_identity_client = MagicMock()
        
        # Configure mock clients
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'cognito-idp': mock_cognito_client,
            'cognito-identity': mock_identity_client
        }[service]
        
        # Mock successful authentication
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'test_access_token',
                'IdToken': 'test_id_token',
                'RefreshToken': 'test_refresh_token'
            }
        }
        
        # Mock identity pool credentials
        mock_identity_client.get_id.return_value = {
            'IdentityId': 'test_identity_id'
        }
        
        # Create a datetime object for expiration
        from datetime import datetime, timezone
        expiration_time = datetime(2024, 3, 14, 12, 0, 0, tzinfo=timezone.utc)
        
        mock_identity_client.get_credentials_for_identity.return_value = {
            'IdentityId': 'test_identity_id',
            'Credentials': {
                'AccessKeyId': 'test_temp_access_key',
                'SecretKey': 'test_temp_secret_key',
                'SessionToken': 'test_session_token',
                'Expiration': expiration_time
            }
        }
        
        # Test authentication flow
        with patch.dict(os.environ, mock_env_vars, clear=True):
            with app.test_request_context() as ctx:
                with app.test_client() as client:
                    ctx.request.get_json = lambda: {
                        'email': 'test@example.com',
                        'password': 'Test123!'
                    }
                    
                    from backend.auth.auth import login
                    response = login()
                    
                    # Convert tuple response to Flask response if needed
                    if isinstance(response, tuple):
                        data, status_code = response
                        assert status_code == 200
                        data = data.get_json() if hasattr(data, 'get_json') else data
                    else:
                        data = response.get_json()
                    
                    assert data['success'] is True
                    assert 'tokens' in data
                    assert 'credentials' in data
                    assert data['credentials']['identity_id'] == 'test_identity_id' 