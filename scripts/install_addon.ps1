param(
    [Parameter(Mandatory=$true)]
    [string]$AddonPath
)

# Set up logging
$LogFile = "install_addon.log"
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -Append -FilePath $LogFile
}

Write-Log "Starting addon installation from: $AddonPath"

try {
    # Verify the addon file exists
    if (-not (Test-Path $AddonPath)) {
        throw "Addon file not found at: $AddonPath"
    }

    Write-Log "Addon file found: $AddonPath (Size: $((Get-Item $AddonPath).Length) bytes)"
    
    # Create addons directory if it doesn't exist
    $appdata = $env:APPDATA
    Write-Log "Using APPDATA directory: $appdata"
    
    $nvdaAddonsDir = Join-Path $appdata "nvda\addons"
    
    if (-not (Test-Path $nvdaAddonsDir)) {
        Write-Log "Creating addons directory: $nvdaAddonsDir"
        New-Item -Path $nvdaAddonsDir -ItemType Directory -Force | Out-Null
    }
    
    # Create a unique temporary directory
    $tempId = [Guid]::NewGuid().ToString()
    $tempDir = Join-Path $env:TEMP $tempId
    Write-Log "Creating temporary directory: $tempDir"
    New-Item -Path $tempDir -ItemType Directory -Force | Out-Null
    
    # Extract the addon with error handling
    try {
        Write-Log "Extracting addon to temporary directory"
        Expand-Archive -Path $AddonPath -DestinationPath $tempDir -Force -ErrorAction Stop
        Write-Log "Addon extracted successfully"
    }
    catch {
        Write-Log "Error extracting addon: $_"
        throw "Failed to extract addon: $_"
    }
    
    # Verify the addon was successfully extracted
    $extractedFiles = Get-ChildItem -Path $tempDir -Recurse
    if ($extractedFiles.Count -eq 0) {
        throw "Addon extraction produced no files"
    }
    
    Write-Log "Found $($extractedFiles.Count) files in extracted addon"
    
    # Get the addon manifest to determine the addon name
    $manifestPath = Join-Path $tempDir "manifest.ini"
    $addonName = "atautomation"  # Default name
    
    if (Test-Path $manifestPath) {
        Write-Log "Reading addon manifest: $manifestPath"
        $manifestContent = Get-Content $manifestPath -Raw -ErrorAction SilentlyContinue
        
        if ($manifestContent) {
            Write-Log "Manifest content found, looking for addon name"
            # Try to extract name from manifest
            if ($manifestContent -match '(?m)^name\s*=\s*(.+)$') {
                $addonName = $matches[1].Trim()
                Write-Log "Found addon name in manifest: $addonName"
            }
            else {
                Write-Log "No name found in manifest, using default: $addonName"
            }
        }
        else {
            Write-Log "Manifest file is empty, using default name: $addonName"
        }
    }
    else {
        Write-Log "Manifest file not found, using default name: $addonName"
    }
    
    # Copy to NVDA addons directory
    $addonDest = Join-Path $nvdaAddonsDir $addonName
    
    # Remove existing addon if it exists
    if (Test-Path $addonDest) {
        Write-Log "Removing existing addon: $addonDest"
        Remove-Item -Path $addonDest -Recurse -Force -ErrorAction Stop
    }
    
    # Copy the addon files
    Write-Log "Copying addon to destination: $addonDest"
    try {
        Copy-Item -Path "$tempDir\*" -Destination $addonDest -Recurse -Force -ErrorAction Stop
        Write-Log "Addon files copied successfully"
    }
    catch {
        Write-Log "Error copying addon files: $_"
        throw "Failed to copy addon files: $_"
    }
    
    # Verify the addon was successfully installed
    if (Test-Path $addonDest) {
        $installedFiles = Get-ChildItem -Path $addonDest -Recurse
        Write-Log "Verified addon installation: $($installedFiles.Count) files in $addonDest"
    }
    else {
        throw "Addon destination directory not found after installation"
    }
    
    # Clean up temp directory
    Write-Log "Cleaning up temporary directory"
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Log "Addon installation completed successfully"
    
    # Return success
    @{
        "success" = $true
        "message" = "Addon installed successfully to $addonDest"
    } | ConvertTo-Json
}
catch {
    Write-Log "Error installing addon: $_"
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
} 