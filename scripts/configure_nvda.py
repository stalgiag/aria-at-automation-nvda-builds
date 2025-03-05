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
import ctypes
import tempfile
import shutil
from default_ini_content import get_default_ini_content

# Set up logging to a file instead of stdout
logging.basicConfig(
    filename='configure_nvda.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_command(cmd, shell=False, check=True):
    """Run a command and log its output without affecting stdout."""
    try:
        # Use subprocess with PIPE to avoid mixing output with our JSON
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
    """
    Install NVDA silently.
    
    Args:
        installer_path (str): Path to the NVDA installer.
    """
    logging.info(f"Installing NVDA from {installer_path}")
    
    try:
        # Run the installer directly - GitHub Actions runners should have sufficient privileges
        cmd = [installer_path, "--install", "--silent"]
        run_command(cmd)
        
        logging.info("NVDA installed successfully")
        
        # Wait for NVDA to start
        logging.info("Waiting for NVDA to start")
        time.sleep(10)
        
        # Kill NVDA process after installation
        logging.info("Killing NVDA process")
        run_command(['taskkill', '/f', '/im', 'nvda.exe'], shell=True)
        time.sleep(2)
    except Exception as e:
        logging.error(f"Error installing NVDA: {str(e)}")
        raise

def create_shortcut_to_nvda():
    """Create a shortcut to NVDA that doesn't require elevation."""
    logging.info("Creating a shortcut to NVDA")
    nvda_path = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'NVDA', 'nvda.exe')
    shortcut_path = os.path.join(tempfile.gettempdir(), 'nvda_shortcut.lnk')
    
    # Create PowerShell script to create shortcut
    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{nvda_path}"
    $Shortcut.Save()
    """
    
    # Save script to temp file
    ps_script_path = os.path.join(tempfile.gettempdir(), 'create_shortcut.ps1')
    with open(ps_script_path, 'w') as f:
        f.write(ps_script)
    
    # Run PowerShell script
    run_command(['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_script_path])
    
    # Check if shortcut was created
    if os.path.exists(shortcut_path):
        logging.info(f"Shortcut created at {shortcut_path}")
        return shortcut_path
    else:
        raise Exception("Failed to create NVDA shortcut")

def start_nvda_without_elevation():
    """Start NVDA without requiring elevation."""
    logging.info("Starting NVDA without elevation")
    
    # Method 1: Try using explorer.exe to start NVDA
    nvda_path = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'NVDA', 'nvda.exe')
    
    try:
        # This approach uses explorer.exe to start NVDA which should bypass UAC
        run_command(['explorer.exe', nvda_path])
        logging.info("Started NVDA using explorer.exe")
        time.sleep(10)
        return True
    except Exception as e:
        logging.warning(f"Failed to start NVDA using explorer.exe: {str(e)}")
    
    # Method 2: Try using a shortcut
    try:
        shortcut_path = create_shortcut_to_nvda()
        run_command(['explorer.exe', shortcut_path])
        logging.info("Started NVDA using shortcut")
        time.sleep(10)
        return True
    except Exception as e:
        logging.warning(f"Failed to start NVDA using shortcut: {str(e)}")
    
    # Method 3: Create a temporary copy of NVDA
    try:
        nvda_dir = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'NVDA')
        temp_nvda_dir = os.path.join(tempfile.gettempdir(), 'nvda_temp')
        
        # Create temp directory if it doesn't exist
        if not os.path.exists(temp_nvda_dir):
            os.makedirs(temp_nvda_dir)
            
        # Copy NVDA.exe and necessary DLLs
        shutil.copy2(os.path.join(nvda_dir, 'nvda.exe'), os.path.join(temp_nvda_dir, 'nvda.exe'))
        
        # Try to copy important DLLs
        for dll in ['nvdaHelperRemote.dll', 'nvdaControllerClient.dll']:
            dll_path = os.path.join(nvda_dir, dll)
            if os.path.exists(dll_path):
                shutil.copy2(dll_path, os.path.join(temp_nvda_dir, dll))
        
        # Run the copied NVDA
        run_command([os.path.join(temp_nvda_dir, 'nvda.exe')])
        logging.info("Started NVDA from temporary copy")
        time.sleep(10)
        return True
    except Exception as e:
        logging.warning(f"Failed to start NVDA from temporary copy: {str(e)}")
    
    # Method 4: Use runas with /savecred (only works if credentials were saved before)
    try:
        run_command(['runas', '/savecred', f'"{nvda_path}"'])
        logging.info("Started NVDA using runas with /savecred")
        time.sleep(10)
        return True
    except Exception as e:
        logging.warning(f"Failed to start NVDA using runas: {str(e)}")
    
    # If all methods fail
    logging.error("All methods to start NVDA without elevation failed")
    return False

def install_addon(addon_path):
    """
    Install the AT Automation addon.
    
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
    """
    Create a portable copy of NVDA using NVDA's built-in portable copy mechanism.
    
    Args:
        version (str): NVDA version for naming the portable copy.
        
    Returns:
        dict: Result dictionary with success status and portable path
    """
    logging.info(f"Creating portable copy for version {version}")
    
    try:
        # Create portable directory
        portable_path = os.path.join(os.getcwd(), f"nvda_{version}_portable")
        os.makedirs(portable_path, exist_ok=True)
        
        # Get path to NVDA executable
        nvda_path = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'NVDA', 'nvda.exe')
        
        # Run NVDA with administrative privileges directly
        nvda_command = f'"{nvda_path}" --portable="{portable_path}" --minimal'
        logging.info(f"Running command with admin rights: {nvda_command}")
        
        # Note: In GitHub Actions, the runneradmin account should already have admin privileges
        run_command([nvda_command], shell=True)
        
        # Give it some time to complete
        time.sleep(15)
        
        # Kill any remaining NVDA processes
        try:
            run_command(['taskkill', '/f', '/im', 'nvda.exe'], shell=True, check=False)
        except:
            pass
        
        # Verify portable copy was created
        if os.path.exists(os.path.join(portable_path, 'nvda.exe')):
            logging.info(f"Portable copy created at: {portable_path}")
            return {"success": True, "portable_path": portable_path}
        else:
            error_msg = "Failed to create portable copy using NVDA's built-in mechanism"
            logging.error(error_msg)
            return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error creating portable copy: {error_msg}")
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
        
        # Check if we're running as admin
        admin_status = "admin" if is_admin() else "non-admin"
        logging.info(f"Running with {admin_status} privileges")
        
        # Step 1: Install NVDA (this works fine based on logs)
        install_nvda(installer_path)
        
        # Install addon without using GUI
        install_addon(addon_path)
        
        # Create portable copy without using GUI
        result = create_portable_copy(version)
        
        # Output the result for GitHub Actions - ONLY output JSON here
        print(json.dumps(result))
        logging.info(f"Configuration successful: {result}")
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Configuration failed: {error_msg}")
        print(json.dumps({"success": False, "error": error_msg})) 