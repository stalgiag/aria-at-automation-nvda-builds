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
        # Run installer silently
        cmd = [installer_path, "--install", "--silent"]
        run_command(cmd)
        logging.info("NVDA installed successfully")
        
        # Give NVDA time to start and then kill it
        time.sleep(5)
        run_command(['taskkill', '/f', '/im', 'nvda.exe'], shell=True, check=False)
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
        
        # Get path to NVDA executable
        nvda_path = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'NVDA', 'nvda.exe')
        
        # Create portable copy using NVDA's built-in mechanism
        nvda_command = f'"{nvda_path}" --portable="{portable_path}" --minimal'
        logging.info(f"Creating portable copy: {nvda_command}")
        
        run_command([nvda_command], shell=True)
        
        # Wait for portable copy creation and verify
        max_wait = 30  # Maximum wait time in seconds
        wait_interval = 2  # Check every 2 seconds
        
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

if __name__ == "__main__":
    if len(sys.argv) < 4:
        error_msg = "Missing arguments. Usage: configure_nvda.py <installer_path> <addon_path> <version>"
        logging.error(error_msg)
        print(json.dumps({"success": False, "error": error_msg}))
        sys.exit(1)
        
    installer_path = sys.argv[1]
    addon_path = sys.argv[2]
    version = sys.argv[3]
    
    try:
        logging.info(f"Starting configuration with installer={installer_path}, addon={addon_path}, version={version}")
        
        # Install NVDA
        install_nvda(installer_path)
        
        # Install addon
        install_addon(addon_path)
        
        # Create portable copy
        result = create_portable_copy(version)
        
        # Output the result for GitHub Actions
        print(json.dumps(result))
        logging.info(f"Configuration successful: {result}")
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Configuration failed: {error_msg}")
        print(json.dumps({"success": False, "error": error_msg})) 