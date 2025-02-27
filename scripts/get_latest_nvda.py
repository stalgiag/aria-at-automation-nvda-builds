#!/usr/bin/env python3
"""
Script to get the latest NVDA version from the official download directory.
"""

import requests
import json
import sys
import re
from bs4 import BeautifulSoup

def get_latest_nvda_version():
    """
    Get the latest stable NVDA version by scraping the directory listing.
    
    Returns:
        str: The latest stable version (e.g., "2024.4.2")
    """
    url = "https://download.nvaccess.org/releases/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for the stable symlink which points to the latest stable version
    # Format is typically: "stable -> ././2024.4.2"
    stable_entry = None
    for line in response.text.splitlines():
        if "stable" in line and "->" in line:
            stable_entry = line
            break
    
    if stable_entry:
        # Extract the version from the symlink target
        match = re.search(r'stable\s+\\?->\s+\.?\.?/?\.?/?(\d+\.\d+\.\d+)', stable_entry)
        if match:
            return match.group(1)
    
    # If we couldn't find the stable symlink, look for the most recent version
    # The directory listing is typically sorted with newest versions at the top
    versions = []
    for line in response.text.splitlines():
        # Look for lines that start with a version number (YYYY.MM.DD)
        match = re.match(r'^(\d{4}\.\d+\.\d+)\s+', line)
        if match and "beta" not in line and "rc" not in line:
            versions.append(match.group(1))
    
    if versions:
        # Return the first (most recent) stable version
        return versions[0]
    
    # Fallback to a known version if we couldn't find any
    return "2024.4.2"

def get_nvda_download_url(version):
    """
    Get the NVDA download URL for a specific version.
    
    Args:
        version (str): NVDA version (e.g., "2024.4.2")
        
    Returns:
        str: The download URL
    """
    return f"https://download.nvaccess.org/releases/{version}/nvda_{version}.exe"

if __name__ == "__main__":
    # If a version is provided as an argument, use it
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        # Get the latest version from the directory listing
        version = get_latest_nvda_version()
    
    download_url = get_nvda_download_url(version)
    
    # Output the result as JSON
    result = {
        "version": version,
        "url": download_url
    }
    
    print(json.dumps(result)) 