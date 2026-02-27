import { msalInstance, tokenRequest } from './msalConfig';
import { EntityListResponse, FabricQueryResponse } from './types';

const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_API_BASE_URL;

if (!backendBaseUrl) {
  throw new Error('Missing required environment variable: NEXT_PUBLIC_BACKEND_API_BASE_URL');
}

export async function acquireToken(): Promise<string> {
  const accounts = msalInstance.getAllAccounts();
  if (accounts.length === 0) {
    throw new Error('No authenticated accounts found');
  }

  const request = {
    ...tokenRequest,
    account: accounts[0],
  };

  try {
    const response = await msalInstance.acquireTokenSilent(request);
    return response.accessToken;
  } catch {
    const response = await msalInstance.acquireTokenPopup(request);
    return response.accessToken;
  }
}

async function apiRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' = 'GET',
  body?: unknown
): Promise<T> {
  const token = await acquireToken();

  const response = await fetch(`${backendBaseUrl}${endpoint}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Backend request failed: ${response.status} ${response.statusText} - ${errorText}`);
  }

  const text = await response.text();
  if (!text) {
    return undefined as T;
  }

  return JSON.parse(text) as T;
}

export async function queryDataAgent(question: string): Promise<FabricQueryResponse> {
  return apiRequest<FabricQueryResponse>('/api/chat', 'POST', { question });
}

export async function getCustomers(): Promise<Record<string, unknown>[]> {
  const response = await apiRequest<EntityListResponse>('/api/customers', 'GET');
  return response.items ?? [];
}

export async function getActiveTripsByCustomer(customerId: string): Promise<Record<string, unknown>[]> {
  const encodedId = encodeURIComponent(customerId);
  const response = await apiRequest<EntityListResponse>(`/api/customers/${encodedId}/active-trips`, 'GET');
  return response.items ?? [];
}
