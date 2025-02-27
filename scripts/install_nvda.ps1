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
    # Install NVDA silently
    Write-Log "Running installer with silent install options"
    Start-Process -FilePath $InstallerPath -ArgumentList "--install", "--silent" -Wait -NoNewWindow
    
    Write-Log "NVDA installation completed successfully"
    
    # Wait for NVDA to start
    Write-Log "Waiting for NVDA to start"
    Start-Sleep -Seconds 10
    
    # Kill NVDA process
    Write-Log "Killing NVDA process"
    Stop-Process -Name "nvda" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Return success
    @{
        "success" = $true
        "message" = "NVDA installed successfully"
    } | ConvertTo-Json
}
catch {
    Write-Log "Error installing NVDA: $_"
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
} 