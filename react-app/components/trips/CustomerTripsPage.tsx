'use client';

import { useEffect, useMemo, useState } from 'react';
import { getActiveTripsByCustomer, getCustomers } from '@/lib/fabricApi';

interface CustomerOption {
  id: string;
  name: string;
  raw: Record<string, unknown>;
}

function readString(
  source: Record<string, unknown>,
  keys: string[],
  fallback = ''
): string {
  for (const key of keys) {
    const value = source[key];
    if (typeof value === 'string' && value.trim()) {
      return value;
    }
  }
  return fallback;
}

function normalizeCustomer(record: Record<string, unknown>): CustomerOption | null {
  const id = readString(record, ['id', 'customerId', 'CustomerId', 'customer_id']);
  if (!id) return null;

  const name = readString(
    record,
    ['name', 'customerName', 'CustomerName', 'displayName'],
    id
  );

  return { id, name, raw: record };
}

function tripField(record: Record<string, unknown>, keys: string[]): string {
  return readString(record, keys, 'N/A');
}

export function CustomerTripsPage() {
  const [customers, setCustomers] = useState<CustomerOption[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [activeTrips, setActiveTrips] = useState<Record<string, unknown>[]>([]);
  const [isLoadingCustomers, setIsLoadingCustomers] = useState(true);
  const [isLoadingTrips, setIsLoadingTrips] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadCustomers = async () => {
      setIsLoadingCustomers(true);
      setError(null);

      try {
        const records = await getCustomers();
        if (cancelled) return;

        const normalized = records
          .map(normalizeCustomer)
          .filter((item): item is CustomerOption => item !== null)
          .sort((a, b) => a.name.localeCompare(b.name));

        setCustomers(normalized);
        if (normalized.length > 0) {
          setSelectedCustomerId(normalized[0].id);
        }
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : 'Failed to load customers';
        setError(message);
      } finally {
        if (!cancelled) {
          setIsLoadingCustomers(false);
        }
      }
    };

    loadCustomers();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadTrips = async () => {
      if (!selectedCustomerId) {
        setActiveTrips([]);
        return;
      }

      setIsLoadingTrips(true);
      setError(null);

      try {
        const trips = await getActiveTripsByCustomer(selectedCustomerId);
        if (!cancelled) {
          setActiveTrips(trips);
        }
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : 'Failed to load active trips';
        setError(message);
      } finally {
        if (!cancelled) {
          setIsLoadingTrips(false);
        }
      }
    };

    loadTrips();
    return () => {
      cancelled = true;
    };
  }, [selectedCustomerId]);

  const selectedCustomer = useMemo(
    () => customers.find((customer) => customer.id === selectedCustomerId) ?? null,
    [customers, selectedCustomerId]
  );

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight">Customer Active Trips</h2>
          <p className="text-sm text-muted-foreground">
            Select a customer to retrieve active trips from the backend Fabric Graph API.
          </p>
        </div>

        <div className="rounded-lg border bg-card p-4">
          <label htmlFor="customer-select" className="mb-2 block text-sm font-medium">
            Customer
          </label>
          <select
            id="customer-select"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            value={selectedCustomerId}
            onChange={(event) => setSelectedCustomerId(event.target.value)}
            disabled={isLoadingCustomers || customers.length === 0}
          >
            {customers.length === 0 && <option value="">No customers found</option>}
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name}
              </option>
            ))}
          </select>

          {selectedCustomer && (
            <p className="mt-2 text-xs text-muted-foreground">
              Selected customer ID: <span className="font-mono">{selectedCustomer.id}</span>
            </p>
          )}
        </div>

        {(isLoadingCustomers || isLoadingTrips) && (
          <div className="rounded-md border bg-background px-4 py-3 text-sm text-muted-foreground">
            Loading data...
          </div>
        )}

        {error && (
          <div className="rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="overflow-hidden rounded-lg border bg-card">
          <div className="border-b px-4 py-3 text-sm font-medium">Active Trips ({activeTrips.length})</div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Trip</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Route</th>
                  <th className="px-4 py-3">Driver</th>
                  <th className="px-4 py-3">Truck</th>
                  <th className="px-4 py-3">Load</th>
                  <th className="px-4 py-3">ETA</th>
                </tr>
              </thead>
              <tbody>
                {activeTrips.length === 0 && !isLoadingTrips ? (
                  <tr>
                    <td className="px-4 py-4 text-muted-foreground" colSpan={7}>
                      No active trips for the selected customer.
                    </td>
                  </tr>
                ) : (
                  activeTrips.map((trip, index) => {
                    const key = tripField(trip, ['tripId', 'id', 'TripId', 'trip_id']);
                    return (
                      <tr key={`${key}-${index}`} className="border-t">
                        <td className="px-4 py-3 font-medium">{key}</td>
                        <td className="px-4 py-3">{tripField(trip, ['status', 'Status'])}</td>
                        <td className="px-4 py-3">{tripField(trip, ['routeName', 'route', 'Route'])}</td>
                        <td className="px-4 py-3">{tripField(trip, ['driverName', 'driver', 'Driver'])}</td>
                        <td className="px-4 py-3">{tripField(trip, ['truckName', 'truck', 'Truck'])}</td>
                        <td className="px-4 py-3">{tripField(trip, ['loadName', 'load', 'Load'])}</td>
                        <td className="px-4 py-3">{tripField(trip, ['eta', 'ETA', 'estimatedArrival'])}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
