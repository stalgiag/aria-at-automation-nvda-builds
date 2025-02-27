#!/usr/bin/env python3
"""
Script to get the latest NVDA version from the official website.
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def get_latest_nvda_version():
    """
    Get the latest NVDA version and download URL from the official website.
    
    Returns:
        dict: A dictionary containing the version and download URL.
    """
    url = "https://www.nvaccess.org/download/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for the download link which contains the version
    download_link = soup.find('a', {'href': re.compile(r'.*NVDA.*\.exe$')})
    if download_link:
        href = download_link['href']
        # Extract version from URL
        match = re.search(r'NVDA_(\d+\.\d+(\.\d+)?)\.exe', href)
        if match:
            version = match.group(1)
            download_url = href
            return {"version": version, "url": download_url}
    
    return None

if __name__ == "__main__":
    result = get_latest_nvda_version()
    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "Could not find latest NVDA version"})) 