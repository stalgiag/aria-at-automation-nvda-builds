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

def test_nvda_portable(portable_path):
    """
    Test if the NVDA portable installation works with the AT Automation plugin.
    
    Args:
        portable_path (str): Path to the NVDA portable installation.
        
    Returns:
        bool: True if the test passes, False otherwise.
    """
    # Start the portable NVDA
    nvda_exe = os.path.join(portable_path, 'nvda.exe')
    subprocess.Popen([nvda_exe, "-m"])  # -m for minimal mode
    time.sleep(15)  # Give NVDA time to start
    
    # Test if AT Automation server is running on port 8765
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8765))
        sock.close()
        
        if result == 0:
            print("AT Automation server is running!")
            success = True
        else:
            print("AT Automation server is not running!")
            success = False
    except Exception as e:
        print(f"Error testing connection: {str(e)}")
        success = False
    
    # Kill NVDA
    os.system('taskkill /f /im nvda.exe')
    time.sleep(2)
    
    return success

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Missing arguments. Usage: test_nvda_portable.py <portable_path>"}))
        sys.exit(1)
        
    portable_path = sys.argv[1]
    
    try:
        success = test_nvda_portable(portable_path)
        print(json.dumps({"success": success}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)})) 