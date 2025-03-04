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
    """Get NVDA version and download URL."""
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
        
        print(f"NVDA_VERSION={nvda_info['version']}")
        print(f"NVDA_DOWNLOAD_URL={nvda_info['url']}")
        print(f"NVDA version: {nvda_info['version']}")
        print(f"NVDA download URL: {nvda_info['url']}")
        
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"NVDA_VERSION={nvda_info['version']}\n")
            f.write(f"NVDA_DOWNLOAD_URL={nvda_info['url']}\n")
    except Exception as e:
        print(f"Error getting NVDA info: {str(e)}", file=sys.stderr)
        sys.exit(1)

def download_nvda_installer():
    """Download the NVDA installer."""
    try:
        print(f"Downloading from: {os.environ['NVDA_DOWNLOAD_URL']}")
        response = requests.get(os.environ['NVDA_DOWNLOAD_URL'])
        response.raise_for_status()
        
        with open('nvda_installer.exe', 'wb') as f:
            f.write(response.content)
        
        if not os.path.exists('nvda_installer.exe') or os.path.getsize('nvda_installer.exe') == 0:
            raise Exception("Downloaded file is empty or does not exist")
        
        print(f"NVDA installer downloaded successfully: {os.path.getsize('nvda_installer.exe')} bytes")
    except Exception as e:
        print(f"Failed to download NVDA installer: {str(e)}", file=sys.stderr)
        sys.exit(1)

def get_nvda_plugin():
    """Get the NVDA AT Automation Plugin."""
    setup_python_path()
    import scripts.clone_nvda_plugin as clone_nvda_plugin

    try:
        result = clone_nvda_plugin.clone_nvda_plugin()
        if not result['success']:
            raise Exception(result['error'])
        
        print(f"Plugin downloaded successfully to: {result['plugin_dir']}")
        
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"PLUGIN_DIR={result['plugin_dir']}\n")
    except Exception as e:
        print(f"Error getting NVDA plugin: {str(e)}", file=sys.stderr)
        sys.exit(1)

def create_plugin_addon():
    """Create the AT Automation Plugin addon."""
    try:
        # Navigate to the NVDAPlugin directory
        os.chdir('NVDAPlugin')
        
        # Create a temporary directory for the addon
        os.makedirs('../temp_addon', exist_ok=True)
        
        # Copy all files to the temporary directory
        for root, dirs, files in os.walk('.'):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, '.')
                dst_path = os.path.join('../temp_addon', rel_path)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
        
        # Create the addon zip file
        os.chdir('../temp_addon')
        with zipfile.ZipFile('../at-automation.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk('.'):
                for file in files:
                    zipf.write(os.path.join(root, file))
        
        os.chdir('..')
        
        # Rename to .nvda-addon
        os.rename('at-automation.zip', 'at-automation.nvda-addon')
        print("AT Automation addon created successfully")
    except Exception as e:
        print(f"Error creating addon: {str(e)}", file=sys.stderr)
        sys.exit(1)

def configure_nvda():
    """Configure NVDA and create portable copy."""
    setup_python_path()
    import scripts.configure_nvda as configure_nvda

    try:
        # Install NVDA silently
        configure_nvda.install_nvda('nvda_installer.exe')
        
        # Configure NVDA using the alternative workflow (no GUI needed)
        if not configure_nvda.alternative_configure_workflow():
            raise Exception("Failed to configure NVDA")
        
        # Install the AT Automation addon
        if not configure_nvda.install_addon('at-automation.nvda-addon'):
            raise Exception("Failed to install addon")
        
        # Create portable copy
        result = configure_nvda.create_portable_copy(os.environ['NVDA_VERSION'])
        if not result['success']:
            raise Exception(result['error'])
        
        print(f"NVDA configured successfully")
        print(f"Portable path: {result['portable_path']}")
        
        with open(os.environ['GITHUB_ENV'], 'a') as f:
            f.write(f"PORTABLE_PATH={result['portable_path']}\n")
    except Exception as e:
        print(f"Error configuring NVDA: {str(e)}", file=sys.stderr)
        sys.exit(1)

def test_nvda():
    """Test the NVDA portable installation."""
    setup_python_path()
    import scripts.test_nvda_portable as test_nvda_portable

    try:
        success = test_nvda_portable.test_nvda_portable(os.environ['PORTABLE_PATH'])
        if not success:
            raise Exception("NVDA portable test failed")
        print("NVDA portable test passed!")
    except Exception as e:
        print(f"Error testing NVDA portable: {str(e)}", file=sys.stderr)
        sys.exit(1)

def package_nvda():
    """Package the NVDA portable installation."""
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
    except Exception as e:
        print(f"Error packaging NVDA portable: {str(e)}", file=sys.stderr)
        sys.exit(1)

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

    tasks[task]() 