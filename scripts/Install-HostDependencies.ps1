[CmdletBinding()]
param(
    [switch]$InstallMissing
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"

function Ensure-Command([string]$Name, [string]$PackageId, [string]$InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        if (-not $InstallMissing) {
            throw "$Name is required. $InstallHint Re-run with -InstallMissing to install it with winget."
        }
        if (-not (Get-Command "winget" -ErrorAction SilentlyContinue)) {
            throw "$Name is required and winget is unavailable. $InstallHint"
        }
        & winget install --id $PackageId --exact --accept-package-agreements --accept-source-agreements
        if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
            throw "$Name was installed but is not available in this PowerShell session. Open a new terminal and rerun this script."
        }
    }
}

Ensure-Command "VBoxManage" "Oracle.VirtualBox" "Install VirtualBox 7.x and ensure VBoxManage is on PATH."
Ensure-Command "vagrant" "Hashicorp.Vagrant" "Install Vagrant 2.4.x and ensure vagrant is on PATH."
Ensure-Command "py" "Python.Python.3.11" "Install Python 3.11+ from python.org or the Microsoft Store."

if (-not (Test-Path $venv)) {
    & py -3 -m venv $venv
}

$python = Join-Path $venv "Scripts\python.exe"
& $python -m pip install --disable-pip-version-check --upgrade -r (Join-Path $root "requirements.txt")
& $python -m ansible --version
