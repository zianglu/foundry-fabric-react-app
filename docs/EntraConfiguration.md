# Entra ID Configuration Guide

This document covers the Entra ID (Azure AD) configuration required for the React frontend + Python backend architecture using the On-Behalf-Of (OBO) flow.

## Architecture

```
React SPA (MSAL.js)
    │
    │  Bearer token (scope: api://<client-id>/access_as_user)
    ▼
Python Backend (FastAPI)
    │
    │  OBO token exchange
    ├──► Azure AI Foundry (scope: https://ai.azure.com/.default)
    └──► Microsoft Fabric (scope: https://api.fabric.microsoft.com/.default)
```

## App Registration Setup

A single app registration is used for both the SPA frontend and the backend OBO flow.

### 1. Create / Locate the App Registration

- **Azure Portal** → **Entra ID** → **App Registrations**
- Note the **Application (client) ID** and **Directory (tenant) ID**

### 2. Authentication Platform (SPA)

- Go to **Authentication** in the left nav
- Under **Single-page application**, add redirect URIs:
  - `http://localhost:3000` (local development)
  - Your production URL when deployed

### 3. Set Token Version to v2.0

This is critical — without it, tokens use the v1.0 issuer (`https://sts.windows.net/{tenant}/`) which the backend's v2.0 OpenID validation rejects.

- Go to **Manifest** in the left nav
- Inside the `"api"` section, find `"requestedAccessTokenVersion"`
- Change it from `null` to `2`
- Click **Save**

### 4. Expose an API

- Go to **Expose an API** in the left nav
- Click **Set** next to "Application ID URI" → accept the default `api://<client-id>`
- Click **+ Add a scope**:
  - **Scope name**: `access_as_user`
  - **Who can consent**: Admins and users
  - **Admin consent display name**: Access backend as signed-in user
  - **Admin consent description**: Allow the app to access the backend API on behalf of the signed-in user
  - **User consent display name**: Access backend on your behalf
  - **User consent description**: Allow the app to access the backend API on your behalf
  - **State**: Enabled
- Under **Authorized client applications**, click **+ Add a client application**:
  - **Client ID**: `<your-client-id>` (the same app — this pre-authorizes the SPA so users skip the consent prompt for the `access_as_user` scope)
  - Check the `access_as_user` scope checkbox

### 5. Create a Client Secret (for backend OBO)

- Go to **Certificates & secrets** in the left nav
- Click **+ New client secret**
- Give it a description (e.g., `Backend OBO local dev`) and pick an expiry
- **Copy the secret Value immediately** — you won't see it again
- Store it in the backend `.env` file as `BACKEND_CLIENT_SECRET`

### 6. Add API Permissions

- Go to **API permissions** in the left nav

**Azure AI Foundry:**
- Click **+ Add a permission** → **APIs my organization uses** → search for `Azure AI`
- Select **Delegated permissions** → check `user_impersonation` → **Add permissions**

**Microsoft Fabric (Power BI Service):**
- Click **+ Add a permission** → **APIs my organization uses** → search for `Power BI Service`
- Select **Delegated permissions** → check `Dataset.Read.All` (and optionally `Workspace.Read.All`) → **Add permissions**

### 7. Grant Admin Consent

**Option A — Portal button:**
- On the **API permissions** page, click **Grant admin consent for [tenant]**

**Option B — Admin consent URL (if the button is grayed out):**
```
https://login.microsoftonline.com/<tenant-id>/adminconsent?client_id=<client-id>
```

**Option C — User consent (if you lack admin rights):**
- If admin consent is unavailable, the frontend login flow triggers user consent via `extraScopesToConsent` in the MSAL login request
- Users will see a consent prompt the first time they sign in

### 8. Revoking User Consent (for re-testing)

If you need to re-trigger the consent prompt:
1. Go to **https://myaccount.microsoft.com/**
2. Click **Permissions**
3. Find the app and click **Revoke**

Alternatively, in the portal:
- **Entra ID** → **Enterprise Applications** → find the app → **Users and groups** → remove your assignment

## Environment Configuration

### Frontend (`react-app/.env.local`)

```env
NEXT_PUBLIC_ENTRA_CLIENT_ID=<client-id>
NEXT_PUBLIC_ENTRA_TENANT_ID=<tenant-id>
NEXT_PUBLIC_API_SCOPE=api://<client-id>/access_as_user
NEXT_PUBLIC_BACKEND_API_BASE_URL=http://localhost:8000
```

### Backend (`backend/.env`)

```env
# Entra
AZURE_TENANT_ID=<tenant-id>
BACKEND_CLIENT_ID=<client-id>
BACKEND_API_AUDIENCE=api://<client-id>
BACKEND_ALLOWED_AUDIENCES=api://<client-id>,<client-id>
BACKEND_REQUIRED_SCOPE=access_as_user
BACKEND_CLIENT_SECRET=<client-secret>

# CORS (must include the frontend origin)
CORS_ORIGINS=http://localhost:3000
```

> **Note on BACKEND_ALLOWED_AUDIENCES**: v2.0 tokens may use either `api://<client-id>` or the bare `<client-id>` as the audience claim. Listing both ensures validation succeeds regardless.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid bearer token: Invalid issuer` | Token is v1.0 but backend validates v2.0 | Set `requestedAccessTokenVersion` to `2` in the app manifest |
| `Invalid bearer token: Audience doesn't match` | Token `aud` claim doesn't match backend config | Add both `api://<client-id>` and `<client-id>` to `BACKEND_ALLOWED_AUDIENCES` |
| `AADSTS65001: The user or administrator has not consented` | Missing consent for downstream API permissions | Grant admin consent or trigger user consent via `extraScopesToConsent` |
| `OBO token exchange failed` | Client secret is missing or wrong, or app lacks API permissions | Verify `BACKEND_CLIENT_SECRET` and check API permissions in the portal |
| CORS errors in browser | Backend doesn't allow the frontend origin | Ensure `CORS_ORIGINS` includes `http://localhost:3000` |
