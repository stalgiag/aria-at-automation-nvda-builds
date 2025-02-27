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
import requests
import zipfile
import io

def clone_nvda_plugin():
    """
    Clone the NVDA AT Automation Plugin from the repository.
    
    Instead of using git clone, which can have permission issues in GitHub Actions,
    we'll download the repository as a ZIP file and extract it.
    """
    try:
        # Create NVDAPlugin directory in current directory
        nvda_plugin_dir = os.path.join(os.getcwd(), "NVDAPlugin")
        if os.path.exists(nvda_plugin_dir):
            shutil.rmtree(nvda_plugin_dir)
        
        # Download the repository as a ZIP file
        repo_url = "https://github.com/Prime-Access-Consulting/nvda-at-automation/archive/refs/heads/main.zip"
        print(f"Downloading repository from {repo_url}")
        
        response = requests.get(repo_url)
        if response.status_code != 200:
            return {"success": False, "error": f"Failed to download repository: HTTP {response.status_code}"}
        
        # Extract the ZIP file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Create a temporary directory for extraction
            temp_dir = tempfile.mkdtemp()
            zip_ref.extractall(temp_dir)
            
            # Find the NVDAPlugin directory in the extracted files
            extracted_dir = os.path.join(temp_dir, "nvda-at-automation-main")
            source_plugin_dir = os.path.join(extracted_dir, "NVDAPlugin")
            
            if not os.path.exists(source_plugin_dir):
                return {"success": False, "error": f"NVDAPlugin directory not found in the repository"}
            
            # Copy the NVDAPlugin directory
            shutil.copytree(source_plugin_dir, nvda_plugin_dir)
            
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
        
        return {"success": True, "plugin_dir": nvda_plugin_dir}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = clone_nvda_plugin()
    print(json.dumps(result)) 