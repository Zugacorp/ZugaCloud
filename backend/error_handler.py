import logging
from flask import jsonify

logger = logging.getLogger(__name__)

class APIError(Exception):
    def __init__(self, message: str, code: str = None, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

def handle_api_error(error: Exception) -> tuple:
    if isinstance(error, APIError):
        return jsonify({
            'error': error.message,
            'code': error.code
        }), error.status_code
    
    logger.error(f"Unhandled error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500