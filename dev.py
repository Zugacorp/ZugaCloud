import sys
import pkg_resources
import os
import subprocess
import threading
import time
import logging
import signal
import shutil
import psutil
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dev.log')
    ]
)
logger = logging.getLogger('zugacloud-dev')

# Global process tracking
processes = []

def kill_process_on_port(port):
    """Kill any process using the specified port, but NEVER kill node processes"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == port:
                        process_name = proc.info['name'].lower()
                        
                        # Add detailed logging about the process found
                        logger.info(f"Found process {process_name} (PID: {proc.pid}) using port {port}")
                        
                        # NEVER kill node processes
                        if 'node' in process_name or 'npm' in process_name or 'electron' in process_name:
                            logger.info(f"Skipping node/npm/electron process: {process_name} (PID: {proc.pid})")
                            continue
                            
                        # Skip killing our own processes if they're in the tracked processes list
                        if any(p.pid == proc.pid for p in processes):
                            logger.info(f"Skipping our own process {process_name} (PID: {proc.pid})")
                            continue
                            
                        # Only kill non-node, non-tracked processes
                        logger.info(f"Killing process {process_name} (PID: {proc.pid}) using port {port}")
                        if os.name == 'nt':  # Windows
                            subprocess.run(['taskkill', '/F', '/PID', str(proc.pid)], capture_output=True)
                        else:  # Unix/Linux/MacOS
                            os.kill(proc.pid, signal.SIGTERM)
                        time.sleep(1)  # Give the process time to die
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {e}")

def cleanup_processes():
    """Cleanup all running processes and ports, but NEVER kill node processes"""
    try:
        # Kill processes using our ports, but only if they're not node processes
        ports_to_clean = [5000, 5001]  # Backend and frontend ports
        for port in ports_to_clean:
            kill_process_on_port(port)
            
        # Kill our tracked processes, but skip node processes
        for process in processes:
            try:
                if process.poll() is None:  # Process is still running
                    # Get process name if possible
                    try:
                        proc = psutil.Process(process.pid)
                        process_name = proc.name().lower()
                        
                        # Skip node processes
                        if 'node' in process_name or 'npm' in process_name or 'electron' in process_name:
                            logger.info(f"Skipping node/npm/electron process during cleanup: {process_name} (PID: {process.pid})")
                            continue
                            
                        logger.info(f"Cleaning up process: {process_name} (PID: {process.pid})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        logger.info(f"Cleaning up process with PID {process.pid} (name unknown)")
                        
                    # Only kill non-node processes
                    if os.name == 'nt':  # Windows
                        subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                     capture_output=True)
                    else:  # Unix/Linux/MacOS
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except Exception as e:
                logger.error(f"Error cleaning up process: {e}")
                
        # Clear the processes list but keep node processes running
        non_node_processes = []
        for process in processes:
            try:
                if process.poll() is None:  # Process is still running
                    try:
                        proc = psutil.Process(process.pid)
                        process_name = proc.name().lower()
                        if 'node' in process_name or 'npm' in process_name or 'electron' in process_name:
                            logger.info(f"Keeping node process in tracked list: {process_name} (PID: {process.pid})")
                            non_node_processes.append(process)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception:
                pass
                
        # Update the processes list to only include node processes that are still running
        processes.clear()
        processes.extend(non_node_processes)
        
        logger.info(f"Process cleanup completed. {len(processes)} node processes preserved.")
    except Exception as e:
        logger.error(f"Error during process cleanup: {e}")

def signal_handler(signum, frame):
    """Handle cleanup on shutdown signals"""
    signal_names = {
        signal.SIGINT: "SIGINT (Ctrl+C)",
        signal.SIGTERM: "SIGTERM",
        signal.SIGABRT: "SIGABRT",
        signal.SIGBREAK: "SIGBREAK (Ctrl+Break)" if hasattr(signal, 'SIGBREAK') else "SIGBREAK"
    }
    signal_name = signal_names.get(signum, f"Unknown signal {signum}")
    
    # Get information about the parent process if possible
    parent_info = "Unknown"
    try:
        current_process = psutil.Process()
        parent = current_process.parent()
        if parent:
            parent_info = f"{parent.name()} (PID: {parent.pid})"
    except Exception as e:
        parent_info = f"Error getting parent: {str(e)}"
    
    logger.info(f"Shutdown signal {signal_name} received from {parent_info}, cleaning up...")
    cleanup_processes()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
if hasattr(signal, 'SIGBREAK'):  # Windows-specific
    signal.signal(signal.SIGBREAK, signal_handler)
signal.signal(signal.SIGABRT, signal_handler)

def cleanup_frontend_cache():
    """Clean up frontend build artifacts and cache"""
    try:
        logger.info("Cleaning up frontend cache and build artifacts...")
        frontend_dir = Path('frontend')
        
        # Directories to clean
        cleanup_dirs = [
            frontend_dir / 'dist',
            frontend_dir / '.vite',
            frontend_dir / 'node_modules/.vite',
            frontend_dir / 'node_modules/.cache'
        ]
        
        for dir_path in cleanup_dirs:
            if dir_path.exists():
                logger.info(f"Removing {dir_path}")
                shutil.rmtree(dir_path, ignore_errors=True)
                
        logger.info("Frontend cleanup completed")
        return True
    except Exception as e:
        logger.error(f"Frontend cleanup failed: {str(e)}")
        return False

def check_environment():
    """Check and log environment information"""
    try:
        logger.info("=== Environment Information ===")
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"Python version: {sys.version}")
        
        # Log PATH information
        logger.info("\n=== PATH Environment ===")
        logger.info(os.environ.get('PATH', 'PATH not found'))
        
        # Check Node.js and npm with shell=True
        try:
            node_version = subprocess.check_output('node --version', shell=True, stderr=subprocess.PIPE).decode().strip()
            npm_version = subprocess.check_output('npm --version', shell=True, stderr=subprocess.PIPE).decode().strip()
            logger.info(f"Node.js version: {node_version}")
            logger.info(f"npm version: {npm_version}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running Node.js: {e.stderr.decode()}")
            return False
        except Exception as e:
            logger.error(f"Error checking Node.js: {str(e)}")
            return False
            
        # Log installed Python packages
        logger.info("\n=== Installed Python Packages ===")
        installed_packages = [f"{dist.key} {dist.version}" for dist in pkg_resources.working_set]
        for package in installed_packages:
            logger.info(f"  {package}")
            
        return True
    except Exception as e:
        logger.error(f"Environment check failed: {str(e)}")
        return False

def check_required_files():
    """Check if all required configuration files exist"""
    try:
        logger.info("Checking required configuration files...")
        required_files = [
            Path('backend/.env'),
            Path('frontend/.env'),
            Path('requirements.txt'),
            Path('frontend/package.json')
        ]
        
        missing_files = [f for f in required_files if not f.exists()]
        if missing_files:
            logger.error(f"Missing required files: {', '.join(str(f) for f in missing_files)}")
            return False
            
        logger.info("All required configuration files present")
        return True
    except Exception as e:
        logger.error(f"Failed to check required files: {str(e)}")
        return False

def load_environment_variables():
    """Load environment variables from appropriate files"""
    try:
        # Load backend environment variables
        backend_env = Path('backend/.env')
        if backend_env.exists():
            load_dotenv(backend_env)
            logger.info("Loaded backend environment variables from backend/.env")
        else:
            logger.warning("Backend environment file not found at backend/.env")
        
        # Load frontend environment variables
        frontend_env = Path('frontend/.env')
        if frontend_env.exists():
            load_dotenv(frontend_env)
            logger.info("Loaded frontend environment variables")
        else:
            logger.warning("Frontend environment file not found at frontend/.env")
        
        # Set development environment variables
        os.environ['NODE_ENV'] = 'development'
        os.environ['FLASK_ENV'] = 'development'
        
        return True
    except Exception as e:
        logger.error(f"Failed to load environment variables: {str(e)}")
        return False

def install_dependencies():
    """Install Python and Node.js dependencies"""
    try:
        logger.info("Installing Python dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, shell=True)
        
        logger.info("Installing frontend dependencies...")
        os.chdir('frontend')
        subprocess.run(['npm', 'install'], shell=True, check=True)
        os.chdir('..')
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error installing dependencies: {str(e)}")
        return False

def build_frontend():
    """Build the frontend application"""
    try:
        logger.info("Building frontend...")
        os.chdir('frontend')
        subprocess.run(['npm', 'run', 'build'], shell=True, check=True)
        os.chdir('..')
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Frontend build failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error building frontend: {str(e)}")
        return False

def run_frontend():
    """Run the frontend development server with Electron"""
    try:
        # Get absolute paths
        root_dir = os.path.abspath(os.path.dirname(__file__))
        frontend_dir = os.path.join(root_dir, 'frontend')
        
        # Ensure we're in the root directory
        if not os.path.exists(frontend_dir):
            logger.error(f"Frontend directory not found at {frontend_dir}")
            return False
            
        # Change to frontend directory
        os.chdir(frontend_dir)
        logger.info(f"Changed to frontend directory: {frontend_dir}")
        
        # Set environment variables
        env = os.environ.copy()
        env['NODE_ENV'] = 'development'
        
        # Start the development server with Electron
        logger.info("Starting Electron development server...")
        process = subprocess.Popen(
            ['npm', 'run', 'electron:dev'],
            shell=True,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        processes.append(process)
        return True
    except Exception as e:
        logger.error(f"Frontend server failed: {str(e)}")
        return False
    finally:
        os.chdir(root_dir)  # Always return to root directory

def run_backend():
    """Run the backend server"""
    try:
        os.chdir('backend')
        logger.info("Starting backend server...")
        # Set up environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'wsgi:app'
        
        # Use python -m flask run to ensure proper module imports
        process = subprocess.Popen([
            sys.executable, '-m', 'flask', 'run',
            '--host=0.0.0.0',
            '--port=5000',
            '--no-debugger',  # Disable debugger when running with Electron
            '--no-reload'     # Disable reloader when running with Electron
        ], shell=True, env=env, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
        processes.append(process)
        return True
    except Exception as e:
        logger.error(f"Backend server failed: {str(e)}")
        return False
    finally:
        os.chdir('..')

def main():
    """Main development startup function"""
    try:
        # Initial cleanup - but preserve node processes
        cleanup_processes()
        if not cleanup_frontend_cache():
            logger.error("Failed to clean up frontend cache")
            return
            
        # Check environment and dependencies
        if not check_environment():
            logger.error("Environment check failed")
            return
            
        # Check required configuration files
        if not check_required_files():
            logger.error("Required files check failed")
            return
            
        # Install dependencies
        if not install_dependencies():
            logger.error("Failed to install dependencies")
            return
            
        # Load environment variables
        if not load_environment_variables():
            logger.error("Failed to load environment variables")
            return
            
        # Build frontend
        if not build_frontend():
            logger.error("Failed to build frontend")
            return
            
        # Start the backend server
        logger.info("Starting backend server...")
        if not run_backend():
            logger.error("Failed to start backend server")
            return
        
        # Wait for backend to initialize
        time.sleep(2)
        
        # Start the frontend with Electron
        logger.info("Starting frontend with Electron...")
        if not run_frontend():
            logger.error("Failed to start frontend")
            return
            
        # Keep the main thread alive
        while True:
            time.sleep(1)
            # Check if any process has terminated unexpectedly
            for process in processes[:]:  # Create a copy of the list to safely modify it
                if process.poll() is not None:
                    exit_code = process.poll()
                    
                    # Try to get process name
                    process_name = "Unknown"
                    try:
                        # This might fail if the process is already gone
                        proc = psutil.Process(process.pid)
                        process_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    
                    logger.warning(f"Process {process_name} (PID: {process.pid}) terminated with exit code {exit_code}")
                    
                    # Remove the terminated process from our tracking list
                    processes.remove(process)
                    
                    # Don't clean up other processes, especially node processes
                    logger.info("Not cleaning up other processes to preserve node/npm/electron processes")
                    
                    # If all processes have terminated, exit the loop
                    if not processes:
                        logger.info("All processes have terminated, exiting")
                        return
        
    except KeyboardInterrupt:
        logger.info("Development server shutdown requested")
    except Exception as e:
        logger.error(f"Development startup failed: {str(e)}")
    finally:
        logger.info("Shutting down development servers (preserving node processes)...")
        cleanup_processes()  # This will now preserve node processes

if __name__ == '__main__':
    main()
