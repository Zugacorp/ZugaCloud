#!/usr/bin/env python3
"""
Test Report Generator for ZugaCloud Storj Integration Tests
This script generates a summary report of all test results.
"""

import os
import sys
import logging
import argparse
import glob
import re
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("report-generator")

# Root directory
ROOT_DIR = Path(__file__).parent.parent

# Results directory
RESULTS_DIR = ROOT_DIR / "tests" / "results"

# Report directory
REPORT_DIR = ROOT_DIR / "tests" / "reports"

def setup_report_dir():
    """Create report directory if it doesn't exist"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    logger.info(f"Reports will be saved to: {REPORT_DIR}")

def parse_test_log(log_file):
    """Parse a test log file and extract relevant information"""
    try:
        with open(log_file, "r") as f:
            content = f.read()
            
        # Extract test name from filename
        test_name = Path(log_file).stem
        test_name = re.sub(r'_\d{8}_\d{6}$', '', test_name)  # Remove timestamp
        
        # Determine test result
        if "✅" in content or "SUCCESS" in content:
            result = "PASS"
        elif "❌" in content or "FAILED" in content or "ERROR" in content:
            result = "FAIL"
        else:
            result = "UNKNOWN"
            
        # Extract timestamp from filename
        timestamp_match = re.search(r'_(\d{8}_\d{6})\.log$', str(log_file))
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        else:
            timestamp = datetime.fromtimestamp(os.path.getmtime(log_file))
            
        # Extract error messages
        error_messages = []
        for line in content.split("\n"):
            if "ERROR" in line or "❌" in line:
                error_messages.append(line.strip())
                
        # Extract success messages
        success_messages = []
        for line in content.split("\n"):
            if "SUCCESS" in line or "✅" in line:
                success_messages.append(line.strip())
                
        return {
            "test_name": test_name,
            "result": result,
            "timestamp": timestamp.isoformat(),
            "error_messages": error_messages,
            "success_messages": success_messages,
            "log_file": str(log_file)
        }
        
    except Exception as e:
        logger.error(f"Error parsing log file {log_file}: {e}")
        return None

def generate_report(output_format="text"):
    """Generate a report of all test results"""
    setup_report_dir()
    
    # Find all log files
    log_files = glob.glob(str(RESULTS_DIR / "*.log"))
    
    if not log_files:
        logger.warning("No test logs found in results directory")
        return
        
    logger.info(f"Found {len(log_files)} test logs")
    
    # Parse log files
    test_results = []
    for log_file in log_files:
        result = parse_test_log(log_file)
        if result:
            test_results.append(result)
            
    # Sort by timestamp (newest first)
    test_results.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Group by test name (keep only the latest result for each test)
    latest_results = {}
    for result in test_results:
        test_name = result["test_name"]
        if test_name not in latest_results:
            latest_results[test_name] = result
            
    # Calculate statistics
    total_tests = len(latest_results)
    passed_tests = sum(1 for result in latest_results.values() if result["result"] == "PASS")
    failed_tests = sum(1 for result in latest_results.values() if result["result"] == "FAIL")
    unknown_tests = sum(1 for result in latest_results.values() if result["result"] == "UNKNOWN")
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_format == "json":
        # JSON report
        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "unknown_tests": unknown_tests,
                "pass_rate": passed_tests / total_tests if total_tests > 0 else 0
            },
            "test_results": list(latest_results.values())
        }
        
        report_file = REPORT_DIR / f"test_report_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"JSON report saved to: {report_file}")
        
    else:
        # Text report
        report_lines = [
            "# ZugaCloud Storj Integration Test Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"Total Tests: {total_tests}",
            f"Passed: {passed_tests} ({passed_tests / total_tests:.0%})",
            f"Failed: {failed_tests} ({failed_tests / total_tests:.0%})",
            f"Unknown: {unknown_tests} ({unknown_tests / total_tests:.0%})",
            "",
            "## Test Results",
            ""
        ]
        
        # Add test results
        for test_name, result in latest_results.items():
            report_lines.append(f"### {test_name}")
            report_lines.append(f"Result: {result['result']}")
            report_lines.append(f"Timestamp: {result['timestamp']}")
            
            if result["error_messages"]:
                report_lines.append("Error Messages:")
                for message in result["error_messages"]:
                    report_lines.append(f"- {message}")
                    
            if result["success_messages"]:
                report_lines.append("Success Messages:")
                for message in result["success_messages"]:
                    report_lines.append(f"- {message}")
                    
            report_lines.append("")
            
        report_file = REPORT_DIR / f"test_report_{timestamp}.md"
        with open(report_file, "w") as f:
            f.write("\n".join(report_lines))
            
        logger.info(f"Text report saved to: {report_file}")
        
    return report_file

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test Report Generator for ZugaCloud Storj Integration Tests")
    
    # Add arguments
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Generate report
    generate_report(args.format)

if __name__ == "__main__":
    main() 