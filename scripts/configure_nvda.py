#!/usr/bin/env python3
"""
Script to install and configure NVDA with the AT Automation plugin.
"""

import os
import sys
import time
import subprocess
import json
import logging
import shutil
from default_ini_content import get_default_ini_content

# Set up logging to a file instead of stdout
logging.basicConfig(
    filename='configure_nvda.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_command(cmd, shell=False, check=True):
    """Run a command and log its output without affecting stdout."""
    try:
        result = subprocess.run(
            cmd, 
            shell=shell, 
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logging.info(f"Command executed: {cmd}")
        logging.info(f"Return code: {result.returncode}")
        logging.info(f"Output: {result.stdout}")
        if result.stderr:
            logging.info(f"Error output: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error output: {e.stderr}")
        raise

def install_nvda(installer_path):
    """Install NVDA silently.
    
    Args:
        installer_path (str): Path to the NVDA installer.
    """
    logging.info(f"Installing NVDA from {installer_path}")
    
    try:
        # Run installer silently and capture output
        cmd = [installer_path, "--install", "--silent", "--debug-logging"]
        result = run_command(cmd)
        
        # Log the full installation details
        logging.info("Installation output:")
        logging.info(result.stdout)
        logging.info("Installation error output:")
        logging.info(result.stderr)
        
        # List contents of Program Files to see where NVDA might be
        program_files = [
            os.environ.get('ProgramFiles', 'C:\\Program Files'),
            os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
        ]
        
        for pf in program_files:
            logging.info(f"Checking contents of {pf}:")
            if os.path.exists(pf):
                contents = os.listdir(pf)
                logging.info(f"Contents: {contents}")
        
        # Give NVDA time to start and then kill it
        time.sleep(5)
        run_command(['taskkill', '/f', '/im', 'nvda.exe'], shell=True, check=False)
        
        # Try to find where NVDA was actually installed
        logging.info("Searching for nvda.exe in common locations...")
        for root, dirs, files in os.walk('C:\\'):
            if 'nvda.exe' in files:
                path = os.path.join(root, 'nvda.exe')
                logging.info(f"Found nvda.exe at: {path}")
                
    except Exception as e:
        logging.error(f"Error installing NVDA: {str(e)}")
        raise

def install_addon(addon_path):
    """Install the AT Automation addon.
    
    Args:
        addon_path (str): Path to the addon file.
    """
    logging.info(f"Installing addon from {addon_path}")
    
    try:
        # Create addons directory if it doesn't exist
        appdata = os.environ.get('APPDATA')
        nvda_addons_dir = os.path.join(appdata, 'nvda', 'addons')
        os.makedirs(nvda_addons_dir, exist_ok=True)
        
        # Copy the addon file to the addons directory
        addon_dest = os.path.join(nvda_addons_dir, os.path.basename(addon_path))
        shutil.copy2(addon_path, addon_dest)
        
        logging.info(f"Addon installed to {addon_dest}")
        return True
    except Exception as e:
        logging.error(f"Error installing addon: {str(e)}")
        raise

def find_nvda_exe():
    """Find the NVDA executable in common installation paths.
    
    Returns:
        str: Path to nvda.exe if found, otherwise raises an exception
    """
    possible_paths = [
        os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'NVDA', 'nvda.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'NVDA', 'nvda.exe'),
        os.path.join('C:\\Program Files', 'NVDA', 'nvda.exe'),
        os.path.join('C:\\Program Files (x86)', 'NVDA', 'nvda.exe'),
    ]
    
    for path in possible_paths:
        if os.path.isfile(path):
            logging.info(f"Found NVDA executable at: {path}")
            return path
            
    # If we get here, we couldn't find NVDA
    paths_checked = '\n'.join(f"- {p}" for p in possible_paths)
    raise FileNotFoundError(f"Could not find nvda.exe. Checked the following paths:\n{paths_checked}")

def create_portable_copy(version):
    """Create a portable copy of NVDA.
    
    Args:
        version (str): NVDA version for naming the portable copy.
        
    Returns:
        dict: Result dictionary with success status and portable path
    """
    logging.info(f"Creating portable copy for version {version}")
    
    try:
        
        # Create portable directory with version-specific name
        portable_path = os.path.join(os.getcwd(), f"nvda_{version}_portable")
        os.makedirs(portable_path, exist_ok=True)
        
        # Find NVDA executable
        try:
            nvda_path = find_nvda_exe()
        except FileNotFoundError as e:
            logging.error(str(e))
            return {"success": False, "error": str(e)}
        
        # Create portable copy using NVDA's built-in mechanism
        cmd = [
            nvda_path,
            "--portable=" + portable_path,
            "--minimal"
        ]
        logging.info(f"Creating portable copy with command: {cmd}")
        
        run_command(cmd, shell=False)
        
        # Wait for portable copy creation and verify
        max_wait = 30
        wait_interval = 2
        
        for _ in range(0, max_wait, wait_interval):
            if os.path.exists(os.path.join(portable_path, 'nvda.exe')):
                logging.info(f"Portable copy created successfully at: {portable_path}")
                
                # Clean up any running NVDA processes
                try:
                    run_command(['taskkill', '/f', '/im', 'nvda.exe'], shell=True, check=False)
                except:
                    pass
                    
                return {"success": True, "portable_path": portable_path}
            time.sleep(wait_interval)
        
        raise Exception("Timeout waiting for portable copy creation")
    except Exception as e:
        error_msg = f"Failed to create portable copy: {str(e)}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}

def setup_nvda(installer_path, addon_path, version):
    """Complete NVDA setup process: install, add addon, and create portable copy.
    
    Args:
        installer_path (str): Path to the NVDA installer
        addon_path (str): Path to the AT Automation addon
        version (str): NVDA version for naming the portable copy
        
    Returns:
        dict: Result with success status and portable path
    """
    try:
        logging.info(f"Starting NVDA setup with installer={installer_path}, addon={addon_path}, version={version}")
        
        # Step 1: Install NVDA
        install_nvda(installer_path)
        
        # Step 2: Install addon
        install_addon(addon_path)
        
        # Step 3: Create portable copy
        result = create_portable_copy(version)
        
        logging.info(f"NVDA setup completed: {result}")
        return result
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"NVDA setup failed: {error_msg}")
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    # This is now just for direct script usage/testing
    if len(sys.argv) < 4:
        error_msg = "Missing arguments. Usage: configure_nvda.py <installer_path> <addon_path> <version>"
        logging.error(error_msg)
        print(json.dumps({"success": False, "error": error_msg}))
        sys.exit(1)
        
    result = setup_nvda(
        installer_path=sys.argv[1],
        addon_path=sys.argv[2],
        version=sys.argv[3]
    )
    print(json.dumps(result)) 