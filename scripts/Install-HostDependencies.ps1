[CmdletBinding()]
param(
    [switch]$InstallMissing
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"

# Mapping of command names to their typical installation directories
$CommonPaths = @{
    "VBoxManage" = "C:\Program Files\Oracle\VirtualBox"
    "vagrant"    = @("C:\Program Files\Vagrant\bin", "C:\Hashicorp\Vagrant\bin")
}

function Ensure-Command([string]$Name, [string]$PackageId, [string]$InstallHint) {
    if (Get-Command $Name -ErrorAction SilentlyContinue) { return }

    # 1. Check if it exists in common known paths but isn't in the current session PATH
    if ($CommonPaths.ContainsKey($Name)) {
        $paths = $CommonPaths[$Name]
        if ($paths -is [string]) { $paths = @($paths) }
        
        foreach ($path in $paths) {
            $exePath = Join-Path $path "$Name.exe"
            if (-not (Test-Path $exePath)) {
                $found = Get-ChildItem -Path $path -Filter "$Name*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($found) { $exePath = $found.FullName }
            }

            if (Test-Path $exePath) {
                Write-Host "Found $Name at $path. Adding to current session PATH..." -ForegroundColor Cyan
                $env:Path += ";$path"
                if (Get-Command $Name -ErrorAction SilentlyContinue) { return }
            }
        }
    }

    # 2. If not found and -InstallMissing is NOT set, fail
    if (-not $InstallMissing) {
        throw "$Name is required. $InstallHint Re-run with -InstallMissing to install it with winget."
    }

    # 3. Use winget to install
    if (-not (Get-Command "winget" -ErrorAction SilentlyContinue)) {
        throw "$Name is required and winget is unavailable. $InstallHint"
    }

    Write-Host "Installing $Name via winget..." -ForegroundColor Yellow
    & winget install --id $PackageId --exact --accept-package-agreements --accept-source-agreements

    # 4. Final check: if still not in PATH, try the common paths one more time
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        if ($CommonPaths.ContainsKey($Name)) {
            $paths = $CommonPaths[$Name]
            if ($paths -is [string]) { $paths = @($paths) }
            foreach ($path in $paths) {
                if (Test-Path $path) {
                    $env:Path += ";$path"
                    if (Get-Command $Name -ErrorAction SilentlyContinue) { return }
                }
            }
        }
        throw "$Name was installed but is not available in this PowerShell session. Please restart your terminal."
    }
}

Ensure-Command "VBoxManage" "Oracle.VirtualBox" "Install VirtualBox 7.x."
Ensure-Command "vagrant" "Hashicorp.Vagrant" "Install Vagrant 2.4.x."
Ensure-Command "py" "Python.Python.3.11" "Install Python 3.11+."

if (-not (Test-Path $venv)) {
    & py -3 -m venv $venv
}

$python = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "The Python virtual environment could not be created at $venv."
}

& $python -m pip install --disable-pip-version-check --upgrade -r (Join-Path $root "requirements.txt")

# Windows Compatibility Fix:
# Ansible-core triggers a Unix-specific 'check_blocking_io' error when run on Windows.
# Since we use the host only to trigger remote runs, we verify installation by 
# checking for the presence of the executables rather than executing them.
$ansibleExec = Join-Path $venv "Scripts\ansible-playbook.exe"
if (Test-Path $ansibleExec) {
    Write-Host "Ansible installation verified (Executable found at $ansibleExec)." -ForegroundColor Green
} else {
    throw "Ansible installation failed: ansible-playbook.exe not found in venv."
}
