# Foundry + Fabric Trucking Demo Architecture

## Existing Fabric components (already created)

1. Fabric Lakehouse/Data Lake with trucking entities (`trips`, `routes`, `drivers`, `trucks`, `customers`, `loads`)
2. Fabric Semantic Model over the data lake for KPIs/rolling metrics
3. Fabric KQL database for realtime load status updates
4. Fabric Data Agent connected to lakehouse + semantic model + KQL DB

## New components implemented in this repo

- `backend/`: Python FastAPI backend with Entra token validation + OBO
- `backend/scripts/create_foundry_agent.py`: script to create/update Azure AI Foundry Agent
- `react-app/`: Next.js front-end updated to call backend APIs
- `infra/`: Azure resource provisioning (Bicep + PowerShell)
- `deploy/`: backend/frontend deployment scripts for Azure Container Apps

## Azure resources to create

- Azure Resource Group
- Azure Container Registry (ACR)
- Azure Container Apps Environment
- Azure Container App (backend)
- Azure Container App (frontend)
- Log Analytics Workspace
- Key Vault (for backend OBO certificate secret)
- User-assigned Managed Identity (backend app + Key Vault + ACR pull)
- Azure AI Foundry Project (if not already created)
- Azure AI Search service + index for PDFs (if not already created)

## Entra identity setup

### 1) Frontend app registration

- Type: SPA
- Redirect URIs: frontend URL(s)
- API permissions: delegated permission to backend API scope `access_as_user`

### 2) Backend app registration

- Type: Web/API
- Expose API scope: `access_as_user`
- Client credential: certificate (recommended)
- OBO delegated downstream permissions:
  - Foundry agent resource scope (for your Foundry endpoint)
  - Fabric Graph API scope

### 3) Backend managed identity

- Assign roles:
  - `AcrPull` on ACR
  - `Key Vault Secrets User` on Key Vault

## Deployment order

1. Deploy Azure base resources

```powershell
.\infra\deploy-resources.ps1 `
  -SubscriptionId "<sub-id>" `
  -ResourceGroupName "rg-contoso-trucking" `
  -Location "eastus" `
  -Prefix "contosotruck"
```

2. Create/update Foundry agent

```powershell
cd backend
python .\scripts\create_foundry_agent.py `
  --agents-base-url "https://<project>.services.ai.azure.com/api/projects/<project-id>/agents" `
  --name "contoso-trucking-agent" `
  --model "gpt-4.1" `
  --fabric-workspace-id "<workspace-guid>" `
  --fabric-data-agent-id "<fabric-data-agent-guid>" `
  --search-connection-id "<search-connection-id>" `
  --search-index-name "trucking-pdf-index"
```

Note: Foundry preview endpoints can vary by API version/region. If your project uses a different agents route, pass that exact URL to `--agents-base-url`.

3. Deploy backend container app

```powershell
.\deploy\deploy-backend.ps1 `
  -SubscriptionId "<sub-id>" `
  -ResourceGroupName "rg-contoso-trucking" `
  -ContainerAppsEnvironmentName "contosotruck-cae" `
  -AcrName "contosotruckacr" `
  -BackendIdentityResourceId "/subscriptions/<sub-id>/resourceGroups/rg-contoso-trucking/providers/Microsoft.ManagedIdentity/userAssignedIdentities/contosotruck-backend-mi" `
  -KeyVaultName "contosotruck-kv" `
  -TenantId "<tenant-id>" `
  -BackendClientId "<backend-app-client-id>" `
  -BackendApiAudience "api://<backend-app-client-id>" `
  -FabricGraphBaseUrl "https://api.fabric.microsoft.com/v1/workspaces/<workspace-id>/graph" `
  -FoundryAgentEndpoint "https://<project>.services.ai.azure.com/api/projects/<project-id>/agents/<agent-id>/chat/completions?api-version=2025-05-15-preview"
```

4. Deploy frontend container app

```powershell
.\deploy\deploy-frontend.ps1 `
  -SubscriptionId "<sub-id>" `
  -ResourceGroupName "rg-contoso-trucking" `
  -ContainerAppsEnvironmentName "contosotruck-cae" `
  -AcrName "contosotruckacr" `
  -FrontendClientId "<frontend-app-client-id>" `
  -TenantId "<tenant-id>" `
  -ApiScope "api://<backend-app-client-id>/access_as_user" `
  -BackendApiBaseUrl "https://<backend-app-fqdn>"
```

## Runtime config summary

### Frontend env

- `NEXT_PUBLIC_ENTRA_CLIENT_ID`
- `NEXT_PUBLIC_ENTRA_TENANT_ID`
- `NEXT_PUBLIC_API_SCOPE`
- `NEXT_PUBLIC_BACKEND_API_BASE_URL`
- `NEXT_PUBLIC_AZURE_MAPS_KEY` (optional map rendering)

### Backend env

- `AZURE_TENANT_ID`
- `BACKEND_CLIENT_ID`
- `BACKEND_API_AUDIENCE`
- `BACKEND_REQUIRED_SCOPE`
- `BACKEND_CLIENT_CERTIFICATE_PATH`
- `BACKEND_CLIENT_CERTIFICATE_THUMBPRINT`
- `FOUNDRY_AGENT_ENDPOINT`
- `FOUNDRY_AGENT_SCOPE`
- `FOUNDRY_AGENT_ID` (optional)
- `FABRIC_GRAPH_BASE_URL`
- `FABRIC_GRAPH_SCOPE`
- `FABRIC_GRAPH_*_PATH`
- `CORS_ORIGINS`

## Frontend behavior change implemented

- The app no longer calls Fabric APIs directly from browser code.
- It now requests backend APIs with Entra access tokens.
- New `Trips` page:
  - loads customers from `GET /api/customers`
  - loads active trips for selected customer from `GET /api/customers/{id}/active-trips`
