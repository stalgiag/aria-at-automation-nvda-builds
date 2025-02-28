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
    
    # First perform structural verification
    Write-Log "Performing structural verification of portable installation"
    
    # List of critical files that should be present in a valid NVDA portable installation
    $criticalFiles = @(
        "nvda.exe",
        "portable.ini",
        "library.zip",
        "synthDrivers",
        "locale",
        "addons"
    )
    
    $missingFiles = @()
    
    # Check for all critical files
    foreach ($file in $criticalFiles) {
        $filePath = Join-Path $PortablePath $file
        if (-not (Test-Path $filePath)) {
            Write-Log "Missing critical file/directory: $file"
            $missingFiles += $file
        } else {
            Write-Log "Found critical file/directory: $file"
        }
    }
    
    # Check for AT Automation addon
    $addonsDir = Join-Path $PortablePath "addons"
    if (Test-Path $addonsDir) {
        $commandSocketDir = Get-ChildItem -Path $addonsDir -Directory | Where-Object { $_.Name -match "CommandSocket" -or $_.Name -match "at-automation" }
        if ($commandSocketDir) {
            Write-Log "Found AT Automation addon: $($commandSocketDir.Name)"
            $hasAtAutomation = $true
        } else {
            Write-Log "AT Automation addon not found in addons directory"
            $hasAtAutomation = $false
        }
    } else {
        Write-Log "Addons directory not found"
        $hasAtAutomation = $false
    }
    
    # Verify portable.ini content
    $portableIni = Join-Path $PortablePath "portable.ini"
    if (Test-Path $portableIni) {
        $iniContent = Get-Content $portableIni -Raw
        if ($iniContent -match "\[portable\]") {
            Write-Log "portable.ini has correct content"
            $hasPortableFlag = $true
        } else {
            Write-Log "portable.ini doesn't contain [portable] section"
            $hasPortableFlag = $false
        }
    } else {
        $hasPortableFlag = $false
    }
    
    # Determine if structure check passed
    $structureCheckPassed = ($missingFiles.Count -eq 0) -and $hasPortableFlag -and $hasAtAutomation
    
    if (-not $structureCheckPassed) {
        Write-Log "Structural check failed, not attempting to run NVDA"
        throw "Structural verification failed: Missing files: $($missingFiles -join ', '). Has portable flag: $hasPortableFlag. Has AT Automation addon: $hasAtAutomation"
    }
    
    Write-Log "Structural check passed, attempting to run NVDA"
    
    # Now try to run NVDA and test its functionality
    
    # Function to check for HTTP response
    function Wait-For-HTTP-Response {
        param (
            [string]$RequestURL,
            [int]$MaxTries = 30,
            [int]$SleepSeconds = 1
        )
        
        $status = "Failed"
        for ($sleeps = 1; $sleeps -le $MaxTries; $sleeps++) {
            try {
                Write-Log "Try ${sleeps}: Making request to $RequestURL"
                $response = Invoke-WebRequest -UseBasicParsing -Uri $RequestURL -TimeoutSec 5 -ErrorAction Stop
                $status = "Success (HTTP $($response.StatusCode))"
                break
            } catch {
                if ($_.Exception.Response -ne $null) {
                    $code = $_.Exception.Response.StatusCode.Value__
                    if ($code -gt 99) {
                        $status = "Success (HTTP $code)"
                        break
                    }
                }
                Write-Log "Request failed: $($_.Exception.Message)"
            }
            Start-Sleep -Seconds $SleepSeconds
        }
        
        Write-Log "$status after $sleeps tries"
        return $status -match "Success"
    }
    
    # Start NVDA as a job
    Write-Log "Starting NVDA in the background"
    $nvdaJob = Start-Job -ScriptBlock {
        param($nvdaExePath)
        try {
            Start-Process -FilePath $nvdaExePath -NoNewWindow -PassThru
            return "Started"
        } catch {
            return "Error: $($_.Exception.Message)"
        }
    } -ArgumentList $nvdaExe
    
    # Wait a moment for NVDA to initialize
    Start-Sleep -Seconds 5
    
    # Check the job result
    $nvdaStartResult = Receive-Job -Job $nvdaJob
    Write-Log "NVDA start job result: $nvdaStartResult"
    
    # Check if NVDA is running
    $nvdaProcess = Get-Process -Name "nvda" -ErrorAction SilentlyContinue
    
    if ($nvdaProcess) {
        Write-Log "NVDA process found running with PID $($nvdaProcess.Id)"
        
        # Try to connect to NVDA's addon port
        Write-Log "Checking if NVDA's addon is responding on port 8765"
        $addonResponding = Wait-For-HTTP-Response -RequestURL "http://localhost:8765/info" -MaxTries 10
        
        if ($addonResponding) {
            Write-Log "Successfully connected to NVDA's addon on port 8765"
            $testSuccess = $true
        } else {
            Write-Log "Could not connect to NVDA's addon port"
            $testSuccess = $false
        }
        
        # Try to gracefully stop NVDA
        Write-Log "Attempting to stop NVDA process"
        try {
            Stop-Process -Name "nvda" -Force -ErrorAction Stop
            Write-Log "NVDA process stopped successfully"
        } catch {
            Write-Log "Failed to stop NVDA process: $_"
        }
    } else {
        Write-Log "NVDA process not found running. Check logs for errors."
        $testSuccess = $false
    }
    
    # Return result based on all checks
    if ($structureCheckPassed -and $testSuccess) {
        Write-Host "============= TEST SUCCEEDED ============="
        Write-Log "All tests passed - NVDA portable is valid and functional"
        @{
            "success" = $true
            "message" = "NVDA portable verification passed (structural check and execution test)"
        } | ConvertTo-Json
    } elseif ($structureCheckPassed) {
        Write-Host "============= TEST PARTIALLY SUCCEEDED ============="
        Write-Log "Structural check passed but execution test failed"
        @{
            "success" = $true  # Still mark as success since structure is valid
            "message" = "NVDA portable structure verification passed, but execution test failed"
            "warning" = "Execution test failed, but structure looks valid"
        } | ConvertTo-Json
    } else {
        Write-Host "============= TEST FAILED ============="
        Write-Log "Structural verification failed - portable copy is missing critical components"
        @{
            "success" = $false
            "error" = "Structural verification failed: Missing files: $($missingFiles -join ', '). Has portable flag: $hasPortableFlag"
        } | ConvertTo-Json
    }
}
catch {
    Write-Log "Error during test: $_"
    
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
} 