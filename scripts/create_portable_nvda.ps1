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

Write-Log "Starting to create portable NVDA for version: $Version"

try {
    # Create portable directory
    $portablePath = Join-Path $PWD "nvda_${Version}_portable"
    Write-Log "Creating portable directory: $portablePath"
    
    if (Test-Path $portablePath) {
        Write-Log "Removing existing portable directory"
        Remove-Item -Path $portablePath -Recurse -Force
    }
    
    New-Item -Path $portablePath -ItemType Directory -Force | Out-Null
    
    # Method 1: Try to create portable copy using NVDA's --portable parameter
    try {
        $nvdaPath = Join-Path ${env:ProgramFiles(x86)} "NVDA\nvda.exe"
        Write-Log "NVDA path: $nvdaPath"
        
        # Create a shortcut that runs NVDA with the portable parameter
        $WshShell = New-Object -ComObject WScript.Shell
        $shortcutPath = Join-Path $env:TEMP "create_portable.lnk"
        $shortcut = $WshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $nvdaPath
        $shortcut.Arguments = "--portable=`"$portablePath`""
        $shortcut.Save()
        
        Write-Log "Created shortcut at: $shortcutPath"
        
        # Use explorer to run the shortcut (avoids UAC prompt)
        Write-Log "Running shortcut with explorer"
        Start-Process explorer.exe -ArgumentList $shortcutPath -Wait
        
        # Wait for portable copy to be created
        Write-Log "Waiting for portable copy to be created"
        Start-Sleep -Seconds 30
        
        # Kill any running NVDA processes
        Write-Log "Killing NVDA processes"
        Stop-Process -Name "nvda" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    catch {
        Write-Log "Error creating portable copy with shortcut: $_"
    }
    
    # Check if portable copy was created
    $portableExe = Join-Path $portablePath "nvda.exe"
    if (Test-Path $portableExe) {
        Write-Log "Portable copy created successfully at: $portablePath"
    }
    else {
        # Method 2: Manually copy installed NVDA to portable directory
        Write-Log "Portable copy not created via NVDA command. Using manual copy approach."
        
        $nvdaInstalledDir = Join-Path ${env:ProgramFiles(x86)} "NVDA"
        Write-Log "Copying from installed directory: $nvdaInstalledDir"
        
        # Copy all files from installed NVDA to portable directory
        Copy-Item -Path "$nvdaInstalledDir\*" -Destination $portablePath -Recurse -Force
        
        # Create portable flag file
        Set-Content -Path (Join-Path $portablePath "portable.ini") -Value "[portable]`n"
        
        Write-Log "Manual portable copy created at: $portablePath"
    }
    
    # Verify the portable copy exists
    if (Test-Path $portableExe) {
        # Return success
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
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
} 