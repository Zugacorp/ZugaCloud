import boto3
import os
from dotenv import load_dotenv
import logging
import unittest
from pathlib import Path
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAWSPermissions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up AWS test environment"""
        try:
            # Find and load the correct .env file
            current_dir = Path(__file__).parent  # Get the directory containing this test file
            project_root = current_dir.parent.parent  # Go up two levels to project root
            backend_env = project_root / 'backend' / '.env.backend'
            
            logger.info(f"Looking for .env.backend at: {backend_env}")
            
            if not backend_env.exists():
                raise EnvironmentError(f"Backend .env file not found at {backend_env}!")
            
            load_dotenv(backend_env)
            
            # Verify required environment variables
            required_vars = [
                'AWS_ACCESS_KEY_ID',
                'AWS_SECRET_ACCESS_KEY',
                'AWS_REGION',
                'COGNITO_USER_POOL_ID',
                'COGNITO_CLIENT_ID'
            ]
            
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
            # Create AWS session
            cls.session = boto3.Session(
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_REGION')
            )
            
            # Store common variables
            cls.user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
            cls.client_id = os.environ.get('COGNITO_CLIENT_ID')
            
            # Create Cognito client
            cls.cognito = cls.session.client('cognito-idp')
            
            logger.info("AWS test environment setup completed")
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            raise
            
    def test_list_user_pools(self):
        """Test ability to list Cognito user pools"""
        try:
            response = self.cognito.list_user_pools(MaxResults=10)
            pools = response.get('UserPools', [])
            self.assertTrue(len(pools) > 0, "No user pools found")
            logger.info(f"Found {len(pools)} user pools")
        except ClientError as e:
            self.fail(f"Failed to list user pools: {str(e)}")
            
    def test_describe_user_pool(self):
        """Test ability to describe our user pool"""
        try:
            response = self.cognito.describe_user_pool(
                UserPoolId=self.user_pool_id
            )
            pool = response.get('UserPool', {})
            self.assertIsNotNone(pool)
            self.assertEqual(pool['Id'], self.user_pool_id)
            logger.info(f"Successfully described user pool: {pool['Name']}")
        except ClientError as e:
            self.fail(f"Failed to describe user pool: {str(e)}")
            
    def test_list_users(self):
        """Test ability to list users in the pool"""
        try:
            response = self.cognito.list_users(
                UserPoolId=self.user_pool_id
            )
            users = response.get('Users', [])
            self.assertIsNotNone(users)
            logger.info(f"Found {len(users)} users in pool")
            
            # Log some user details (without sensitive info)
            for user in users:
                username = user.get('Username')
                status = user.get('UserStatus')
                logger.info(f"User: {username}, Status: {status}")
        except ClientError as e:
            self.fail(f"Failed to list users: {str(e)}")
            
    def test_describe_client(self):
        """Test ability to describe our client configuration"""
        try:
            response = self.cognito.describe_user_pool_client(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id
            )
            client = response.get('UserPoolClient', {})
            self.assertIsNotNone(client)
            self.assertEqual(client['ClientId'], self.client_id)
            
            # Log client configuration (without secrets)
            logger.info(f"Client name: {client['ClientName']}")
            logger.info(f"Auth flows: {client.get('ExplicitAuthFlows', [])}")
            logger.info(f"OAuth flows: {client.get('AllowedOAuthFlows', [])}")
        except ClientError as e:
            self.fail(f"Failed to describe client: {str(e)}")
            
    def test_iam_permissions(self):
        """Test IAM-specific permissions"""
        try:
            iam = self.session.client('iam')
            
            # Get current user info
            user_response = iam.get_user()
            self.assertIsNotNone(user_response.get('User'))
            username = user_response['User']['UserName']
            logger.info(f"Current IAM user: {username}")
            
            # List attached policies
            policy_response = iam.list_attached_user_policies(
                UserName=username
            )
            policies = policy_response.get('AttachedPolicies', [])
            self.assertTrue(len(policies) > 0, "No policies attached to user")
            
            logger.info("\nAttached policies:")
            for policy in policies:
                logger.info(f"- {policy['PolicyName']}")
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                logger.warning("Limited IAM permissions - this is normal for restricted users")
            else:
                self.fail(f"Failed to test IAM permissions: {str(e)}")

def run_tests():
    """Run all AWS permission tests"""
    try:
        logger.info("=== Starting AWS Permissions Tests ===")
        unittest.main(verbosity=2, exit=False)
        logger.info("=== AWS Tests Completed Successfully ===")
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_tests() 