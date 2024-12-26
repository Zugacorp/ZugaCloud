import os

class EnvironmentManager:
    AWS_VARS = {
        'access_key': ['AWS_ACCESS_KEY', 'VENV_AWS_ACCESS_KEY', 'AWS_ACCESS_KEY_ID'],
        'secret_key': ['AWS_SECRET_KEY', 'VENV_AWS_SECRET_KEY', 'AWS_SECRET_ACCESS_KEY'],
        'region': ['AWS_DEFAULT_REGION', 'VENV_AWS_DEFAULT_REGION']
    }

    @staticmethod
    def get_env_value(var_type: str) -> str:
        """Get environment variable value checking multiple possible names"""
        if var_type not in EnvironmentManager.AWS_VARS:
            return None
        
        for var_name in EnvironmentManager.AWS_VARS[var_type]:
            value = os.environ.get(var_name)
            if value:
                return value
        return None

    @staticmethod
    def set_env_value(var_type: str, value: str) -> bool:
        """Set environment variable with appropriate naming"""
        if var_type not in EnvironmentManager.AWS_VARS:
            return False
        
        primary_var = EnvironmentManager.AWS_VARS[var_type][0]
        venv_var = EnvironmentManager.AWS_VARS[var_type][1]
        
        os.environ[primary_var] = value
        os.environ[venv_var] = value
        return True