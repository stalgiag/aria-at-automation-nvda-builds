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
        
        try {
            $result = $output | ConvertFrom-Json
            return $result
        }
        catch {
            Write-Log "Failed to parse output as JSON: $_"
            Write-Log "Raw output: $output"
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
    
    if (-not $portableResult.success) {
        throw "Creating portable copy failed: $($portableResult.error)"
    }
    
    Write-Log "Portable copy created successfully at: $($portableResult.portable_path)"
    
    # Return success result
    @{
        "success" = $true
        "portable_path" = $portableResult.portable_path
    } | ConvertTo-Json
}
catch {
    Write-Log "Configuration failed: $_"
    @{
        "success" = $false
        "error" = $_.ToString()
    } | ConvertTo-Json
} 