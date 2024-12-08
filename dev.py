import os
import time
import sys
import subprocess
from main import create_app

def run_flask():
    app = create_app()
    app.run(host='0.0.0.0', port=5000)

def run_electron():
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    # Ensure electron/src directory exists
    electron_src_dir = os.path.join(frontend_dir, 'electron', 'src')
    os.makedirs(electron_src_dir, exist_ok=True)
    
    # Run Vite in development mode
    vite_process = subprocess.Popen('npm run dev', shell=True, cwd=frontend_dir)
    
    # Wait for Vite to start
    time.sleep(2)
    
    try:
        # Start Electron
        subprocess.run('npm run electron-dev', shell=True, cwd=frontend_dir)
    finally:
        vite_process.terminate()

if __name__ == '__main__':
    # Start Flask in a separate process
    from multiprocessing import Process
    server = Process(target=run_flask)
    server.start()
    
    # Wait for Flask to start
    time.sleep(2)
    
    try:
        run_electron()
    finally:
        server.terminate()
