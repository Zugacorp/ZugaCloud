import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment files for frontend and backend"""
    try:
        # Get the project root directory
        current_dir = Path(__file__).parent  # Get the directory containing this script
        project_root = current_dir.parent.parent  # Go up two levels to project root
        
        # Define environment file paths
        backend_env = project_root / 'backend' / '.env.backend'
        frontend_env = project_root / 'frontend' / '.env.frontend'
        admin_env = project_root / 'backend' / '.env.backend.admin'
        
        logger.info(f"\nChecking environment files:")
        logger.info(f"Backend env path: {backend_env}")
        logger.info(f"Frontend env path: {frontend_env}")
        logger.info(f"Admin env path: {admin_env}")
        
        # Ensure backend .env.backend exists
        if not backend_env.exists():
            logger.error("Backend .env.backend file not found!")
            return False
            
        # Read backend .env.backend
        with open(backend_env, 'r') as f:
            env_contents = f.readlines()
            
        # Validate required backend variables
        required_backend_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'COGNITO_USER_POOL_ID',
            'COGNITO_CLIENT_ID',
            'COGNITO_CLIENT_SECRET',
            'COGNITO_DOMAIN',
            'FRONTEND_URL'
        ]
        
        # Check for missing variables
        existing_vars = {line.split('=')[0].strip(): line for line in env_contents if '=' in line}
        missing_vars = [var for var in required_backend_vars if var not in existing_vars]
        
        if missing_vars:
            logger.error(f"Missing required backend variables: {', '.join(missing_vars)}")
            return False
            
        # Create frontend .env.frontend
        frontend_vars = []
        frontend_vars.append("# Frontend Environment Variables\n")
        
        # Add all existing VITE_ variables
        frontend_vars.extend([line for line in env_contents if line.startswith('VITE_')])
        
        # Map backend variables to frontend VITE_ variables
        frontend_mappings = {
            'COGNITO_USER_POOL_ID': 'VITE_COGNITO_USER_POOL_ID',
            'COGNITO_CLIENT_ID': 'VITE_COGNITO_CLIENT_ID',
            'AWS_REGION': 'VITE_AWS_REGION',
            'COGNITO_DOMAIN': 'VITE_COGNITO_DOMAIN',
            'FRONTEND_URL': 'VITE_FRONTEND_URL',
            'BACKEND_URL': 'VITE_BACKEND_URL'
        }
        
        # Add mapped variables
        for backend_key, frontend_key in frontend_mappings.items():
            if backend_key in existing_vars:
                value = existing_vars[backend_key].split('=', 1)[1].strip()
                frontend_vars.append(f"{frontend_key}={value}\n")
        
        # Create frontend directory if it doesn't exist
        frontend_env.parent.mkdir(parents=True, exist_ok=True)
        
        # Write frontend environment file
        with open(frontend_env, 'w') as f:
            f.writelines(frontend_vars)
        logger.info(f"Created frontend environment file at {frontend_env}")
        
        # Create admin environment file if it doesn't exist
        if not admin_env.exists() and 'COGNITO_ADMIN_CLIENT_ID' in existing_vars:
            with open(admin_env, 'w') as f:
                f.write(existing_vars['COGNITO_ADMIN_CLIENT_ID'])
            logger.info(f"Created admin environment file at {admin_env}")
        
        # Clean up any old .env files
        old_files = [
            project_root / '.env',
            project_root / 'frontend' / '.env',
            project_root / 'backend' / '.env'
        ]
        
        for old_file in old_files:
            if old_file.exists():
                old_file.unlink()
                logger.info(f"Removed old environment file: {old_file}")
                
        logger.info("\nEnvironment setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up environment: {str(e)}")
        return False

if __name__ == '__main__':
    setup_environment() 