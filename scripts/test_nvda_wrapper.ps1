param(
    [Parameter(Mandatory=$true)]
    [string]$PortablePath
)

# Set up logging
$LogFile = "test_nvda_wrapper.log"
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -Append -FilePath $LogFile
}

Write-Log "Starting NVDA portable test with path: $PortablePath"

try {
    # Verify the portable path exists
    if (-not (Test-Path $PortablePath)) {
        throw "Portable path does not exist: $PortablePath"
    }
    
    $nvdaExe = Join-Path $PortablePath "nvda.exe"
    
    if (-not (Test-Path $nvdaExe)) {
        throw "NVDA executable not found at: $nvdaExe"
    }
    
    Write-Log "Found NVDA executable at: $nvdaExe"
    
    # Start NVDA portable in minimal mode
    Write-Log "Starting NVDA in minimal mode"
    try {
        Start-Process -FilePath $nvdaExe -ArgumentList "-m" -NoNewWindow
        Write-Log "NVDA process started"
    }
    catch {
        Write-Log "Error starting NVDA process: $_"
        throw "Failed to start NVDA: $_"
    }
    
    # Wait for NVDA to start
    Write-Log "Waiting for NVDA to start (15 seconds)"
    Start-Sleep -Seconds 15
    
    # Test if AT Automation server is running on port 8765
    Write-Log "Testing connection to AT Automation server on port 8765"
    $success = $false
    
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $portOpen = $tcpClient.ConnectAsync("127.0.0.1", 8765).Wait(5000)
        $tcpClient.Close()
        
        if ($portOpen) {
            Write-Log "AT Automation server is running!"
            $success = $true
        } else {
            Write-Log "AT Automation server is not running!"
            $success = $false
        }
    } catch {
        Write-Log "Error testing connection: $_"
        $success = $false
    }
    finally {
        # Always kill NVDA
        Write-Log "Killing NVDA process"
        Stop-Process -Name "nvda" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    
    # Return the result
    if ($success) {
        @{
            "success" = $true
            "message" = "NVDA portable test passed"
        } | ConvertTo-Json
    } else {
        @{
            "success" = $false
            "error" = "AT Automation server not detected on port 8765"
        } | ConvertTo-Json
    }
}
catch {
    Write-Log "Error during test: $_"
    
    # Make sure NVDA is killed even if there's an error
    Stop-Process -Name "nvda" -Force -ErrorAction SilentlyContinue
    
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
} 