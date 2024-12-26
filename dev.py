import os
import time
import sys
import subprocess
import platform
from importlib.metadata import version
import json
import venv
from pathlib import Path
import logging
import shutil
import concurrent.futures

# Configure logging at the start of your script
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_PYTHON_PACKAGES = {
    'flask': 'Flask',
    'flask-cors': 'flask_cors',
    'boto3': 'boto3',
    'cryptography': 'cryptography',
    'opencv-python': 'cv2',
    'pillow': 'PIL',
    'pywin32': 'win32security',
    'aiohttp': 'aiohttp',
    'requests': 'requests'
}

def check_package(package_info):
    """Check if a single package is installed"""
    package_name, import_name = package_info
    try:
        __import__(import_name)
        return True, package_name
    except ImportError:
        return False, package_name

def install_packages(pip_path, packages):
    """Install packages using pip"""
    try:
        # Install packages one by one to better handle errors
        for package in packages:
            logger.info(f"Installing {package}...")
            result = subprocess.run(
                [pip_path, 'install', '-q', package],
                check=True,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.error(f"Failed to install {package}: {result.stderr}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error installing packages: {e}")
        return False

def fast_venv_setup():
    """Optimized virtual environment setup"""
    try:
        venv_path = os.path.join(os.path.dirname(__file__), 'venv')
        is_windows = platform.system() == "Windows"
        scripts_dir = 'Scripts' if is_windows else 'bin'
        
        python_path = os.path.join(venv_path, scripts_dir, 'python.exe' if is_windows else 'python')
        pip_path = os.path.join(venv_path, scripts_dir, 'pip.exe' if is_windows else 'pip')

        # Create new venv if needed
        if not os.path.exists(venv_path):
            logger.info("Creating virtual environment...")
            venv.create(venv_path, with_pip=True)
            
            # Ensure pip is available and updated
            subprocess.run([python_path, '-m', 'ensurepip', '--upgrade'], check=True)
            subprocess.run([pip_path, 'install', '--upgrade', 'pip'], check=True)
        
        # Install required packages
        if not install_packages(pip_path, REQUIRED_PYTHON_PACKAGES.keys()):
            raise Exception("Failed to install required packages")

        return python_path

    except Exception as e:
        logger.error(f"Error in fast_venv_setup: {e}")
        raise

def main():
    """Main entry point with optimized startup"""
    start_time = time.time()
    
    try:
        # Quick environment check
        if sys.prefix == sys.base_prefix:
            python_path = fast_venv_setup()
            if python_path:
                logger.info("Restarting with virtual environment...")
                os.execv(python_path, [python_path, __file__])
                return

        # Import required components
        from backend.initialization import initialize_aws, initialize_app
        from backend.api import create_app
        import threading
        import subprocess
        
        # Create Flask application with optimized settings
        app = create_app()
        app.config['JSON_SORT_KEYS'] = False  # Faster JSON responses
        app.config['PROPAGATE_EXCEPTIONS'] = True
        
        # Initialize backend components in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            aws_future = executor.submit(initialize_aws)
            aws_integration = aws_future.result()
            initialize_app()
        
        # Start Flask server in a separate thread
        def run_flask():
            app.run(host='127.0.0.1', port=5000, threaded=True)
            
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("Flask server started successfully")
        
        # Update Vite config to ensure proper proxy
        vite_config_path = os.path.join(os.path.dirname(__file__), 'frontend', 'vite.config.ts')
        if os.path.exists(vite_config_path):
            with open(vite_config_path, 'r') as f:
                content = f.read()
            if '::1' in content or 'localhost:5000' in content:
                content = content.replace('::1', '127.0.0.1').replace('localhost:5000', '127.0.0.1:5000')
                with open(vite_config_path, 'w') as f:
                    f.write(content)
        
        # Start frontend with proper environment
        base_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_dir = os.path.join(base_dir, 'frontend')
        
        env = {
            **os.environ,
            'NODE_ENV': 'development',
            'VITE_API_URL': 'http://127.0.0.1:5000',
            'AWS_SDK_LOAD_CONFIG': '1'  # Ensure AWS SDK loads config properly
        }
        
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, shell=True, check=True)
            subprocess.Popen(['npm', 'run', 'electron:dev'], cwd=frontend_dir, shell=True, env=env)
            logger.info("Frontend started successfully")
        except Exception as e:
            logger.error(f"Frontend startup error: {e}")
            return False
        
        elapsed_time = time.time() - start_time
        logger.info(f"Startup completed in {elapsed_time:.2f} seconds")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        return False

if __name__ == '__main__':
    main()
