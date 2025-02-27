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
from pywinauto.application import Application
import ctypes

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

def run_elevated(cmd):
    """Run a command with elevated privileges using PowerShell."""
    logging.info(f"Running with elevation: {cmd}")
    
    # Create a PowerShell command to run the process with elevation
    ps_cmd = [
        "powershell.exe",
        "-Command",
        f"Start-Process -FilePath '{cmd[0]}' -ArgumentList '{' '.join(cmd[1:])}' -Wait"
    ]
    
    result = subprocess.run(ps_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Elevated process failed: {result.stderr}")
        raise Exception(f"Elevated process failed: {result.stderr}")
    
    return result

def install_nvda(installer_path):
    """
    Install NVDA silently.
    
    Args:
        installer_path (str): Path to the NVDA installer.
    """
    logging.info(f"Installing NVDA from {installer_path}")
    
    try:
        # Run the installer silently with appropriate privileges
        cmd = [installer_path, "--install", "--silent"]
        
        if is_admin():
            # We already have admin privileges
            subprocess.run(cmd, check=True)
        else:
            # Need to elevate
            run_elevated(cmd)
        
        logging.info("NVDA installed successfully")
        
        # Wait for NVDA to start
        logging.info("Waiting for NVDA to start")
        time.sleep(10)
        
        # Kill NVDA process after installation
        logging.info("Killing NVDA process")
        os.system('taskkill /f /im nvda.exe')
        time.sleep(2)
    except Exception as e:
        logging.error(f"Error installing NVDA: {str(e)}")
        raise

def install_addon(addon_path):
    """
    Install the AT Automation addon.
    
    Args:
        addon_path (str): Path to the addon file.
    """
    logging.info(f"Installing addon from {addon_path}")
    # Start NVDA
    nvda_path = os.path.join(os.environ['ProgramFiles(x86)'], 'NVDA', 'nvda.exe')
    logging.info(f"Starting NVDA from {nvda_path}")
    
    try:
        # Start NVDA with appropriate privileges
        if is_admin():
            # We already have admin privileges
            subprocess.Popen([nvda_path])
        else:
            # Use PowerShell to start NVDA
            ps_cmd = [
                "powershell.exe",
                "-Command",
                f"Start-Process -FilePath '{nvda_path}'"
            ]
            subprocess.run(ps_cmd)
        
        time.sleep(10)
        
        # Connect to NVDA
        logging.info("Connecting to NVDA")
        app = Application(backend="uia").connect(path="nvda.exe")
        
        # Navigate to Tools -> Add-on store
        logging.info("Navigating to Tools -> Add-on store")
        main_window = app.window(name="NVDA")
        main_window.menu_select("Tools->Add-on store...")
        time.sleep(2)
        
        # Click "Install from external source"
        logging.info("Clicking 'Install from external source'")
        addon_dialog = app.window(name="Add-on store")
        install_button = addon_dialog.child_window(title="Install from external source", control_type="Button")
        install_button.click()
        time.sleep(2)
        
        # Select the addon file
        logging.info(f"Selecting addon file: {addon_path}")
        file_dialog = app.window(name="Open")
        file_dialog.Edit.set_text(addon_path)
        file_dialog.Open.click()
        time.sleep(2)
        
        # Confirm installation
        logging.info("Confirming installation")
        confirm_dialog = app.window(name="Add-on Installation")
        confirm_dialog.child_window(title="Install", control_type="Button").click()
        time.sleep(5)
        
        # Restart NVDA
        logging.info("Restarting NVDA")
        restart_dialog = app.window(name="Add-on Installation")
        restart_dialog.child_window(title="Restart now", control_type="Button").click()
        time.sleep(10)
        
        logging.info("Add-on installed successfully")
    except Exception as e:
        logging.error(f"Error installing addon: {str(e)}")
        raise

def configure_nvda_settings():
    """
    Configure NVDA settings:
    - Disable automatic update checking
    - Set synthesizer to Capture Speech
    """
    logging.info("Configuring NVDA settings")
    # Start NVDA
    nvda_path = os.path.join(os.environ['ProgramFiles(x86)'], 'NVDA', 'nvda.exe')
    logging.info(f"Starting NVDA from {nvda_path}")
    
    try:
        # Start NVDA with appropriate privileges
        if is_admin():
            # We already have admin privileges
            subprocess.Popen([nvda_path])
        else:
            # Use PowerShell to start NVDA
            ps_cmd = [
                "powershell.exe",
                "-Command",
                f"Start-Process -FilePath '{nvda_path}'"
            ]
            subprocess.run(ps_cmd)
        
        time.sleep(10)
        
        # Connect to NVDA
        logging.info("Connecting to NVDA")
        app = Application(backend="uia").connect(path="nvda.exe")
        
        # Open preferences
        logging.info("Opening preferences")
        main_window = app.window(name="NVDA")
        main_window.menu_select("Preferences->Settings...")
        time.sleep(2)
        
        # Navigate to General category and disable update checking
        logging.info("Navigating to General category")
        settings_dialog = app.window(name="Settings")
        
        # Find the General category
        general_item = settings_dialog.child_window(title="General", control_type="TreeItem")
        general_item.click_input()
        time.sleep(1)
        
        # Find and uncheck the update checkbox
        logging.info("Disabling automatic updates")
        update_checkbox = settings_dialog.child_window(title="Automatically check for NVDA updates", control_type="CheckBox")
        if update_checkbox.get_toggle_state() == 1:  # If checked
            update_checkbox.click()
            time.sleep(1)
        
        # Navigate to Speech category
        logging.info("Navigating to Speech category")
        speech_item = settings_dialog.child_window(title="Speech", control_type="TreeItem")
        speech_item.click_input()
        time.sleep(1)
        
        # Set synthesizer to Capture Speech
        logging.info("Setting synthesizer to Capture Speech")
        synth_combo = settings_dialog.child_window(title="Synthesizer", control_type="ComboBox")
        synth_combo.select("Capture Speech")
        time.sleep(1)
        
        # Save settings
        logging.info("Saving settings")
        settings_dialog.child_window(title="OK", control_type="Button").click()
        time.sleep(2)
        
        logging.info("NVDA settings configured successfully")
    except Exception as e:
        logging.error(f"Error configuring settings: {str(e)}")
        raise

def create_portable_copy(version):
    """
    Create a portable copy of NVDA.
    
    Args:
        version (str): NVDA version for naming the portable copy.
        
    Returns:
        str: Path to the portable copy.
    """
    logging.info(f"Creating portable copy for version {version}")
    # Start NVDA
    nvda_path = os.path.join(os.environ['ProgramFiles(x86)'], 'NVDA', 'nvda.exe')
    logging.info(f"Starting NVDA from {nvda_path}")
    
    try:
        # Start NVDA with appropriate privileges
        if is_admin():
            # We already have admin privileges
            subprocess.Popen([nvda_path])
        else:
            # Use PowerShell to start NVDA
            ps_cmd = [
                "powershell.exe",
                "-Command",
                f"Start-Process -FilePath '{nvda_path}'"
            ]
            subprocess.run(ps_cmd)
        
        time.sleep(10)
        
        # Connect to NVDA
        logging.info("Connecting to NVDA")
        app = Application(backend="uia").connect(path="nvda.exe")
        
        # Navigate to Tools -> Create portable copy
        logging.info("Navigating to Tools -> Create portable copy")
        main_window = app.window(name="NVDA")
        main_window.menu_select("Tools->Create portable copy...")
        time.sleep(2)
        
        # Set the portable path
        portable_path = os.path.join(os.getcwd(), f"nvda_{version}_portable")
        logging.info(f"Setting portable path to {portable_path}")
        portable_dialog = app.window(name="Create Portable Copy")
        portable_dialog.Edit.set_text(portable_path)
        
        # Click Continue
        logging.info("Clicking Continue")
        portable_dialog.child_window(title="Continue", control_type="Button").click()
        time.sleep(10)
        
        # Confirm completion
        logging.info("Confirming completion")
        completion_dialog = app.window(name="Creating Portable Copy")
        completion_dialog.child_window(title="OK", control_type="Button").click()
        time.sleep(2)
        
        # Kill NVDA
        logging.info("Killing NVDA process")
        os.system('taskkill /f /im nvda.exe')
        time.sleep(2)
        
        logging.info(f"Portable copy created at: {portable_path}")
        return portable_path
    except Exception as e:
        logging.error(f"Error creating portable copy: {str(e)}")
        raise

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
        
        install_nvda(installer_path)
        install_addon(addon_path)
        configure_nvda_settings()
        portable_path = create_portable_copy(version)
        
        # Output the result for GitHub Actions
        result = {"success": True, "portable_path": portable_path}
        logging.info(f"Configuration successful: {result}")
        print(json.dumps(result))
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Configuration failed: {error_msg}")
        print(json.dumps({"success": False, "error": error_msg})) 