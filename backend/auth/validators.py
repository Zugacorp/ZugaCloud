class ConfigValidator:
    @staticmethod
    def validate_aws_config(config: dict) -> tuple[bool, str]:
        required_fields = {
            'bucket_name': str,
            'region': str
        }
        
        for field, field_type in required_fields.items():
            if field not in config:
                return False, f"Missing required field: {field}"
            if not isinstance(config[field], field_type):
                return False, f"Invalid type for {field}"
        
        return True, ""

class EmailValidator:
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """
        Validate email format.
        Returns (is_valid: bool, error_message: str)
        """
        import re
        
        if not email:
            return False, "Email is required"
            
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
            
        return True, ""

class PasswordValidator:
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password against security requirements.
        Returns (is_valid: bool, error_message: str)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
            
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
            
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
            
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
            
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False, "Password must contain at least one special character"
            
        return True, ""

class TokenValidator:
    @staticmethod
    def validate_token(token: str) -> tuple[bool, str]:
        """
        Validates a JWT token format
        
        Args:
            token (str): The JWT token to validate
            
        Returns:
            tuple[bool, str]: A tuple containing (is_valid, error_message)
        """
        if not token:
            return False, "Token is required"
            
        # Basic JWT format check (header.payload.signature)
        parts = token.split('.')
        if len(parts) != 3:
            return False, "Invalid token format"
            
        return True, ""

class CognitoValidator:
    @staticmethod
    def validate_cognito_config(config: dict) -> tuple[bool, str]:
        """
        Validates AWS Cognito configuration
        
        Args:
            config (dict): The Cognito configuration to validate
            
        Returns:
            tuple[bool, str]: A tuple containing (is_valid, error_message)
        """
        required_fields = {
            'user_pool_id': str,
            'client_id': str,
            'client_secret': str,
            'region': str
        }
        
        for field, field_type in required_fields.items():
            if field not in config:
                return False, f"Missing required field: {field}"
            if not isinstance(config[field], field_type):
                return False, f"Invalid type for {field}"
                
        return True, "" 