[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    & vagrant up gitlab runner app jenkins --provider=vmware_desktop
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the four service VMs.' }
    & vagrant halt jumpbox
    if ($LASTEXITCODE -ne 0) { throw 'Could not halt jumpbox.' }
    & vagrant status
}
finally {
    Pop-Location
}
