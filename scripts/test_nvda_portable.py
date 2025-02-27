#!/usr/bin/env python3
"""
Script to test the NVDA portable installation with AT Automation plugin.
"""

import os
import sys
import time
import subprocess
import json
import socket
import logging

# Set up logging to a file instead of stdout
logging.basicConfig(
    filename='test_nvda_portable.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_nvda_portable(portable_path):
    """
    Test if the NVDA portable installation works with the AT Automation plugin.
    
    Args:
        portable_path (str): Path to the NVDA portable installation.
        
    Returns:
        bool: True if the test passes, False otherwise.
    """
    logging.info(f"Testing NVDA portable at {portable_path}")
    
    # Start the portable NVDA
    nvda_exe = os.path.join(portable_path, 'nvda.exe')
    logging.info(f"Starting NVDA from {nvda_exe} in minimal mode")
    
    try:
        subprocess.Popen([nvda_exe, "-m"])  # -m for minimal mode
        logging.info("Waiting for NVDA to start (15 seconds)")
        time.sleep(15)  # Give NVDA time to start
        
        # Test if AT Automation server is running on port 8765
        logging.info("Testing connection to AT Automation server on port 8765")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8765))
            sock.close()
            
            if result == 0:
                logging.info("AT Automation server is running!")
                success = True
            else:
                logging.error(f"AT Automation server is not running! Connection result: {result}")
                success = False
        except Exception as e:
            logging.error(f"Error testing connection: {str(e)}")
            success = False
        
        # Kill NVDA
        logging.info("Killing NVDA process")
        os.system('taskkill /f /im nvda.exe')
        time.sleep(2)
        
        return success
    except Exception as e:
        logging.error(f"Error during test: {str(e)}")
        # Make sure NVDA is killed even if there's an error
        try:
            os.system('taskkill /f /im nvda.exe')
        except:
            pass
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        error_msg = "Missing arguments. Usage: test_nvda_portable.py <portable_path>"
        logging.error(error_msg)
        print(json.dumps({"success": False, "error": error_msg}))
        sys.exit(1)
        
    portable_path = sys.argv[1]
    
    try:
        success = test_nvda_portable(portable_path)
        result = {"success": success}
        logging.info(f"Test result: {result}")
        print(json.dumps(result))
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Test failed with exception: {error_msg}")
        print(json.dumps({"success": False, "error": error_msg})) 