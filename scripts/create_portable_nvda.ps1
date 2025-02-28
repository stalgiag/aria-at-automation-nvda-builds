param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

# Set up logging
$LogFile = "create_portable_nvda.log"
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -Append -FilePath $LogFile
}

Write-Log "Starting to create portable NVDA for version: ${Version}"

try {
    # Create portable directory
    $portablePath = Join-Path $PWD "nvda_${Version}_portable"
    Write-Log "Creating portable directory: ${portablePath}"
    
    if (Test-Path $portablePath) {
        Write-Log "Removing existing portable directory"
        Remove-Item -Path $portablePath -Recurse -Force
    }
    
    New-Item -Path $portablePath -ItemType Directory -Force | Out-Null
    
    # Check if NVDA is installed
    $nvdaInstalledDir = Join-Path ${env:ProgramFiles(x86)} "NVDA"
    $nvdaExe = Join-Path $nvdaInstalledDir "nvda.exe"
    
    if (-not (Test-Path $nvdaExe)) {
        throw "NVDA not found at expected location: ${nvdaExe}"
    }
    
    Write-Log "NVDA found at: ${nvdaExe}"
    
    # Skip the built-in portable creation option as it requires admin rights
    Write-Log "Skipping NVDA's built-in portable creation (requires elevation)"
    Write-Log "Using manual copy method to create portable NVDA"
    
    try {
        # Copy all files from installed NVDA to portable directory
        Write-Log "Copying from ${nvdaInstalledDir} to ${portablePath}"
        
        # Use robocopy for more reliable copying
        Write-Log "Running robocopy to copy files"
        & robocopy $nvdaInstalledDir $portablePath /E /NFL /NDL /NJH /NJS /nc /ns /np
        $robocopyExitCode = $LASTEXITCODE
        
        # Interpret robocopy exit codes correctly
        # 0 = No files copied
        # 1 = Files copied successfully
        # 2-7 = Some files copied with additional info
        # 8+ = At least one failure
        if ($robocopyExitCode -lt 8) {
            Write-Log "Robocopy completed successfully with exit code: ${robocopyExitCode} (codes 0-7 indicate success)"
        } else {
            Write-Log "ERROR: Robocopy failed with exit code: ${robocopyExitCode}"
            throw "Robocopy failed with exit code ${robocopyExitCode}"
        }
        
        # Check for any NVDA process and kill it
        Write-Log "Checking for NVDA processes"
        Get-Process -Name "nvda" -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Log "Killing NVDA process with ID: $($_.Id)"
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
        
        # Create portable flag file
        $portableIni = Join-Path $portablePath "portable.ini"
        Write-Log "Creating portable flag file: $portableIni"
        Set-Content -Path $portableIni -Value "[portable]`n"
        
        # Create userConfig/addons directory structure
        $userConfigDir = Join-Path $portablePath "userConfig"
        $addonsDir = Join-Path $userConfigDir "addons"
        Write-Log "Creating userConfig/addons directory: $addonsDir"
        New-Item -Path $addonsDir -ItemType Directory -Force | Out-Null
        
        # Copy any installed NVDA addons to the portable installation
        $installedAddonsDir = Join-Path $env:APPDATA "nvda\addons"
        if (Test-Path $installedAddonsDir) {
            Write-Log "Copying addons from installed NVDA"
            
            # Get list of installed addons
            $addonDirs = Get-ChildItem -Path $installedAddonsDir -Directory
            
            foreach ($addonDir in $addonDirs) {
                $addonName = $addonDir.Name
                $sourcePath = $addonDir.FullName
                $destPath = Join-Path $addonsDir $addonName
                
                Write-Log "Copying addon: ${addonName}"
                try {
                    # Use robocopy for reliable copying
                    robocopy $sourcePath $destPath /E /NFL /NDL /NJH /NJS
                    
                    # Check if robocopy was successful (exit codes 0-7 indicate success)
                    if ($LASTEXITCODE -lt 8) {
                        Write-Log "Successfully copied addon: ${addonName}"
                    } else {
                        Write-Log "WARNING: Robocopy reported issues when copying addon: ${addonName} (Exit code: ${LASTEXITCODE})"
                        Write-Log "Trying alternative copy method"
                        Copy-Item -Path "$sourcePath\*" -Destination $destPath -Recurse -Force -ErrorAction SilentlyContinue
                    }
                } catch {
                    Write-Log "Error copying addon ${addonName}: $_"
                    # Continue with other addons - this is not critical
                }
            }
        } else {
            Write-Log "No installed addons directory found at: $installedAddonsDir"
        }
        
        # Specifically look for AT Automation addon
        $atAutomationDirs = Get-ChildItem -Path $addonsDir -Directory | Where-Object { $_.Name -match "CommandSocket" -or $_.Name -match "at-automation" }
        if ($atAutomationDirs) {
            Write-Log "AT Automation addon found in portable installation: ${atAutomationDirs.Name}"
        } else {
            Write-Log "WARNING: AT Automation addon not found in portable installation"
        }
        
        $portableExe = Join-Path $portablePath "nvda.exe"
        $portableCreated = Test-Path $portableExe
        if ($portableCreated) {
            Write-Log "Portable copy created successfully using manual method"
        } else {
            throw "Failed to create portable copy using manual method"
        }
    }
    catch {
        Write-Log "Error with manual copy method: $_"
        throw "Failed to create portable copy: $_"
    }
    
    # Verify the portable copy exists as final check
    if ($portableCreated) {
        # Return success with detailed information
        Write-Log "Successfully created portable NVDA"
        Write-Host "=========== PORTABLE CREATION SUCCESS =========="
        Write-Host "Portable path: ${portablePath}"
        
        @{
            "success" = $true
            "portable_path" = $portablePath
        } | ConvertTo-Json
    }
    else {
        throw "Failed to create portable copy of NVDA"
    }
}
catch {
    Write-Log "Error creating portable NVDA: $_"
    Write-Host "=========== PORTABLE CREATION FAILED =========="
    Write-Host "Error: $_"
    
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
} 