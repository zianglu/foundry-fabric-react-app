# Backend API (FastAPI)

Python backend that receives Entra bearer tokens from the Next.js frontend, validates them, and uses On-Behalf-Of (OBO) to call:
- Azure AI Foundry Agent runtime
- Fabric Graph API

## Endpoints

- `GET /health`
- `GET /api/trucks`
- `GET /api/drivers`
- `GET /api/loads`
- `GET /api/trips?status=<status>&customerId=<id>`
- `GET /api/customers`
- `GET /api/customers/{customer_id}/active-trips`
- `POST /api/chat` with `{ "question": "..." }`

## Local run

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Authentication notes

- The API validates inbound Entra access tokens using tenant OpenID metadata.
- OBO is done with `msal.ConfidentialClientApplication.acquire_token_on_behalf_of`.
- For Azure deployment, use certificate-based service principal auth (Key Vault + managed identity), not static keys.

## Foundry agent creation script

Use `scripts/create_foundry_agent.py`:

```powershell
python .\scripts\create_foundry_agent.py `
  --agents-base-url "https://<project>.services.ai.azure.com/api/projects/<project-id>/agents" `
  --name "contoso-trucking-agent" `
  --model "gpt-4.1" `
  --fabric-workspace-id "<workspace-guid>" `
  --fabric-data-agent-id "<fabric-data-agent-guid>" `
  --search-connection-id "<foundry-search-connection-id>" `
  --search-index-name "trucking-pdf-index"
```
