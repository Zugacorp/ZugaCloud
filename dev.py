import sys
import pkg_resources
import os
import subprocess
from dotenv import load_dotenv
import threading
import time

# Print Python information for debugging
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")

# Print installed packages
print("Installed packages:")
installed_packages = [f"  {dist.key} {dist.version}" for dist in pkg_resources.working_set]
for package in installed_packages:
    print(package)

# Load environment variables
load_dotenv()

def run_frontend():
    """Run the frontend development server"""
    os.chdir('frontend')
    subprocess.run(['npm', 'run', 'electron:dev'], shell=True)

def run_backend():
    """Run the backend server"""
    try:
        # Import and create the Flask application
        from backend.api import create_app
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        import logging
        logging.error(f"Startup error: {str(e)}")
        raise

if __name__ == '__main__':
    # Start the backend server in a separate thread
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()

    # Wait a bit for the backend to start
    time.sleep(2)

    # Start the frontend server in the main thread
    run_frontend()
