# Contoso Trucking Frontend (Next.js)

Next.js UI for the Foundry + Fabric trucking demo. The frontend authenticates users with Entra ID and calls a Python backend API for all data and AI operations.

## What changed

- Removed direct browser calls to Fabric REST/Data Agent APIs
- Added backend API integration (`NEXT_PUBLIC_BACKEND_API_BASE_URL`)
- Added Trips page:
  - loads customers from backend `GET /api/customers`
  - loads active trips from backend `GET /api/customers/{id}/active-trips`

## Prerequisites

- Node.js 20+
- Backend API running and reachable
- Entra app registration for SPA auth

## Environment

Copy `.env.example` to `.env.local` and fill values:

```env
NEXT_PUBLIC_ENTRA_CLIENT_ID=<frontend-app-client-id>
NEXT_PUBLIC_ENTRA_TENANT_ID=<tenant-id>
NEXT_PUBLIC_API_SCOPE=api://<backend-app-client-id>/access_as_user
NEXT_PUBLIC_BACKEND_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_AZURE_MAPS_KEY=<optional>
```

## Run locally

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
npm start
```
