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
import ctypes  # For elevation
from default_ini_content import get_default_ini_content
import datetime

# Set up logging to a file instead of stdout
logging.basicConfig(
    filename='configure_nvda.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def is_admin():
    """
    Check if the script is running with administrator privileges.
    
    Returns:
        bool: True if running as admin, False otherwise.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(f"Admin check failed: {e}")
        return False

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

def run_as_admin(executable, parameters):
    """
    Run a command with elevated privileges using ShellExecuteEx.

    Args:
        executable (str): Full path to the executable.
        parameters (str): Command-line arguments.

    Returns:
        int: The process's exit code once it finishes.

    Raises:
        Exception: If the elevated process cannot be started.
    """
    SW_SHOW = 5
    SEE_MASK_NOCLOSEPROCESS = 0x00000040

    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("fMask", ctypes.c_ulong),
            ("hwnd", ctypes.c_void_p),
            ("lpVerb", ctypes.c_wchar_p),
            ("lpFile", ctypes.c_wchar_p),
            ("lpParameters", ctypes.c_wchar_p),
            ("lpDirectory", ctypes.c_wchar_p),
            ("nShow", ctypes.c_int),
            ("hInstApp", ctypes.c_void_p),
            ("lpIDList", ctypes.c_void_p),
            ("lpClass", ctypes.c_wchar_p),
            ("hkeyClass", ctypes.c_void_p),
            ("dwHotKey", ctypes.c_ulong),
            ("hIcon", ctypes.c_void_p),
            ("hProcess", ctypes.c_void_p)
        ]
    
    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
    sei.fMask = SEE_MASK_NOCLOSEPROCESS
    sei.hwnd = None
    sei.lpVerb = "runas"  # Causes UAC elevation prompt if needed
    sei.lpFile = executable
    sei.lpParameters = parameters
    sei.lpDirectory = None
    sei.nShow = SW_SHOW
    sei.hInstApp = None

    if not ctypes.windll.shell32.ShellExecuteEx(ctypes.byref(sei)):
        raise Exception("Failed to execute process with elevated privileges. (ShellExecuteEx failed)")
    
    # Wait for the process to finish - 30 seconds timeout (30000 milliseconds)
    ret = ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 30000)
    if ret == 0x102:  # WAIT_TIMEOUT
        ctypes.windll.kernel32.TerminateProcess(sei.hProcess, 1)
        raise Exception("Elevated process timed out and was terminated")
    
    # Retrieve exit code
    exit_code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(exit_code))
    return exit_code.value

def install_nvda(installer_path):
    """Install NVDA silently.
    
    Args:
        installer_path (str): Path to the NVDA installer.
        
    Returns:
        str: Path to the installed nvda.exe
    """
    logging.info(f"Installing NVDA from {installer_path}")
    
    try:
        # Run installer silently
        cmd = [installer_path, "--install", "--silent"]
        run_command(cmd)
        logging.info("NVDA installed successfully")
        
        # NVDA installs to Program Files (x86) by default
        nvda_path = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'NVDA', 'nvda.exe')
        if not os.path.isfile(nvda_path):
            raise FileNotFoundError(f"NVDA executable not found at expected path: {nvda_path}")
            
        logging.info(f"NVDA installed at: {nvda_path}")
        
        # Give NVDA time to start and then kill it
        time.sleep(5)
        run_command(['taskkill', '/f', '/im', 'nvda.exe'], shell=True, check=False)
        
        return nvda_path
        
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

def create_portable_copy(version, nvda_path):
    """Create a portable copy of NVDA.
    
    Args:
        version (str): NVDA version for naming the portable copy.
        nvda_path (str): Path to the installed NVDA executable.
        
    Returns:
        dict: Result dictionary with success status and portable path
    """
    logging.info(f"Creating portable copy for version {version}")

    # Ensure administrator privileges – run_as_admin will fail if not
    if not is_admin():
        error_msg = "Administrator privileges are required to create a portable copy. Please run this script as an administrator."
        logging.error(error_msg)
        raise Exception(error_msg)
    
    try:
        # Create portable directory with version-specific name
        portable_path = os.path.join(os.getcwd(), f"nvda_{version}_portable")
        os.makedirs(portable_path, exist_ok=True)
        
        # Kill any existing NVDA processes
        run_command(['taskkill', '/f', '/im', 'nvda.exe'], shell=True, check=False)
        time.sleep(2)
        
        # Build the argument string for NVDA's portable mode.
        # Note: NVDA expects the portable directory via the --portable option.
        nvda_arguments = f'--portable="{portable_path}" --minimal'
        logging.info(f"Launching NVDA elevated with arguments: {nvda_arguments}")
        
        # Launch the process elevated using scheduled tasks instead of direct elevation
        task_name = "NVDA_Portable_Task"
        # Schedule the task to start one minute from now
        start_time = (datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime("%H:%M")
        create_task_cmd = f'schtasks /Create /SC ONCE /TN {task_name} /TR "\"{nvda_path}\" {nvda_arguments}" /RL HIGHEST /ST {start_time} /F'
        logging.info(f"Creating scheduled task with command: {create_task_cmd}")
        run_command(create_task_cmd, shell=True)
        task_name = "NVDA_Portable_Task"
        # Schedule the task to start one minute from now
        start_time = (datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime("%H:%M")
        # Wrap the command with cmd /c so that the executable path with spaces is parsed correctly.
        tr_command = f'cmd /c ""{nvda_path}" {nvda_arguments}"'
        create_task_cmd = f'schtasks /Create /SC ONCE /TN {task_name} /TR "{tr_command}" /RL HIGHEST /ST {start_time} /F'
        logging.info(f"Creating scheduled task with command: {create_task_cmd}")
        run_command(create_task_cmd, shell=True)

        run_task_cmd = f'schtasks /Run /TN {task_name}'
        logging.info(f"Running scheduled task with command: {run_task_cmd}")
        run_command(run_task_cmd, shell=True)

        # Optionally, delete the scheduled task
        delete_task_cmd = f'schtasks /Delete /TN {task_name} /F'
        logging.info(f"Deleting scheduled task with command: {delete_task_cmd}")
        run_command(delete_task_cmd, shell=True)

        # Wait for the portable copy to be created
        time.sleep(10)

        # Verify the portable copy was created
        if os.path.exists(os.path.join(portable_path, 'nvda.exe')):
            logging.info(f"Portable copy created successfully at: {portable_path}")
            
            # Clean up any running NVDA processes
            try:
                run_command(['taskkill', '/f', '/im', 'nvda.exe'], shell=True, check=False)
            except Exception:
                pass
                
            return {"success": True, "portable_path": portable_path}
        
        raise Exception("Portable copy was not created successfully")
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
        
        # Step 1: Install NVDA and get its path
        nvda_path = install_nvda(installer_path)
        
        # Step 2: Install addon
        install_addon(addon_path)
        
        # Step 3: Create portable copy
        result = create_portable_copy(version, nvda_path)
        
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