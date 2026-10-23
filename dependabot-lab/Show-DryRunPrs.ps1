param(
    [string]$LogName = "devsec-pip-root.log"
)

$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "filter-dry-run-prs.py"
$remoteDir = "/home/vagrant/dependabot-core"

Push-Location $PSScriptRoot
try {
    vagrant ssh -c "mkdir -p $remoteDir/scripts"
    vagrant upload $script "$remoteDir/scripts/filter-dry-run-prs.py"
    vagrant ssh -c "python3 $remoteDir/scripts/filter-dry-run-prs.py $remoteDir/dry-run/$LogName"
}
finally {
    Pop-Location
}
