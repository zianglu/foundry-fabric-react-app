# Contoso Trucking Operations Center

A full-stack web application that combines **Azure AI Foundry Agents**, **Microsoft Fabric**, and a **React/Next.js** frontend to provide an intelligent operations dashboard for a trucking company. Users can view terminals on a live map, query trucking data through natural language chat, and browse customer trips — all secured with Microsoft Entra ID.

# IMPORTANT NOTE: 
THIS CODEBASE IS PROVIDED FOR EDUCATIONAL PURPOSES AND SHOULD NOT BE USED IN PRODUCTION. 

This is a reference codebase provided as an example of how to implement a full stack application with a Fabric/Foundry backend.
This app was used as the basis for the following YouTube video and was created to illustrate a specific architectural approach. This code
is not intended for production deployment.:

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          User's Browser                                 │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              React / Next.js Frontend (:3000)                    │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────────┐  ┌────────────────────┐    │   │
│  │  │  Azure Map  │  │  Chat Interface │  │  Customer Trips    │    │   │
│  │  │  (terminals,│  │  (natural lang  │  │  (trip tracking)   │    │   |
│  │  │   trucks)   │  │   queries)      │  │                    │    │   │
│  │  └─────────────┘  └─────────────────┘  └────────────────────┘    │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                             │ Bearer token                              │
│                             │ (api://<client-id>/access_as_user)        │
└─────────────────────────────┼───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Python FastAPI Backend (:8000)                       │
│                                                                         │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────────────────┐    │
│  │ Entra Token  │  │  OBO Token       │  │  API Endpoints          │    │
│  │ Validation   │──│  Provider (MSAL) │  │  /api/terminals         │    │
│  │              │  │                  │  │  /api/chat              │    │
│  └──────────────┘  └───────┬──────────┘  │  /api/customers         │    │
│                            │             │  /api/trips             │    │
│                            │             │  /api/trucks ...        │    │
│                            │             └─────────────────────────┘    │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │  On-Behalf-Of (OBO) Flow    │
              │  Exchange user token for    │
              │  downstream service tokens  │
              ▼                             ▼
┌───────────────────────┐    ┌──────────────────────────────┐
│  Azure AI Foundry     │    │  Microsoft Fabric            │
│                       │    │                              │
│  ┌─────────────────┐  │    │  ┌────────────────────────┐  │
│  │ Foundry Agent   │  │    │  │ GraphQL API            │  │
│  │ (chat/Q&A)      │  │    │  │ (terminals, entities)  │  │
│  │                 │  │    │  └────────────────────────┘  │
│  │  ┌───────────┐  │  │    │  ┌────────────────────────┐  │
│  │  │ Fabric    │  │  │    │  │ Lakehouse / Data Lake  │  │
│  │  │ Data Agent│  │  │    │  │ (trips, trucks,        │  │
│  │  └───────────┘  │  │    │  │  drivers, loads,       │  │
│  │  ┌───────────┐  │  │    │  │  customers)            │  │
│  │  │ AI Search │  │  │    │  └────────────────────────┘  │
│  │  │ Index     │  │  │    │  ┌────────────────────────┐  │
│  │  └───────────┘  │  │    │  │ Semantic Model (KPIs)  │  │
│  └─────────────────┘  │    │  └────────────────────────┘  │
└───────────────────────┘    └──────────────────────────────┘
```

### Authentication Flow

1. The user signs in via the React SPA using **MSAL.js** and receives an Entra access token scoped to `api://<client-id>/access_as_user`
2. The frontend sends this token as a Bearer header to the Python backend
3. The backend validates the token against Entra's OpenID metadata
4. For downstream calls, the backend performs an **On-Behalf-Of (OBO)** token exchange via MSAL, obtaining tokens scoped to:
   - `https://ai.azure.com/.default` — for the Azure AI Foundry Agent
   - `https://api.fabric.microsoft.com/.default` — for Fabric GraphQL and REST APIs
5. All downstream calls execute under the **signed-in user's identity**, preserving Fabric row-level security and workspace permissions

## Project Structure

```
foundry-fabric-react-app/
├── backend/           Python FastAPI backend
│   ├── app/
│   │   ├── main.py        API endpoints and CORS config
│   │   ├── auth.py        Entra token validation
│   │   ├── obo.py         OBO token exchange provider
│   │   ├── config.py      Environment-driven settings
│   │   ├── models.py      Request/response models
│   │   └── clients/
│   │       ├── foundry.py       Azure AI Foundry Agent SDK client
│   │       └── fabric_graph.py  Fabric REST + GraphQL client
│   ├── scripts/           Agent creation/management scripts
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── react-app/         Next.js frontend
│   ├── app/               Pages and layout
│   ├── components/
│   │   ├── chat/          Chat interface (natural language queries)
│   │   ├── map/           Azure Maps with terminal/truck pins
│   │   ├── tracking/      Main tracking dashboard page
│   │   ├── trips/         Customer trips page
│   │   ├── layout/        Dashboard shell/navigation
│   │   └── ui/            Shared UI primitives
│   ├── hooks/             useAuth, useFabricAgent
│   ├── lib/               MSAL config, API client, types
│   ├── config/            Sample questions for chat
│   ├── .env.example
│   └── Dockerfile
│
├── infra/             Azure infrastructure (Bicep + PowerShell)
│   ├── main.bicep         Resource definitions
│   └── deploy-resources.ps1
│
├── deploy/            Deployment scripts
│   ├── deploy-backend.ps1
│   └── deploy-frontend.ps1
│
└── docs/              Documentation
    ├── architecture-and-deployment.md
    └── EntraConfiguration.md
```

## Key Features

- **Live Terminal Map** — Terminals are loaded from Fabric via GraphQL and plotted on an Azure Maps instance
- **AI Chat** — Users can ask natural language questions answered by a Foundry Agent backed by a Fabric Data Agent and AI Search index
- **Truck Tracking** — Truck locations returned by the chat agent are plotted on the map in real time
- **Customer Trips** — Browse customers and their active trips via Fabric REST APIs
- **Secure by Default** — All API calls use Entra OBO flow; no service keys in the browser

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- An Entra app registration configured per [`docs/EntraConfiguration.md`](docs/EntraConfiguration.md)
- Access to an Azure AI Foundry project with a configured agent
- A Microsoft Fabric workspace with a GraphQL API and data

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env    # then fill in real values
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend

```powershell
cd react-app
npm install
copy .env.example .env.local    # then fill in real values
npm run dev
```

The frontend runs on `http://localhost:3000` and the backend on `http://localhost:8000`. CORS is pre-configured for this setup.

### Health Check

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

## Deployment

See [`docs/architecture-and-deployment.md`](docs/architecture-and-deployment.md) for full Azure Container Apps deployment instructions using the scripts in `infra/` and `deploy/`.

## Entra Configuration

See [`docs/EntraConfiguration.md`](docs/EntraConfiguration.md) for step-by-step Entra ID setup including:
- Exposing the API scope
- Creating client secrets/certificates
- Adding delegated API permissions
- Token version configuration
- Troubleshooting common auth errors
