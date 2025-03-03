import hmac
import hashlib
import base64
from dotenv import load_dotenv
import os
import logging
import unittest
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCognitoHash(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Find and load the correct .env file
        current_dir = Path(__file__).parent  # Get the directory containing this test file
        project_root = current_dir.parent.parent  # Go up two levels to project root
        backend_env = project_root / 'backend' / '.env.backend'
        
        logger.info(f"Looking for .env.backend at: {backend_env}")
        
        if not backend_env.exists():
            raise EnvironmentError(f"Backend .env file not found at {backend_env}!")
        
        load_dotenv(backend_env)
        
        # Verify required environment variables
        required_vars = ['COGNITO_CLIENT_ID', 'COGNITO_CLIENT_SECRET']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        cls.client_id = os.environ.get('COGNITO_CLIENT_ID')
        cls.client_secret = os.environ.get('COGNITO_CLIENT_SECRET')
        
        logger.info("Environment setup completed successfully")
        
    def calculate_secret_hash(self, username):
        """Calculate secret hash for Cognito authentication"""
        try:
            # Validate input
            if not username or not username.strip():
                raise ValueError("Username cannot be empty")
            
            # Clean inputs
            username = username.strip()
            client_id = self.client_id.strip()
            client_secret = self.client_secret.strip()
            
            # Validate Cognito credentials
            if not client_id or not client_secret:
                raise ValueError("Invalid Cognito credentials")
            
            # Log input information
            logger.info("\n=== Input Values ===")
            logger.info(f"Username ({len(username)}): {username}")
            logger.info(f"Client ID ({len(client_id)}): {client_id}")
            logger.info(f"Client Secret length: {len(client_secret)}")
            
            # Create message string
            message_str = username + client_id
            message = message_str.encode('utf-8')
            key = client_secret.encode('utf-8')
            
            # Calculate HMAC SHA256
            dig = hmac.new(key, message, digestmod=hashlib.sha256).digest()
            
            # Base64 encode
            return base64.b64encode(dig).decode()
            
        except Exception as e:
            logger.error(f"Error calculating hash: {str(e)}")
            raise
            
    def test_valid_email(self):
        """Test hash generation with valid email"""
        email = "zugacloud@gmail.com"
        hash_result = self.calculate_secret_hash(email)
        self.assertIsNotNone(hash_result)
        self.assertTrue(len(hash_result) > 0)
        logger.info(f"Valid email hash: {hash_result}")
        
    def test_empty_username(self):
        """Test hash generation with empty username"""
        with self.assertRaises(ValueError):
            self.calculate_secret_hash("")
            
    def test_special_characters(self):
        """Test hash generation with special characters"""
        email = "test+special@zugacloud.com"
        hash_result = self.calculate_secret_hash(email)
        self.assertIsNotNone(hash_result)
        logger.info(f"Special characters hash: {hash_result}")
        
    def test_hash_consistency(self):
        """Test that same input produces same hash"""
        email = "test@zugacloud.com"
        hash1 = self.calculate_secret_hash(email)
        hash2 = self.calculate_secret_hash(email)
        self.assertEqual(hash1, hash2)
        logger.info("Hash consistency verified")
        
    def test_different_users(self):
        """Test that different users produce different hashes"""
        hash1 = self.calculate_secret_hash("user1@zugacloud.com")
        hash2 = self.calculate_secret_hash("user2@zugacloud.com")
        self.assertNotEqual(hash1, hash2)
        logger.info("Different users produce different hashes")

def run_tests():
    """Run all tests with detailed logging"""
    try:
        logger.info("=== Starting Cognito Hash Tests ===")
        unittest.main(verbosity=2, exit=False)
        logger.info("=== Tests Completed Successfully ===")
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_tests() 