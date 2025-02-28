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
        throw "Addon file not found at: ${AddonPath}"
    }

    Write-Log "Addon file found: ${AddonPath} (Size: $((Get-Item $AddonPath).Length) bytes)"
    
    # Create addons directory if it doesn't exist
    $appdata = $env:APPDATA
    Write-Log "Using APPDATA directory: ${appdata}"
    
    $nvdaAddonsDir = Join-Path $appdata "nvda\addons"
    
    if (-not (Test-Path $nvdaAddonsDir)) {
        Write-Log "Creating addons directory: ${nvdaAddonsDir}"
        New-Item -Path $nvdaAddonsDir -ItemType Directory -Force | Out-Null
    }
    
    # Create a unique temporary directory
    $tempId = [Guid]::NewGuid().ToString()
    $tempDir = Join-Path $env:TEMP $tempId
    Write-Log "Creating temporary directory: ${tempDir}"
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
        Write-Log "Reading addon manifest: ${manifestPath}"
        $manifestContent = Get-Content $manifestPath -Raw -ErrorAction SilentlyContinue
        
        if ($manifestContent) {
            Write-Log "Manifest content found, looking for addon name"
            # Try to extract name from manifest
            if ($manifestContent -match '(?m)^name\s*=\s*(.+)$') {
                $addonName = $matches[1].Trim()
                Write-Log "Found addon name in manifest: ${addonName}"
                
                # Strip quotes from addon name if present
                $addonName = $addonName -replace '^"(.*)"$', '$1'
                $addonName = $addonName -replace "^'(.*)'$", '$1'
                Write-Log "Sanitized addon name for filesystem use: ${addonName}"
            }
            else {
                Write-Log "No name found in manifest, using default: ${addonName}"
            }
        }
        else {
            Write-Log "Manifest file is empty, using default name: ${addonName}"
        }
    }
    else {
        Write-Log "Manifest file not found, using default name: ${addonName}"
    }
    
    # Copy to NVDA addons directory
    $addonDest = Join-Path $nvdaAddonsDir $addonName
    
    # More aggressively check and remove existing addon
    if (Test-Path $addonDest) {
        Write-Log "Removing existing addon at: ${addonDest}"
        try {
            # Check if it's a file rather than a directory
            if (Test-Path $addonDest -PathType Leaf) {
                Write-Log "WARNING: Destination exists as a file, not a directory. Removing file."
                Remove-Item -Path $addonDest -Force -ErrorAction Stop
            } else {
                # For directories, make sure they're fully removed
                Write-Log "Removing existing addon directory"
                Remove-Item -Path $addonDest -Recurse -Force -ErrorAction Stop
            }
            
            # Verify it was actually removed
            if (Test-Path $addonDest) {
                Write-Log "WARNING: Failed to remove existing addon, trying again with robocopy"
                # Use robocopy to clear the directory (a common trick)
                $emptyDir = Join-Path $env:TEMP "empty_$([Guid]::NewGuid().ToString())"
                New-Item -Path $emptyDir -ItemType Directory -Force | Out-Null
                robocopy $emptyDir $addonDest /MIR /NFL /NDL /NJH /NJS | Out-Null
                Remove-Item -Path $emptyDir -Force -ErrorAction SilentlyContinue
                Remove-Item -Path $addonDest -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
        catch {
            Write-Log "Error removing existing addon: $_"
            # Continue anyway - we'll try to handle this later
        }
    }
    
    # Create fresh addon directory to avoid copying issues
    Write-Log "Creating fresh addon directory: ${addonDest}"
    try {
        if (Test-Path $addonDest) {
            Write-Log "WARNING: Destination still exists after attempted removal"
        } else {
            New-Item -Path $addonDest -ItemType Directory -Force | Out-Null
        }
    } catch {
        Write-Log "Error creating addon directory: $_"
        # Continue anyway - the copy might still work
    }
    
    # Copy the addon files - using robocopy for reliability
    Write-Log "Copying addon to destination: ${addonDest}"
    try {
        Write-Log "Trying primary copy method (robocopy)"
        $robocopyOutput = robocopy $tempDir $addonDest /E /NFL /NDL /NJH /NJS
        $robocopyExitCode = $LASTEXITCODE
        Write-Log "Robocopy completed with exit code: ${robocopyExitCode}"
        
        # Robocopy has special exit codes - codes 0-7 indicate success with varying levels of copying actions
        if ($robocopyExitCode -gt 7) {
            Write-Log "Robocopy reported errors, trying alternative copy method"
            Copy-Item -Path "$tempDir\*" -Destination $addonDest -Recurse -Force
        }
        
        Write-Log "Addon files copied successfully"
    }
    catch {
        Write-Log "Error copying addon files: $_"
        throw "Failed to copy addon files: $_"
    }
    
    # Verify the addon was successfully installed
    if (Test-Path $addonDest) {
        $installedFiles = Get-ChildItem -Path $addonDest -Recurse
        $fileCount = if ($installedFiles) { $installedFiles.Count } else { 0 }
        Write-Log "Verified addon installation: ${fileCount} files in ${addonDest}"
        
        if ($fileCount -eq 0) {
            throw "No files were copied to the addon destination"
        }
    }
    else {
        throw "Addon destination directory not found after installation"
    }
    
    # Clean up temp directory
    Write-Log "Cleaning up temporary directory"
    Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    
    # Also check for existing portable NVDA installations and install there if found
    # Look for portable NVDA in the workspace directory
    $potentialPortableLocations = @(
        "$PWD\nvda_*_portable", 
        "$env:USERPROFILE\nvda_*_portable"
    )
    
    foreach ($portablePattern in $potentialPortableLocations) {
        $portableDirs = Get-Item -Path $portablePattern -ErrorAction SilentlyContinue
        if ($portableDirs) {
            foreach ($portableDir in $portableDirs) {
                Write-Log "Found potential portable NVDA installation: ${portableDir.FullName}"
                $portableUserConfig = Join-Path $portableDir.FullName "userConfig"
                $portableAddonsDir = Join-Path $portableUserConfig "addons"
                
                # Create addons directory if it doesn't exist
                if (-not (Test-Path $portableAddonsDir)) {
                    Write-Log "Creating portable addons directory: ${portableAddonsDir}"
                    New-Item -Path $portableAddonsDir -ItemType Directory -Force | Out-Null
                }
                
                $portableAddonDest = Join-Path $portableAddonsDir $addonName
                
                # Remove existing addon
                if (Test-Path $portableAddonDest) {
                    Write-Log "Removing existing addon from portable installation: ${portableAddonDest}"
                    Remove-Item -Path $portableAddonDest -Recurse -Force -ErrorAction SilentlyContinue
                }
                
                # Copy addon to portable installation
                Write-Log "Copying addon to portable installation: ${portableAddonDest}"
                try {
                    $robocopyOutput = robocopy $tempDir $portableAddonDest /E /NFL /NDL /NJH /NJS
                    $robocopyExitCode = $LASTEXITCODE
                    
                    # Robocopy has special exit codes - codes 0-7 indicate success
                    if ($robocopyExitCode -le 7) {
                        Write-Log "Successfully installed addon to portable NVDA: ${portableAddonDest}"
                    } else {
                        Write-Log "Robocopy reported errors, trying alternative copy method"
                        Copy-Item -Path "$tempDir\*" -Destination $portableAddonDest -Recurse -Force -ErrorAction SilentlyContinue
                        
                        if (Test-Path $portableAddonDest) {
                            Write-Log "Successfully installed addon to portable NVDA using alternative method"
                        } else {
                            Write-Log "Failed to install addon to portable NVDA"
                        }
                    }
                } catch {
                    Write-Log "Error installing addon to portable NVDA: $_"
                    # Continue anyway - this is not critical for regular installation
                }
            }
        }
    }
    
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