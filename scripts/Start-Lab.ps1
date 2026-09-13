[CmdletBinding()]
param(
    [switch]$ProvisionOnly
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"
$ansible = Join-Path $venv "Scripts\ansible-playbook.exe"
$inventory = Join-Path $root "ansible\inventory\runtime.yml"

if (-not (Test-Path $ansible)) {
    throw "Ansible is not installed. Run .\scripts\Install-HostDependencies.ps1 first."
}

Push-Location $root
try {
    & vagrant up --provider=virtualbox
    & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Write-RuntimeInventory.ps1") -OutputPath $inventory
    if (-not $ProvisionOnly) {
        $env:ANSIBLE_CONFIG = Join-Path $root "ansible\ansible.cfg"
        & $ansible -i $inventory (Join-Path $root "ansible\playbooks\site.yml") `
            --extra-vars "lab_root=/opt/devsecops-lab"
    }
}
finally {
    Pop-Location
}
