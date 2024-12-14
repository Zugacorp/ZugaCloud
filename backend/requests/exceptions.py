class APIException(Exception):
    """Base exception for API errors"""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

class ConfigurationError(APIException):
    """Raised when there's a configuration error"""
    def __init__(self, message):
        super().__init__(message, status_code=500)

class CredentialsError(APIException):
    """Raised when there's an issue with AWS credentials"""
    def __init__(self, message):
        super().__init__(message, status_code=401)

class ConnectionError(APIException):
    """Raised when there's a connection issue"""
    def __init__(self, message):
        super().__init__(message, status_code=503)

class ValidationError(APIException):
    """Raised when validation fails"""
    def __init__(self, message):
        super().__init__(message, status_code=400)
