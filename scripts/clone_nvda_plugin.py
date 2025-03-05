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
import logging

# Set up logging to a file instead of stdout
logging.basicConfig(
    filename='clone_nvda_plugin.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
            logging.info(f"Removing existing directory: {nvda_plugin_dir}")
            shutil.rmtree(nvda_plugin_dir)
        
        # Download the repository as a ZIP file
        repo_url = "https://github.com/Prime-Access-Consulting/nvda-at-automation/archive/refs/heads/main.zip"
        logging.info(f"Downloading repository from {repo_url}")
        
        response = requests.get(repo_url)
        if response.status_code != 200:
            error_msg = f"Failed to download repository: HTTP {response.status_code}"
            logging.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Extract the ZIP file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Create a temporary directory for extraction
            temp_dir = tempfile.mkdtemp()
            logging.info(f"Extracting to temporary directory: {temp_dir}")
            zip_ref.extractall(temp_dir)
            
            # Find the NVDAPlugin directory in the extracted files
            extracted_dir = os.path.join(temp_dir, "nvda-at-automation-main")
            source_plugin_dir = os.path.join(extracted_dir, "NVDAPlugin")
            
            if not os.path.exists(source_plugin_dir):
                error_msg = f"NVDAPlugin directory not found in the repository"
                logging.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Verify the expected structure
            required_files = [
                os.path.join(source_plugin_dir, "manifest.ini"),
                os.path.join(source_plugin_dir, "globalPlugins", "CommandSocket", "__init__.py"),
                os.path.join(source_plugin_dir, "synthDrivers", "captureSpeech", "__init__.py")
            ]
            
            for file_path in required_files:
                if not os.path.exists(file_path):
                    error_msg = f"Required file not found: {file_path}"
                    logging.error(error_msg)
                    return {"success": False, "error": error_msg}
            
            # Log the manifest content for debugging
            manifest_path = os.path.join(source_plugin_dir, "manifest.ini")
            with open(manifest_path, 'r') as f:
                manifest_content = f.read()
                logging.info(f"Manifest content:\n{manifest_content}")
            
            # Copy the NVDAPlugin directory
            logging.info(f"Copying from {source_plugin_dir} to {nvda_plugin_dir}")
            shutil.copytree(source_plugin_dir, nvda_plugin_dir)
            
            # Clean up the temporary directory
            logging.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
        
        logging.info(f"Successfully downloaded plugin to: {nvda_plugin_dir}")
        return {"success": True, "plugin_dir": nvda_plugin_dir}
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error: {error_msg}")
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    result = clone_nvda_plugin()
    # Only output the JSON result, nothing else
    print(json.dumps(result)) 