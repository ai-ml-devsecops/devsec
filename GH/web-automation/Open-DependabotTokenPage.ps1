[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$tokenPage = 'https://github.com/settings/personal-access-tokens/new?name=Dependabot+devsec+dry-run&target_name=ai-ml-devsecops&expires_in=30&contents=read'

Write-Host 'In the GitHub form:'
Write-Host '  Resource owner: ai-ml-devsecops'
Write-Host '  Repository access: Only select repositories -> devsec'
Write-Host '  Repository permissions: Contents -> Read-only'
Write-Host '  Expiration: choose a short period that suits your lab'
Write-Host 'Click Generate token and copy it.'
Write-Host 'Then paste it at the waiting "GitHub token:" prompt in the Ubuntu VM and press Enter.'
Write-Host 'The VM prompt hides the token as you type. Do not paste it into chat.'

Start-Process $tokenPage
