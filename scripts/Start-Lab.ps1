[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Push-Location $root
try {
    Write-Host "Booting lab VMs..." -ForegroundColor Cyan
    & vagrant up --provider=vmware_desktop

    Write-Host "`n--- Lab Access Info ---" -ForegroundColor Green
    $nodes = @("gitlab", "runner", "app", "jumpbox")
    foreach ($node in $nodes) {
        $ip = & vagrant ssh $node -c "hostname -I"
        $ip = $ip.Trim().Split(" ")[0].Trim()
        Write-Host "$node`t-> http://$ip"
    }
    Write-Host "-----------------------`n"
}
finally {
    Pop-Location
}
