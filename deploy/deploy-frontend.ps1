param(
  [Parameter(Mandatory = $true)]
  [string]$SubscriptionId,

  [Parameter(Mandatory = $true)]
  [string]$ResourceGroupName,

  [Parameter(Mandatory = $true)]
  [string]$ContainerAppsEnvironmentName,

  [Parameter(Mandatory = $true)]
  [string]$AcrName,

  [Parameter(Mandatory = $true)]
  [string]$FrontendClientId,

  [Parameter(Mandatory = $true)]
  [string]$TenantId,

  [Parameter(Mandatory = $true)]
  [string]$ApiScope,

  [Parameter(Mandatory = $true)]
  [string]$BackendApiBaseUrl,

  [string]$FrontendAppName = 'contoso-frontend-web',
  [string]$ImageTag = 'latest',
  [string]$AzureMapsKey = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$frontendPath = Join-Path $repoRoot 'react-app'
$imageName = 'foundry-fabric-frontend'
$imageRef = "$AcrName.azurecr.io/$imageName`:$ImageTag"

Write-Host "Setting subscription $SubscriptionId"
az account set --subscription $SubscriptionId | Out-Null

Write-Host "Building frontend image $imageRef from $frontendPath"
az acr build `
  --registry $AcrName `
  --image "$imageName`:$ImageTag" `
  --build-arg NEXT_PUBLIC_ENTRA_CLIENT_ID=$FrontendClientId `
  --build-arg NEXT_PUBLIC_ENTRA_TENANT_ID=$TenantId `
  --build-arg NEXT_PUBLIC_API_SCOPE=$ApiScope `
  --build-arg NEXT_PUBLIC_BACKEND_API_BASE_URL=$BackendApiBaseUrl `
  --build-arg NEXT_PUBLIC_AZURE_MAPS_KEY=$AzureMapsKey `
  $frontendPath

$existing = az containerapp show --name $FrontendAppName --resource-group $ResourceGroupName --query name -o tsv 2>$null

if (-not $existing) {
  Write-Host "Creating container app $FrontendAppName"
  az containerapp create `
    --name $FrontendAppName `
    --resource-group $ResourceGroupName `
    --environment $ContainerAppsEnvironmentName `
    --image $imageRef `
    --target-port 3000 `
    --ingress external `
    --registry-server "$AcrName.azurecr.io" `
    --registry-identity system `
    --system-assigned `
    --cpu 0.5 `
    --memory 1.0Gi

  $principalId = az containerapp show --name $FrontendAppName --resource-group $ResourceGroupName --query identity.principalId -o tsv
  $acrId = az acr show --name $AcrName --resource-group $ResourceGroupName --query id -o tsv
  az role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal --role AcrPull --scope $acrId | Out-Null

  az containerapp update --name $FrontendAppName --resource-group $ResourceGroupName --image $imageRef | Out-Null
} else {
  Write-Host "Updating container app $FrontendAppName"
  az containerapp update --name $FrontendAppName --resource-group $ResourceGroupName --image $imageRef | Out-Null
}

$frontendUrl = az containerapp show --name $FrontendAppName --resource-group $ResourceGroupName --query properties.configuration.ingress.fqdn -o tsv
Write-Host "Frontend deployed at: https://$frontendUrl"
