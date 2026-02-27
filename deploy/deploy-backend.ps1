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
  [string]$BackendIdentityResourceId,

  [Parameter(Mandatory = $true)]
  [string]$KeyVaultName,

  [Parameter(Mandatory = $true)]
  [string]$TenantId,

  [Parameter(Mandatory = $true)]
  [string]$BackendClientId,

  [Parameter(Mandatory = $true)]
  [string]$BackendApiAudience,

  [Parameter(Mandatory = $true)]
  [string]$FabricGraphBaseUrl,

  [Parameter(Mandatory = $true)]
  [string]$FoundryAgentEndpoint,

  [string]$BackendAppName = 'contoso-backend-api',
  [string]$ImageTag = 'latest',
  [string]$FoundryAgentScope = 'https://ai.azure.com/.default',
  [string]$FabricGraphScope = 'https://api.fabric.microsoft.com/.default',
  [string]$CorsOrigins = 'https://contoso-frontend.example.com',
  [string]$FoundryAgentId = '',
  [string]$BackendRequiredScope = 'access_as_user',
  [string]$BackendCertificatePath = '/mnt/secrets/backend-obo-pem',
  [string]$BackendCertificateThumbprint = '',
  [string]$BackendSecretName = 'backend-obo-pem'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$backendPath = Join-Path $repoRoot 'backend'
$imageName = 'foundry-fabric-backend'
$imageRef = "$AcrName.azurecr.io/$imageName`:$ImageTag"

Write-Host "Setting subscription $SubscriptionId"
az account set --subscription $SubscriptionId | Out-Null

Write-Host "Building backend image $imageRef from $backendPath"
az acr build --registry $AcrName --image "$imageName`:$ImageTag" $backendPath

$existing = az containerapp show --name $BackendAppName --resource-group $ResourceGroupName --query name -o tsv 2>$null

$envVars = @(
  "AZURE_TENANT_ID=$TenantId"
  "BACKEND_CLIENT_ID=$BackendClientId"
  "BACKEND_API_AUDIENCE=$BackendApiAudience"
  "BACKEND_REQUIRED_SCOPE=$BackendRequiredScope"
  "BACKEND_CLIENT_CERTIFICATE_PATH=$BackendCertificatePath"
  "BACKEND_CLIENT_CERTIFICATE_THUMBPRINT=$BackendCertificateThumbprint"
  "FOUNDRY_AGENT_ENDPOINT=$FoundryAgentEndpoint"
  "FOUNDRY_AGENT_SCOPE=$FoundryAgentScope"
  "FABRIC_GRAPH_BASE_URL=$FabricGraphBaseUrl"
  "FABRIC_GRAPH_SCOPE=$FabricGraphScope"
  "CORS_ORIGINS=$CorsOrigins"
)

if ($FoundryAgentId) {
  $envVars += "FOUNDRY_AGENT_ID=$FoundryAgentId"
}

if (-not $existing) {
  Write-Host "Creating container app $BackendAppName"
  az containerapp create `
    --name $BackendAppName `
    --resource-group $ResourceGroupName `
    --environment $ContainerAppsEnvironmentName `
    --image $imageRef `
    --target-port 8000 `
    --ingress external `
    --registry-server "$AcrName.azurecr.io" `
    --registry-identity $BackendIdentityResourceId `
    --user-assigned $BackendIdentityResourceId `
    --cpu 0.5 `
    --memory 1.0Gi `
    --env-vars $envVars `
    --secrets "$BackendSecretName=keyvaultref:https://$KeyVaultName.vault.azure.net/secrets/$BackendSecretName,identityref:$BackendIdentityResourceId" `
    --secret-volume-mount /mnt/secrets
} else {
  Write-Host "Updating container app $BackendAppName"
  az containerapp update `
    --name $BackendAppName `
    --resource-group $ResourceGroupName `
    --image $imageRef `
    --set-env-vars $envVars
}

$backendUrl = az containerapp show --name $BackendAppName --resource-group $ResourceGroupName --query properties.configuration.ingress.fqdn -o tsv
Write-Host "Backend deployed at: https://$backendUrl"
