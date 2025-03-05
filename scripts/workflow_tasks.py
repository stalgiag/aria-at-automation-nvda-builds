#!/usr/bin/env python3
"""
Centralized module for GitHub Actions workflow tasks.
"""

import os
import sys
import json
import shutil
import zipfile
import requests

def setup_python_path():
    """Add the workspace root to Python path."""
    workspace_dir = os.getcwd()
    if workspace_dir not in sys.path:
        sys.path.insert(0, workspace_dir)

def get_nvda_info(version=None):
    """Get NVDA version and download URL.
    
    Args:
        version (str, optional): Specific NVDA version to get. If None, gets latest.
        
    Returns:
        dict: Result with success status and NVDA info
    """
    setup_python_path()
    import scripts.get_latest_nvda as get_latest_nvda

    try:
        if not version:
            version = get_latest_nvda.get_latest_nvda_version()
        download_url = get_latest_nvda.get_nvda_download_url(version)
        
        nvda_info = {
            'version': version,
            'url': download_url
        }
        
        # Set environment variables
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"NVDA_VERSION={nvda_info['version']}\n")
            f.write(f"NVDA_DOWNLOAD_URL={nvda_info['url']}\n")
        
        print(f"NVDA version: {nvda_info['version']}")
        print(f"NVDA download URL: {nvda_info['url']}")
        
        return {"success": True, "nvda_info": nvda_info}
    except Exception as e:
        error_msg = f"Failed to get NVDA info: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"success": False, "error": error_msg}

def download_nvda_installer():
    """Download the NVDA installer.
    
    Returns:
        dict: Result with success status and installer path
    """
    try:
        print(f"Downloading from: {os.environ['NVDA_DOWNLOAD_URL']}")
        response = requests.get(os.environ['NVDA_DOWNLOAD_URL'])
        response.raise_for_status()
        
        installer_path = 'nvda_installer.exe'
        with open(installer_path, 'wb') as f:
            f.write(response.content)
        
        if not os.path.exists(installer_path) or os.path.getsize(installer_path) == 0:
            raise Exception("Downloaded file is empty or does not exist")
        
        print(f"NVDA installer downloaded successfully: {os.path.getsize(installer_path)} bytes")
        return {"success": True, "installer_path": installer_path}
    except Exception as e:
        error_msg = f"Failed to download NVDA installer: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"success": False, "error": error_msg}

def get_nvda_plugin():
    """Get the NVDA AT Automation Plugin.
    
    Returns:
        dict: Result with success status and plugin info
    """
    setup_python_path()
    import scripts.clone_nvda_plugin as clone_nvda_plugin

    try:
        result = clone_nvda_plugin.clone_nvda_plugin()
        if not result['success']:
            return result
        
        print(f"Plugin downloaded successfully to: {result['plugin_dir']}")
        
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"PLUGIN_DIR={result['plugin_dir']}\n")
            
        return result
    except Exception as e:
        error_msg = f"Failed to get NVDA plugin: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"success": False, "error": error_msg}

def create_plugin_addon():
    """Create the AT Automation Plugin addon.
    
    Returns:
        dict: Result with success status and addon path
    """
    try:
        # Navigate to the NVDAPlugin directory
        os.chdir('NVDAPlugin')
        addon_path = '../at-automation.nvda-addon'
        
        # Create the addon zip file directly from the contents
        with zipfile.ZipFile(addon_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk('.'):
                for file in files:
                    file_path = os.path.join(root, file)
                    archive_path = os.path.relpath(file_path, '.')
                    zipf.write(file_path, archive_path)
        
        print("AT Automation addon created successfully")
        return {"success": True, "addon_path": os.path.abspath(addon_path)}
    except Exception as e:
        error_msg = f"Failed to create addon: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"success": False, "error": error_msg}

def configure_nvda():
    """Configure NVDA and create portable copy.
    
    Returns:
        dict: Result with success status and portable path
    """
    setup_python_path()
    import scripts.configure_nvda as configure_nvda

    try:
        result = configure_nvda.create_portable_copy(os.environ['NVDA_VERSION'])
        if not result['success']:
            return result
            
        print(f"NVDA configured successfully")
        print(f"Portable path: {result['portable_path']}")
        
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"PORTABLE_PATH={result['portable_path']}\n")
            
        return result
    except Exception as e:
        error_msg = f"Failed to configure NVDA: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"success": False, "error": error_msg}

def test_nvda():
    """Test the NVDA portable installation.
    
    Returns:
        dict: Result with success status
    """
    setup_python_path()
    import scripts.test_nvda_portable as test_nvda_portable

    try:
        success = test_nvda_portable.test_nvda_portable(os.environ['PORTABLE_PATH'])
        if not success:
            return {"success": False, "error": "NVDA portable test failed"}
            
        print("NVDA portable test passed!")
        return {"success": True}
    except Exception as e:
        error_msg = f"Failed to test NVDA portable: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"success": False, "error": error_msg}

def package_nvda():
    """Package the NVDA portable installation.
    
    Returns:
        dict: Result with success status and package path
    """
    try:
        zip_path = f"{os.environ['NVDA_VERSION']}.zip"
        portable_path = os.environ['PORTABLE_PATH']
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(portable_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, portable_path)
                    zipf.write(file_path, arcname)
        
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"ZIP_PATH={zip_path}\n")
        
        print(f"NVDA portable packaged successfully: {zip_path}")
        return {"success": True, "zip_path": zip_path}
    except Exception as e:
        error_msg = f"Failed to package NVDA portable: {str(e)}"
        print(error_msg, file=sys.stderr)
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: workflow_tasks.py <task_name> [args...]", file=sys.stderr)
        sys.exit(1)

    task = sys.argv[1]
    args = sys.argv[2:]

    tasks = {
        'get_nvda_info': lambda: get_nvda_info(args[0] if args else None),
        'download_nvda_installer': download_nvda_installer,
        'get_nvda_plugin': get_nvda_plugin,
        'create_plugin_addon': create_plugin_addon,
        'configure_nvda': configure_nvda,
        'test_nvda': test_nvda,
        'package_nvda': package_nvda,
    }

    if task not in tasks:
        print(f"Unknown task: {task}", file=sys.stderr)
        print(f"Available tasks: {', '.join(tasks.keys())}", file=sys.stderr)
        sys.exit(1)

    result = tasks[task]()
    if not result['success']:
        print(result['error'], file=sys.stderr)
        sys.exit(1) 