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
        [string]$Script,
        [string]$Arguments
    )
    
    Write-Log "Running script: $Script $Arguments"
    $output = & $Script $Arguments
    
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

try {
    # Step 1: Install NVDA
    Write-Log "Step 1: Installing NVDA"
    $installResult = Run-Script -Script "powershell" -Arguments "-ExecutionPolicy Bypass -File scripts\install_nvda.ps1 -InstallerPath '$InstallerPath'"
    
    if (-not $installResult.success) {
        throw "NVDA installation failed: $($installResult.error)"
    }
    
    Write-Log "NVDA installation successful"
    
    # Step 2: Install addon
    Write-Log "Step 2: Installing addon"
    $addonResult = Run-Script -Script "powershell" -Arguments "-ExecutionPolicy Bypass -File scripts\install_addon.ps1 -AddonPath '$AddonPath'"
    
    if (-not $addonResult.success) {
        throw "Addon installation failed: $($addonResult.error)"
    }
    
    Write-Log "Addon installation successful"
    
    # Step 3: Create portable copy
    Write-Log "Step 3: Creating portable copy"
    $portableResult = Run-Script -Script "powershell" -Arguments "-ExecutionPolicy Bypass -File scripts\create_portable_nvda.ps1 -Version '$Version'"
    
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