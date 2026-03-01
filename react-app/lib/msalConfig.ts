import { Configuration, PublicClientApplication } from '@azure/msal-browser';

const clientId = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID;
const tenantId = process.env.NEXT_PUBLIC_ENTRA_TENANT_ID;
const apiScope = process.env.NEXT_PUBLIC_API_SCOPE;

if (!clientId || !tenantId || !apiScope) {
  throw new Error(
    'Missing required environment variables: NEXT_PUBLIC_ENTRA_CLIENT_ID, NEXT_PUBLIC_ENTRA_TENANT_ID, NEXT_PUBLIC_API_SCOPE'
  );
}

export const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000',
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
};

export const loginRequest = {
  scopes: ['openid', 'profile', apiScope],
  extraScopesToConsent: [
    'https://ai.azure.com/user_impersonation',
    'https://api.fabric.microsoft.com/Item.ReadWrite.All',
  ],
};

export const tokenRequest = {
  scopes: [apiScope],
};

export const msalInstance = new PublicClientApplication(msalConfig);
