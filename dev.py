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

def create_venv():
    """Create and activate virtual environment if it doesn't exist."""
    try:
        # Get absolute path and handle spaces
        base_dir = os.path.dirname(os.path.abspath(__file__))
        venv_path = os.path.join(base_dir, 'venv')
        
        if not os.path.exists(venv_path):
            print("Creating virtual environment...")
            venv.create(venv_path, with_pip=True)
            print(f"Virtual environment created at: {venv_path}")
        else:
            print("Virtual environment already exists")

        # Determine the path to the activation script
        if platform.system() == "Windows":
            python_path = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_path = os.path.join(venv_path, "bin", "python")

        if not os.path.exists(python_path):
            print("Error: Virtual environment Python not found")
            sys.exit(1)

        # If we're not already in the venv, restart the script with the venv Python
        if sys.prefix == sys.base_prefix:
            print("Restarting with virtual environment...")
            script_path = os.path.abspath(__file__)
            
            # Use list form of execv to properly handle paths with spaces
            os.execv(python_path, [
                python_path,
                f'"{script_path}"' if ' ' in script_path else script_path
            ])

        print("Using virtual environment Python:", sys.executable)
        return True
        
    except Exception as e:
        print(f"Error creating virtual environment: {str(e)}")
        logger.exception("Detailed traceback:")
        sys.exit(1)

def check_python_dependencies():
    """Check if required Python packages are installed."""
    print("\nChecking Python dependencies...")
    missing = []
    installed = []
    for package, import_name in REQUIRED_PYTHON_PACKAGES.items():
        try:
            __import__(import_name)
            pkg_version = version(package)
            installed.append(f"{package} ({pkg_version})")
        except ImportError:
            missing.append(package)
        except Exception:  # Handle case where package is installed but version can't be determined
            installed.append(f"{package} (version unknown)")
    
    if installed:
        print("Installed packages:")
        for pkg in installed:
            print(f"  ✓ {pkg}")
    
    return missing

def install_python_dependencies(missing_packages):
    """Install missing Python packages."""
    if missing_packages:
        print("\nInstalling missing Python packages:")
        for package in missing_packages:
            print(f"  Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"  ✓ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"  ✗ Failed to install {package}: {str(e)}")
                sys.exit(1)

def check_node_version():
    """Check if Node.js is installed and version is compatible."""
    print("\nChecking Node.js installation...")
    try:
        node_version = subprocess.check_output(['node', '--version']).decode().strip()
        version_num = float(node_version.replace('v', '').split('.')[0])
        if version_num >= 14:
            print(f"  ✓ Node.js {node_version} detected (compatible)")
            return True
        else:
            print(f"  ✗ Node.js {node_version} detected (incompatible - requires v14+)")
            return False
    except:
        print("  ✗ Node.js not found")
        return False

def check_npm_dependencies(directory):
    """Check if npm dependencies are installed in specified directory."""
    print(f"\nChecking npm dependencies in {directory}...")
    node_modules = os.path.join(directory, 'node_modules')
    package_lock = os.path.join(directory, 'package-lock.json')
    
    if os.path.exists(node_modules) and os.path.exists(package_lock):
        print("  ✓ npm dependencies found")
        return True
    else:
        print("  ✗ npm dependencies missing")
        return False

def install_npm_dependencies(directory):
    """Install npm dependencies in specified directory."""
    print(f"\nInstalling npm dependencies in {directory}...")
    try:
        subprocess.check_call('npm install', shell=True, cwd=directory)
        print("  ✓ npm dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to install npm dependencies: {str(e)}")
        sys.exit(1)

def check_aws_cli():
    """Check if AWS CLI is installed."""
    print("\nChecking AWS CLI installation...")
    try:
        version = subprocess.check_output(['aws', '--version']).decode().strip()
        print(f"  ✓ AWS CLI detected: {version}")
        return True
    except:
        print("  ✗ AWS CLI not found")
        return False

def check_vlc():
    """Check if VLC is installed."""
    print("\nChecking VLC installation...")
    if platform.system() == 'Windows':
        vlc_path = 'C:\\Program Files\\VideoLAN\\VLC\\vlc.exe'
    elif platform.system() == 'Darwin':
        vlc_path = '/Applications/VLC.app'
    else:
        vlc_path = '/usr/bin/vlc'
    
    if os.path.exists(vlc_path):
        print(f"  ✓ VLC detected at: {vlc_path}")
        return True
    else:
        print("  ✗ VLC not found")
        return False

def setup_environment():
    """Setup and verify all requirements."""
    print("\n=== Setting up ZugaCloud Development Environment ===")
    
    # Create and activate virtual environment
    create_venv()
    
    # Transfer environment variables if they exist
    if os.environ.get('AWS_ACCESS_KEY') and os.environ.get('AWS_SECRET_KEY'):
        os.environ['VENV_AWS_ACCESS_KEY'] = os.environ['AWS_ACCESS_KEY']
        os.environ['VENV_AWS_SECRET_KEY'] = os.environ['AWS_SECRET_KEY']
        os.environ['VENV_AWS_DEFAULT_REGION'] = os.environ.get('AWS_DEFAULT_REGION', 'us-east-2')
    
    # Check Python dependencies
    missing_packages = check_python_dependencies()
    if missing_packages:
        print(f"\nMissing Python packages: {', '.join(missing_packages)}")
        install_python_dependencies(missing_packages)

    # Check Node.js
    if not check_node_version():
        print("\nError: Node.js v14+ is required")
        print("Please install from https://nodejs.org/")
        sys.exit(1)

    # Check and install npm dependencies
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, 'frontend')
    
    if not check_npm_dependencies(root_dir):
        install_npm_dependencies(root_dir)
    
    if not check_npm_dependencies(frontend_dir):
        install_npm_dependencies(frontend_dir)

    # Check AWS CLI
    if not check_aws_cli():
        print("\nWarning: AWS CLI not found")
        print("Please install from https://aws.amazon.com/cli/")

    # Check VLC
    if not check_vlc():
        print("\nWarning: VLC not found")
        print("Please install VLC from https://www.videolan.org/")

    print("\n=== Environment setup completed ===\n")

def run_flask():
    """Run Flask server."""
    print("Starting Flask server...")
    from main import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=5000)

def wait_for_flask():
    """Wait for Flask server to be ready"""
    print("Waiting for Flask server to start...")
    max_attempts = 30
    attempts = 0
    
    # Import the actual requests library
    try:
        import requests
    except ImportError:
        print("Error: requests module not found")
        return False
    
    while attempts < max_attempts:
        try:
            response = requests.get('http://127.0.0.1:5000/api/health')
            if response.status_code == 200:
                print("Flask server is ready!")
                return True
        except requests.exceptions.RequestException:  # Use a more general exception
            attempts += 1
            time.sleep(1)
            print(f"Waiting for Flask server... ({attempts}/{max_attempts})")
    
    print("Failed to connect to Flask server")
    return False

def run_electron():
    """Run Electron application."""
    logger.info("Starting Electron application...")
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')

    # Find npm executable
    npm_command = shutil.which('npm')
    if npm_command is None:
        logger.error("npm command not found. Please ensure npm is installed and in your PATH.")
        sys.exit(1)
    else:
        logger.info(f"Found npm at: {npm_command}")

    # Ensure electron/src directory exists
    electron_src_dir = os.path.join(frontend_dir, 'electron', 'src')
    os.makedirs(electron_src_dir, exist_ok=True)

    # Run Vite in development mode
    logger.info("Starting Vite development server...")
    vite_process = subprocess.Popen([npm_command, 'run', 'dev'], cwd=frontend_dir)

    # Wait for Vite to start
    logger.info("Waiting for Vite server to start...")
    time.sleep(5)  # Increase wait time if necessary

    try:
        # Start Electron
        logger.info("Starting Electron...")
        subprocess.run([npm_command, 'run', 'electron-dev'], cwd=frontend_dir)
    finally:
        vite_process.terminate()

if __name__ == '__main__':
    print("Initializing ZugaCloud development environment...")
    setup_environment()
    
    print("\nStarting ZugaCloud...")
    # Start Flask in a separate process
    from multiprocessing import Process
    server = Process(target=run_flask)
    server.start()
    
    # Wait for Flask to be fully started
    if not wait_for_flask():
        print("Error: Flask server failed to start")
        server.terminate()
        sys.exit(1)
    
    try:
        run_electron()
    finally:
        print("\nShutting down servers...")
        server.terminate()
        print("Cleanup completed")
