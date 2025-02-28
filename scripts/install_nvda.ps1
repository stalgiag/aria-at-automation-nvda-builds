param(
    [Parameter(Mandatory=$true)]
    [string]$InstallerPath
)

# Set up logging
$LogFile = "install_nvda.log"
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -Append -FilePath $LogFile
}

Write-Log "Starting NVDA installation with installer: $InstallerPath"

try {
    # Check if installer exists
    if (-not (Test-Path $InstallerPath)) {
        throw "Installer not found at: $InstallerPath"
    }

    Write-Log "Running installer with silent install options"
    Write-Log "Using --install-silent flag instead of --install --silent"
    
    # Use a job to run the installer with a timeout
    $job = Start-Job -ScriptBlock {
        param($installerPath)
        Start-Process -FilePath $installerPath -ArgumentList "--install-silent" -Wait -NoNewWindow
    } -ArgumentList $InstallerPath
    
    # Wait for the job to complete with a timeout of 5 minutes
    $timeout = 300  # 5 minutes in seconds
    Write-Log "Waiting for installer to complete (timeout: $timeout seconds)"
    
    $completed = Wait-Job -Job $job -Timeout $timeout
    
    if ($completed -eq $null) {
        Write-Log "ERROR: Installation timed out after $timeout seconds"
        Stop-Job -Job $job
        Remove-Job -Job $job -Force
        throw "NVDA installation timed out after $timeout seconds"
    }
    
    # Get the job results
    $result = Receive-Job -Job $job
    Write-Log "Job completed with result: $result"
    Remove-Job -Job $job
    
    Write-Log "NVDA installation completed"
    
    # Since we're using --install-silent, NVDA should not start automatically
    # but let's check anyway
    Write-Log "Checking if NVDA is running (should not be with --install-silent)"
    $nvdaProcess = Get-Process -Name "nvda" -ErrorAction SilentlyContinue
    
    if ($nvdaProcess) {
        Write-Log "NVDA is running (unexpected), attempting to kill the process"
        try {
            Stop-Process -Name "nvda" -Force -ErrorAction Stop
            Write-Log "NVDA process killed successfully"
        }
        catch {
            Write-Log "Warning: Failed to kill NVDA process: $_"
            # Continue anyway since this is not critical
        }
    }
    else {
        Write-Log "NVDA process not found (expected behavior with --install-silent)"
    }
    
    # Check if NVDA was actually installed
    $nvdaPath = Join-Path ${env:ProgramFiles(x86)} "NVDA\nvda.exe"
    if (Test-Path $nvdaPath) {
        Write-Log "Successfully verified NVDA installation at: $nvdaPath"
        
        # Return success
        @{
            "success" = $true
            "message" = "NVDA installed successfully"
        } | ConvertTo-Json
    }
    else {
        throw "NVDA executable not found at expected location: $nvdaPath"
    }
}
catch {
    Write-Log "Error installing NVDA: $_"
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
} 