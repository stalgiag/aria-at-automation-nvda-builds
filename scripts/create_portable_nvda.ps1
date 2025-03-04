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
    
    # First try using NVDA's built-in portable creation feature
    Write-Log "Attempting to use NVDA's built-in portable creation feature"
    
    # Create a temporary batch file to run NVDA with --portable parameter
    $tempBatPath = Join-Path $env:TEMP "create_portable_nvda.bat"
    Write-Log "Creating temporary batch file: $tempBatPath"
    
    $batContent = @"
@echo off
"$nvdaExe" --portable="$portablePath"
exit
"@
    
    Set-Content -Path $tempBatPath -Value $batContent
    
    # Run the batch file using explorer.exe to avoid elevation issues
    Write-Log "Running batch file with explorer.exe"
    Start-Process "explorer.exe" -ArgumentList $tempBatPath -Wait
    
    # Wait for NVDA to create the portable copy
    Write-Log "Waiting for NVDA to create portable copy..."
    Start-Sleep -Seconds 10
    
    # Check if NVDA is still running and kill it
    Write-Log "Checking for NVDA processes"
    Get-Process -Name "nvda" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Log "Killing NVDA process with ID: $($_.Id)"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    
    # Check if portable copy was created successfully
    $portableExe = Join-Path $portablePath "nvda.exe"
    $portableIniPath = Join-Path $portablePath "portable.ini"
    $libraryZipPath = Join-Path $portablePath "library.zip"
    
    $builtInMethodSucceeded = (Test-Path $portableExe) -and (Test-Path $portableIniPath) -and (Test-Path $libraryZipPath)
    
    if ($builtInMethodSucceeded) {
        Write-Log "Portable copy created successfully using NVDA's built-in feature"
    } else {
        Write-Log "NVDA's built-in portable creation failed or was incomplete. Falling back to manual copy method."
        
        # Clean up the incomplete portable directory
        if (Test-Path $portablePath) {
            Remove-Item -Path $portablePath -Recurse -Force
            New-Item -Path $portablePath -ItemType Directory -Force | Out-Null
        }
        
        # Use robocopy for more reliable copying
        Write-Log "Running robocopy to copy files from ${nvdaInstalledDir} to ${portablePath}"
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
        
        # Create portable flag file
        $portableIni = Join-Path $portablePath "portable.ini"
        Write-Log "Creating portable flag file: $portableIni"
        Set-Content -Path $portableIni -Value "[portable]`n"
        
        # Create userConfig/addons directory structure if it doesn't exist
        $userConfigDir = Join-Path $portablePath "userConfig"
        if (-not (Test-Path $userConfigDir)) {
            Write-Log "Creating userConfig directory: $userConfigDir"
            New-Item -Path $userConfigDir -ItemType Directory -Force | Out-Null
        }
        
        $addonsDir = Join-Path $userConfigDir "addons"
        if (-not (Test-Path $addonsDir)) {
            Write-Log "Creating addons directory: $addonsDir"
            New-Item -Path $addonsDir -ItemType Directory -Force | Out-Null
        }
        
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
    }
    
    # Specifically look for AT Automation addon
    $atAutomationDirs = Get-ChildItem -Path (Join-Path $portablePath "userConfig\addons") -Directory -ErrorAction SilentlyContinue | 
                        Where-Object { $_.Name -match "CommandSocket" -or $_.Name -match "at-automation" }
    
    if ($atAutomationDirs) {
        Write-Log "AT Automation addon found in portable installation: $($atAutomationDirs.Name)"
    } else {
        Write-Log "WARNING: AT Automation addon not found in portable installation"
        
        # Try to find the addon in the installed NVDA and copy it
        $installedAddonsDir = Join-Path $env:APPDATA "nvda\addons"
        $commandSocketDir = Get-ChildItem -Path $installedAddonsDir -Directory -ErrorAction SilentlyContinue | 
                           Where-Object { $_.Name -match "CommandSocket" -or $_.Name -match "at-automation" }
        
        if ($commandSocketDir) {
            Write-Log "Found CommandSocket addon in installed NVDA, copying to portable installation"
            $addonsDir = Join-Path $portablePath "userConfig\addons"
            
            # Ensure the addons directory exists
            if (-not (Test-Path $addonsDir)) {
                New-Item -Path $addonsDir -ItemType Directory -Force | Out-Null
            }
            
            $destPath = Join-Path $addonsDir $commandSocketDir.Name
            robocopy $commandSocketDir.FullName $destPath /E /NFL /NDL /NJH /NJS
            
            if ($LASTEXITCODE -lt 8) {
                Write-Log "Successfully copied CommandSocket addon to portable installation"
            } else {
                Write-Log "WARNING: Failed to copy CommandSocket addon to portable installation"
            }
        } else {
            Write-Log "CommandSocket addon not found in installed NVDA"
        }
    }
    
    # Verify the portable copy structure
    Write-Log "Verifying portable copy structure"
    
    # List of critical files that should be present in a valid NVDA portable installation
    $criticalFiles = @(
        "nvda.exe",
        "portable.ini",
        "library.zip",
        "synthDrivers",
        "locale",
        "userConfig"
    )
    
    $missingFiles = @()
    
    # Check for all critical files
    foreach ($file in $criticalFiles) {
        $filePath = Join-Path $portablePath $file
        if (-not (Test-Path $filePath)) {
            Write-Log "Missing critical file/directory: $file"
            $missingFiles += $file
        } else {
            Write-Log "Found critical file/directory: $file"
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Log "WARNING: Portable copy is missing critical files: $($missingFiles -join ', ')"
    } else {
        Write-Log "All critical files are present in the portable copy"
    }
    
    # Return success with detailed information
    Write-Log "Successfully created portable NVDA"
    Write-Host "=========== PORTABLE CREATION SUCCESS =========="
    Write-Host "Portable path: ${portablePath}"
    
    @{
        "success" = $true
        "portable_path" = $portablePath
    } | ConvertTo-Json
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