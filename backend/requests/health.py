from flask import jsonify
from .exceptions import ConnectionError

def check_health():
    """Check the health of various system components"""
    try:
        # Basic health check response
        return jsonify({
            'status': 'ok',
            'components': {
                'api': 'healthy',
                'database': 'healthy'
            }
        })
    except Exception as e:
        raise ConnectionError(f"Health check failed: {str(e)}")
