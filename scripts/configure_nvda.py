#!/usr/bin/env python3
"""
Script to install and configure NVDA with the AT Automation plugin.
"""

import os
import sys
import time
import subprocess
import json
from pywinauto.application import Application

def install_nvda(installer_path):
    """
    Install NVDA silently.
    
    Args:
        installer_path (str): Path to the NVDA installer.
    """
    # Run the installer silently
    subprocess.run([installer_path, "--install", "--silent"], check=True)
    print("NVDA installed successfully")
    
    # Wait for NVDA to start
    time.sleep(10)
    
    # Kill NVDA process after installation
    os.system('taskkill /f /im nvda.exe')
    time.sleep(2)

def install_addon(addon_path):
    """
    Install the AT Automation addon.
    
    Args:
        addon_path (str): Path to the addon file.
    """
    # Start NVDA
    nvda_path = os.path.join(os.environ['ProgramFiles(x86)'], 'NVDA', 'nvda.exe')
    subprocess.Popen([nvda_path])
    time.sleep(10)
    
    # Connect to NVDA
    app = Application(backend="uia").connect(path="nvda.exe")
    
    # Navigate to Tools -> Add-on store
    main_window = app.window(name="NVDA")
    main_window.menu_select("Tools->Add-on store...")
    time.sleep(2)
    
    # Click "Install from external source"
    addon_dialog = app.window(name="Add-on store")
    install_button = addon_dialog.child_window(title="Install from external source", control_type="Button")
    install_button.click()
    time.sleep(2)
    
    # Select the addon file
    file_dialog = app.window(name="Open")
    file_dialog.Edit.set_text(addon_path)
    file_dialog.Open.click()
    time.sleep(2)
    
    # Confirm installation
    confirm_dialog = app.window(name="Add-on Installation")
    confirm_dialog.child_window(title="Install", control_type="Button").click()
    time.sleep(5)
    
    # Restart NVDA
    restart_dialog = app.window(name="Add-on Installation")
    restart_dialog.child_window(title="Restart now", control_type="Button").click()
    time.sleep(10)
    
    print("Add-on installed successfully")

def configure_nvda_settings():
    """
    Configure NVDA settings:
    - Disable automatic update checking
    - Set synthesizer to Capture Speech
    """
    # Start NVDA
    nvda_path = os.path.join(os.environ['ProgramFiles(x86)'], 'NVDA', 'nvda.exe')
    subprocess.Popen([nvda_path])
    time.sleep(10)
    
    # Connect to NVDA
    app = Application(backend="uia").connect(path="nvda.exe")
    
    # Open preferences
    main_window = app.window(name="NVDA")
    main_window.menu_select("Preferences->Settings...")
    time.sleep(2)
    
    # Navigate to General category and disable update checking
    settings_dialog = app.window(name="Settings")
    
    # Find the General category
    general_item = settings_dialog.child_window(title="General", control_type="TreeItem")
    general_item.click_input()
    time.sleep(1)
    
    # Find and uncheck the update checkbox
    update_checkbox = settings_dialog.child_window(title="Automatically check for NVDA updates", control_type="CheckBox")
    if update_checkbox.get_toggle_state() == 1:  # If checked
        update_checkbox.click()
        time.sleep(1)
    
    # Navigate to Speech category
    speech_item = settings_dialog.child_window(title="Speech", control_type="TreeItem")
    speech_item.click_input()
    time.sleep(1)
    
    # Set synthesizer to Capture Speech
    synth_combo = settings_dialog.child_window(title="Synthesizer", control_type="ComboBox")
    synth_combo.select("Capture Speech")
    time.sleep(1)
    
    # Save settings
    settings_dialog.child_window(title="OK", control_type="Button").click()
    time.sleep(2)
    
    print("NVDA settings configured successfully")

def create_portable_copy(version):
    """
    Create a portable copy of NVDA.
    
    Args:
        version (str): NVDA version for naming the portable copy.
        
    Returns:
        str: Path to the portable copy.
    """
    # Start NVDA
    nvda_path = os.path.join(os.environ['ProgramFiles(x86)'], 'NVDA', 'nvda.exe')
    subprocess.Popen([nvda_path])
    time.sleep(10)
    
    # Connect to NVDA
    app = Application(backend="uia").connect(path="nvda.exe")
    
    # Navigate to Tools -> Create portable copy
    main_window = app.window(name="NVDA")
    main_window.menu_select("Tools->Create portable copy...")
    time.sleep(2)
    
    # Set the portable path
    portable_dialog = app.window(name="Create Portable Copy")
    portable_path = os.path.join(os.getcwd(), f"nvda_{version}_portable")
    portable_dialog.Edit.set_text(portable_path)
    
    # Click Continue
    portable_dialog.child_window(title="Continue", control_type="Button").click()
    time.sleep(10)
    
    # Confirm completion
    completion_dialog = app.window(name="Creating Portable Copy")
    completion_dialog.child_window(title="OK", control_type="Button").click()
    time.sleep(2)
    
    # Kill NVDA
    os.system('taskkill /f /im nvda.exe')
    time.sleep(2)
    
    print(f"Portable copy created at: {portable_path}")
    return portable_path

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"success": False, "error": "Missing arguments. Usage: configure_nvda.py <installer_path> <addon_path> <version>"}))
        sys.exit(1)
        
    installer_path = sys.argv[1]
    addon_path = sys.argv[2]
    version = sys.argv[3]
    
    try:
        install_nvda(installer_path)
        install_addon(addon_path)
        configure_nvda_settings()
        portable_path = create_portable_copy(version)
        
        # Output the result for GitHub Actions
        print(json.dumps({"success": True, "portable_path": portable_path}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)})) 