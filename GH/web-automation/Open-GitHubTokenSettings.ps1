[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# GitHub's classic PAT form accepts a scopes query parameter. The user must
# still sign in, review expiration/organization policy, and explicitly generate it.
$tokenPage = 'https://github.com/settings/tokens/new?scopes=repo%2Cread%3Aorg%2Cgist%2Cworkflow&description=devsec%20GitHub%20CLI'
Write-Host 'Opening GitHub classic token creation with gh CLI scopes preselected:'
Write-Host 'repo, read:org, gist, workflow'
Write-Host 'The classic repo scope covers every repository your account can access.'
Start-Process $tokenPage
