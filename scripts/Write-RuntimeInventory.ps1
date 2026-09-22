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

# External Inventory (For Windows Host)
$yamlExt = @(
    "all:"
    "  vars:"
    "    ansible_user: vagrant"
    "    ansible_ssh_private_key_file: .vagrant\machines\jumpbox\vmware_desktop\private_key"
    "  children:"
    "    lab:"
    "      hosts:"
)
foreach ($node in $nodeNames) {
    $entry = $entries[$node]
    $yamlExt += "        ${node}:"
    $yamlExt += "          ansible_host: $($entry["HostName"])"
    $yamlExt += "          ansible_port: $($entry["Port"])"
    $yamlExt += "          ansible_ssh_private_key_file: .vagrant\machines\$node\vmware_desktop\private_key"
}
$yamlExt += "    jumpbox:"
$yamlExt += "      hosts:"
$yamlExt += "        jumpbox:"

# Internal Inventory (For Jump Box)
$yamlInt = @(
    "all:"
    "  vars:"
    "    ansible_user: vagrant"
  "  children:"
    "    lab:"
    "      hosts:"
)
foreach ($node in $nodeNames) {
    $ipRaw = & vagrant ssh $node -c "hostname -I"
    if ($null -eq $ipRaw -or [string]::IsNullOrWhiteSpace($ipRaw)) {
        Write-Warning "Could not get IP for $node, using dummy 0.0.0.0"
        $ip = "0.0.0.0"
    } else {
        $ip = $ipRaw.Trim().Split(" ")[0].Trim()
    }
    $yamlInt += "        ${node}:"
    $yamlInt += "          ansible_host: $ip"
    $yamlInt += "          ansible_port: 22"
}
$yamlInt += "    jumpbox:"
$yamlInt += "      hosts:"
$yamlInt += "        jumpbox:"

$parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $parent | Out-Null
$yamlExt | Set-Content -Encoding ascii $OutputPath
$yamlInt | Set-Content -Encoding ascii (Join-Path $parent "runtime-internal.yml")
