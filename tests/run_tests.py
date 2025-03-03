#!/usr/bin/env python3
"""
Test Runner for ZugaCloud Storj Integration Tests
This script organizes and runs all the tests related to Storj integration.
"""

import os
import sys
import logging
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test-runner")

# Define test categories and their corresponding test scripts
TEST_CATEGORIES = {
    "env": [
        "tests/aws/check_storj_env.py"
    ],
    "connection": [
        "tests/aws/test_direct_storj.py",
        "tests/aws/test_direct_bucket.py",
        "tests/aws/test_head_bucket.py"
    ],
    "client": [
        "tests/aws/test_storj_client.py"
    ],
    "frontend": [
        "tests/frontend/test_bucket_selector.js",
        "tests/frontend/test_storj_auto_detection.js"
    ],
    "server": [
        "tests/simple_server.py"
    ]
}

# Root directory
ROOT_DIR = Path(__file__).parent.parent

# Results directory
RESULTS_DIR = ROOT_DIR / "tests" / "results"

def setup_results_dir():
    """Create results directory if it doesn't exist"""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    logger.info(f"Results will be saved to: {RESULTS_DIR}")

def run_python_test(test_path, save_output=True):
    """Run a Python test script and optionally save the output"""
    test_name = Path(test_path).stem
    logger.info(f"Running test: {test_name}")
    
    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Log the result
        if result.returncode == 0:
            logger.info(f"✅ Test {test_name} passed")
        else:
            logger.error(f"❌ Test {test_name} failed with exit code {result.returncode}")
        
        # Save output if requested
        if save_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = RESULTS_DIR / f"{test_name}_{timestamp}.log"
            
            with open(output_file, "w") as f:
                f.write(f"=== STDOUT ===\n{result.stdout}\n\n=== STDERR ===\n{result.stderr}")
            
            logger.info(f"Output saved to: {output_file}")
        
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Error running test {test_name}: {e}")
        return False

def run_node_test(test_path, save_output=True):
    """Run a Node.js test script and optionally save the output"""
    test_name = Path(test_path).stem
    logger.info(f"Running test: {test_name}")
    
    try:
        # Run the test script
        result = subprocess.run(
            ["node", test_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Log the result
        if result.returncode == 0:
            logger.info(f"✅ Test {test_name} passed")
        else:
            logger.error(f"❌ Test {test_name} failed with exit code {result.returncode}")
        
        # Save output if requested
        if save_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = RESULTS_DIR / f"{test_name}_{timestamp}.log"
            
            with open(output_file, "w") as f:
                f.write(f"=== STDOUT ===\n{result.stdout}\n\n=== STDERR ===\n{result.stderr}")
            
            logger.info(f"Output saved to: {output_file}")
        
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Error running test {test_name}: {e}")
        return False

def run_server_test(test_path, timeout=5):
    """Run a server test script with a timeout"""
    test_name = Path(test_path).stem
    logger.info(f"Starting server: {test_name}")
    
    try:
        # Start the server
        server_process = subprocess.Popen(
            [sys.executable, test_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        logger.info(f"Waiting {timeout} seconds for server to start...")
        time.sleep(timeout)
        
        # Check if server is still running
        if server_process.poll() is None:
            logger.info(f"✅ Server {test_name} started successfully")
            
            # Return the process so it can be terminated later
            return server_process
        else:
            stdout, stderr = server_process.communicate()
            logger.error(f"❌ Server {test_name} failed to start")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error starting server {test_name}: {e}")
        return None

def run_tests(categories=None, save_output=True):
    """Run tests in the specified categories"""
    setup_results_dir()
    
    # If no categories specified, run all tests
    if not categories:
        categories = list(TEST_CATEGORIES.keys())
    
    # Track results
    results = {}
    server_process = None
    
    try:
        # Run tests in each category
        for category in categories:
            if category not in TEST_CATEGORIES:
                logger.warning(f"Unknown category: {category}")
                continue
                
            logger.info(f"\n=== Running {category} tests ===")
            category_results = []
            
            for test_path in TEST_CATEGORIES[category]:
                # Handle server tests differently
                if category == "server":
                    server_process = run_server_test(test_path)
                    category_results.append(server_process is not None)
                    continue
                
                # Run Python or Node.js tests
                if test_path.endswith(".py"):
                    result = run_python_test(test_path, save_output)
                elif test_path.endswith(".js"):
                    result = run_node_test(test_path, save_output)
                else:
                    logger.warning(f"Unknown test type: {test_path}")
                    continue
                    
                category_results.append(result)
            
            # Calculate category success rate
            success_count = sum(1 for result in category_results if result)
            total_count = len(category_results)
            success_rate = success_count / total_count if total_count > 0 else 0
            
            results[category] = {
                "success_count": success_count,
                "total_count": total_count,
                "success_rate": success_rate
            }
            
            logger.info(f"{category} tests: {success_count}/{total_count} passed ({success_rate:.0%})")
        
        # Print summary
        logger.info("\n=== Test Summary ===")
        for category, result in results.items():
            logger.info(f"{category}: {result['success_count']}/{result['total_count']} passed ({result['success_rate']:.0%})")
            
    finally:
        # Terminate server if it was started
        if server_process and server_process.poll() is None:
            logger.info("Terminating server...")
            server_process.terminate()
            server_process.wait()

def list_tests():
    """List all available tests"""
    logger.info("Available test categories:")
    
    for category, tests in TEST_CATEGORIES.items():
        logger.info(f"\n{category}:")
        for test in tests:
            logger.info(f"  - {test}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test Runner for ZugaCloud Storj Integration Tests")
    
    # Add arguments
    parser.add_argument("--list", action="store_true", help="List all available tests")
    parser.add_argument("--categories", nargs="+", help="Test categories to run")
    parser.add_argument("--no-save", action="store_true", help="Don't save test output")
    
    # Parse arguments
    args = parser.parse_args()
    
    # List tests if requested
    if args.list:
        list_tests()
        return
    
    # Run tests
    run_tests(args.categories, not args.no_save)

if __name__ == "__main__":
    main() 