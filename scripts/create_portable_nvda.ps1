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
    
    # Check if NVDA is installed
    $nvdaInstalledDir = Join-Path ${env:ProgramFiles(x86)} "NVDA"
    $nvdaExe = Join-Path $nvdaInstalledDir "nvda.exe"
    
    if (-not (Test-Path $nvdaExe)) {
        throw "NVDA not found at expected location: $nvdaExe"
    }
    
    Write-Log "NVDA found at: $nvdaExe"
    
    # Method 1: Use NVDA's built-in portable creation option
    Write-Log "Attempting to create portable copy using NVDA's built-in --create-portable-silent option"
    
    # Use a job to run with timeout
    $job = Start-Job -ScriptBlock {
        param($nvdaExe, $portablePath)
        Start-Process -FilePath $nvdaExe -ArgumentList "--create-portable-silent", "--portable-path=`"$portablePath`"" -Wait -NoNewWindow
    } -ArgumentList $nvdaExe, $portablePath
    
    # Wait for the job with a timeout of 2 minutes
    $timeout = 120 # 2 minutes
    Write-Log "Running portable creation with timeout of $timeout seconds"
    $completed = Wait-Job -Job $job -Timeout $timeout
    
    if ($completed -eq $null) {
        Write-Log "Portable creation timed out, stopping job"
        Stop-Job -Job $job
    }
    
    # Get any results
    $result = Receive-Job -Job $job
    Write-Log "Job result: $result"
    Remove-Job -Job $job -Force
    
    # Check for any NVDA process and kill it
    Write-Log "Checking for NVDA processes"
    Get-Process -Name "nvda" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Log "Killing NVDA process with ID: $($_.Id)"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    
    # Check if portable was created
    $portableExe = Join-Path $portablePath "nvda.exe"
    $portableCreated = Test-Path $portableExe
    
    if ($portableCreated) {
        Write-Log "Portable copy created successfully using NVDA's built-in option"
    } else {
        Write-Log "NVDA's built-in option failed to create portable copy"
        
        # Method 2: Manual copy method
        Write-Log "Using manual copy method to create portable NVDA"
        
        try {
            # Copy all files from installed NVDA to portable directory
            Write-Log "Copying from $nvdaInstalledDir to $portablePath"
            
            # Use robocopy for more reliable copying
            $robocopyOutput = robocopy $nvdaInstalledDir $portablePath /E /NFL /NDL /NJH /NJS /nc /ns /np
            Write-Log "Robocopy completed with exit code: $LASTEXITCODE"
            
            # Create portable flag file
            $portableIni = Join-Path $portablePath "portable.ini"
            Write-Log "Creating portable flag file: $portableIni"
            Set-Content -Path $portableIni -Value "[portable]`n"
            
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
    }
    
    # Verify the portable copy exists as final check
    if ($portableCreated) {
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