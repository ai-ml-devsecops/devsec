[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$sshConfig = Join-Path $root ".vagrant\ssh-config"
$nodeNames = @("gitlab", "runner", "app", "jumpbox")

Push-Location $root
try {
    & vagrant ssh-config | Set-Content -Encoding ascii $sshConfig
}
finally {
    Pop-Location
}

$entries = @{}
$current = $null
foreach ($line in Get-Content $sshConfig) {
    if ($line -match "^Host\s+(.+)$") {
        $current = $Matches[1].Trim()
        $entries[$current] = @{}
        continue
    }
    if ($null -ne $current -and $line -match "^\s*HostName\s+(.+)$") {
        $entries[$current]["HostName"] = $Matches[1].Trim()
        continue
    }
    if ($null -ne $current -and $line -match "^\s*Port\s+(.+)$") {
        $entries[$current]["Port"] = $Matches[1].Trim()
    }
}

$missing = $nodeNames | Where-Object {
    -not $entries.ContainsKey($_) -or
    -not $entries[$_].ContainsKey("HostName") -or
    -not $entries[$_].ContainsKey("Port")
}
if ($missing) {
    throw "Could not resolve runtime SSH addresses for: $($missing -join ', ')"
}

$yaml = @(
    "all:"
    "  vars:"
    "    ansible_user: vagrant"
    "    ansible_ssh_private_key_file: .vagrant\machines\jumpbox\virtualbox\private_key"
    "  children:"
    "    lab:"
    "      hosts:"
)
foreach ($node in $nodeNames) {
    $entry = $entries[$node]
    $yaml += "        ${node}:"
    $yaml += "          ansible_host: $($entry["HostName"])"
    $yaml += "          ansible_port: $($entry["Port"])"
    $yaml += "          ansible_ssh_private_key_file: .vagrant\machines\$node\virtualbox\private_key"
}
$yaml += "    jumpbox:"
$yaml += "      hosts:"
$yaml += "        jumpbox:"

$parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $parent | Out-Null
$yaml | Set-Content -Encoding ascii $OutputPath
