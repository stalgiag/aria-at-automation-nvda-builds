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
    # Create addons directory if it doesn't exist
    $appdata = $env:APPDATA
    $nvdaAddonsDir = Join-Path $appdata "nvda\addons"
    
    if (-not (Test-Path $nvdaAddonsDir)) {
        Write-Log "Creating addons directory: $nvdaAddonsDir"
        New-Item -Path $nvdaAddonsDir -ItemType Directory -Force | Out-Null
    }
    
    # Extract addon to a temporary directory
    $tempDir = Join-Path $env:TEMP ([System.Guid]::NewGuid().ToString())
    Write-Log "Creating temporary directory: $tempDir"
    New-Item -Path $tempDir -ItemType Directory -Force | Out-Null
    
    # Extract the addon
    Write-Log "Extracting addon to temporary directory"
    Expand-Archive -Path $AddonPath -DestinationPath $tempDir -Force
    
    # Get the addon manifest to determine the addon name
    $manifestPath = Join-Path $tempDir "manifest.ini"
    $addonName = "atautomation"  # Default name
    
    if (Test-Path $manifestPath) {
        Write-Log "Reading addon manifest"
        $manifestContent = Get-Content $manifestPath -Raw
        
        # Try to extract name from manifest
        if ($manifestContent -match '(?m)^name\s*=\s*(.+)$') {
            $addonName = $matches[1].Trim()
            Write-Log "Found addon name in manifest: $addonName"
        }
    }
    
    # Copy to NVDA addons directory
    $addonDest = Join-Path $nvdaAddonsDir $addonName
    
    # Remove existing addon if it exists
    if (Test-Path $addonDest) {
        Write-Log "Removing existing addon: $addonDest"
        Remove-Item -Path $addonDest -Recurse -Force
    }
    
    # Copy the addon files
    Write-Log "Copying addon to destination: $addonDest"
    Copy-Item -Path $tempDir\* -Destination $addonDest -Recurse -Force
    
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