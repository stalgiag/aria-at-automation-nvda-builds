#!/usr/bin/env python3
"""
Script to clone the NVDA AT Automation Plugin from the repository.
"""

import os
import sys
import shutil
import tempfile
import subprocess
import json

def clone_nvda_plugin():
    """
    Clone the NVDA AT Automation Plugin from the repository.
    """
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Clone the repository
        repo_url = "https://github.com/Prime-Access-Consulting/nvda-at-automation.git"
        subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_dir], check=True)
        
        # Create NVDAPlugin directory in current directory
        nvda_plugin_dir = os.path.join(os.getcwd(), "NVDAPlugin")
        if os.path.exists(nvda_plugin_dir):
            shutil.rmtree(nvda_plugin_dir)
        
        # Copy the NVDAPlugin directory from the cloned repository
        source_plugin_dir = os.path.join(temp_dir, "NVDAPlugin")
        shutil.copytree(source_plugin_dir, nvda_plugin_dir)
        
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
        
        return {"success": True, "plugin_dir": nvda_plugin_dir}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = clone_nvda_plugin()
    print(json.dumps(result)) 