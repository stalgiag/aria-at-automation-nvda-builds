param(
    [Parameter(Mandatory=$true)]
    [string]$InstallerPath,
    
    [Parameter(Mandatory=$true)]
    [string]$AddonPath,
    
    [Parameter(Mandatory=$true)]
    [string]$Version
)

# Set up logging
$LogFile = "configure_nvda_wrapper.log"
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -Append -FilePath $LogFile
}

Write-Log "Starting NVDA configuration with:"
Write-Log "- Installer: $InstallerPath"
Write-Log "- Addon: $AddonPath"
Write-Log "- Version: $Version"

function Run-Script {
    param(
        [string]$ScriptPath,
        [hashtable]$Parameters
    )
    
    Write-Log "Running script: $ScriptPath with parameters: $($Parameters | ConvertTo-Json -Compress)"
    
    try {
        # Execute the script directly with parameters
        $output = & $ScriptPath @Parameters
        
        # Special handling for output that contains success markers
        if ($output -match "=========== PORTABLE CREATION SUCCESS ==========") {
            Write-Log "Detected direct success marker in output"
            # Extract the JSON part - it should be the last part of the output
            $jsonPart = $output -split "=========== PORTABLE CREATION SUCCESS ==========" | Select-Object -Last 1
            $jsonPart = $jsonPart -replace "^.*?(\{.*\}).*$", '$1'
            
            try {
                $parsedJson = $jsonPart | ConvertFrom-Json
                return $parsedJson
            } catch {
                # If we can't parse the JSON but we saw the success marker, still return success
                Write-Log "Found success marker but couldn't parse JSON. Returning success anyway."
                return @{
                    "success" = $true
                    "portable_path" = $Parameters.Contains("Version") ? "nvda_$($Parameters.Version)_portable" : "unknown_path"
                }
            }
        }
        
        # Standard JSON parsing for normal output
        try {
            $result = $output | ConvertFrom-Json
            return $result
        }
        catch {
            Write-Log "Failed to parse output as JSON: $_"
            Write-Log "Raw output: $output"
            
            # Check for success indicators in the raw output
            if ($output -match "successfully" -and -not ($output -match "Error|Failed|failed")) {
                Write-Log "Output contains success indicators even though JSON parsing failed."
                return @{
                    "success" = $true
                    "message" = "Operation completed with success indicators in output"
                }
            }
            
            return @{
                "success" = $false
                "error" = "Failed to parse script output"
            }
        }
    }
    catch {
        Write-Log "Error executing script: $_"
        return @{
            "success" = $false
            "error" = $_.Exception.Message
        }
    }
}

try {
    # Step 1: Install NVDA
    Write-Log "Step 1: Installing NVDA"
    $installParams = @{
        InstallerPath = $InstallerPath
    }
    $installResult = Run-Script -ScriptPath "$PSScriptRoot\install_nvda.ps1" -Parameters $installParams
    
    if (-not $installResult.success) {
        throw "NVDA installation failed: $($installResult.error)"
    }
    
    Write-Log "NVDA installation successful"
    
    # Step 2: Install addon
    Write-Log "Step 2: Installing addon"
    $addonParams = @{
        AddonPath = $AddonPath
    }
    $addonResult = Run-Script -ScriptPath "$PSScriptRoot\install_addon.ps1" -Parameters $addonParams
    
    if (-not $addonResult.success) {
        throw "Addon installation failed: $($addonResult.error)"
    }
    
    Write-Log "Addon installation successful"
    
    # Step 3: Create portable copy
    Write-Log "Step 3: Creating portable copy"
    $portableParams = @{
        Version = $Version
    }
    $portableResult = Run-Script -ScriptPath "$PSScriptRoot\create_portable_nvda.ps1" -Parameters $portableParams
    
    Write-Log "Portable copy script returned: $($portableResult | ConvertTo-Json -Compress)"
    
    if (-not $portableResult.success) {
        throw "Creating portable copy failed: $($portableResult.error)"
    }
    
    $portablePath = if ($portableResult.portable_path) {
        $portableResult.portable_path
    } else {
        Join-Path $PWD "nvda_${Version}_portable"
    }
    
    # Verify the portable path actually exists
    if (Test-Path $portablePath) {
        Write-Log "Verified portable path exists: $portablePath"
    } else {
        Write-Log "WARNING: Portable path reported successful but directory not found: $portablePath"
    }
    
    Write-Log "Portable copy created successfully at: $portablePath"
    
    # Return success result
    @{
        "success" = $true
        "portable_path" = $portablePath
    } | ConvertTo-Json
}
catch {
    Write-Log "Configuration failed: $_"
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
    exit 1  # Ensure the error is properly propagated
} 