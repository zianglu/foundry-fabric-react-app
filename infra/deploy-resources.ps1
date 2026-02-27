param(
  [Parameter(Mandatory = $true)]
  [string]$SubscriptionId,

  [Parameter(Mandatory = $true)]
  [string]$ResourceGroupName,

  [string]$Location = 'eastus',
  [string]$Prefix = 'contosotruck'
)

$ErrorActionPreference = 'Stop'

Write-Host "Setting subscription $SubscriptionId"
az account set --subscription $SubscriptionId | Out-Null

Write-Host "Ensuring resource group $ResourceGroupName in $Location"
az group create --name $ResourceGroupName --location $Location | Out-Null

$deploymentName = "infra-$(Get-Date -Format 'yyyyMMddHHmmss')"
$templateFile = Join-Path $PSScriptRoot 'main.bicep'

Write-Host "Deploying infrastructure with Bicep template: $templateFile"
$deployment = az deployment group create `
  --name $deploymentName `
  --resource-group $ResourceGroupName `
  --template-file $templateFile `
  --parameters location=$Location prefix=$Prefix `
  --output json | ConvertFrom-Json

$outputs = $deployment.properties.outputs

Write-Host 'Deployment completed. Outputs:'
Write-Host "  Container Apps Env: $($outputs.containerAppsEnvironmentName.value)"
Write-Host "  ACR Login Server   : $($outputs.acrLoginServer.value)"
Write-Host "  Backend MI Id      : $($outputs.backendIdentityId.value)"
Write-Host "  Key Vault URI      : $($outputs.keyVaultUri.value)"

Write-Host ''
Write-Host 'Next steps:'
Write-Host '1) Upload backend OBO certificate PEM to Key Vault as a secret (example secret name: backend-obo-pem).'
Write-Host '2) Run ../deploy/deploy-backend.ps1 to deploy the Python API container app.'
Write-Host '3) Run ../deploy/deploy-frontend.ps1 to deploy the Next.js container app.'
