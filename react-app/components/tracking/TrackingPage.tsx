'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { Terminal } from '@/components/map/AzureMap';
import { TruckPin } from '@/components/map/AzureMap';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { TruckLocation } from '@/hooks/useFabricAgent';
import { getTerminals } from '@/lib/fabricApi';

// Dynamic import to avoid SSR issues with Azure Maps
const AzureMap = dynamic(
  () => import('@/components/map/AzureMap').then((mod) => mod.AzureMap),
  { ssr: false }
);



export function TrackingPage() {
  const [terminals, setTerminals] = useState<Terminal[]>([]);
  const [trucks, setTrucks] = useState<TruckPin[]>([]);
  const [isLoadingTerminals, setIsLoadingTerminals] = useState(true);
  const chatInputRef = useRef<HTMLInputElement>(null);

  const handleTrucksDetected = useCallback((detected: TruckLocation[]) => {
    setTrucks(detected.map((t) => ({
      label: t.label,
      latitude: t.latitude,
      longitude: t.longitude,
    })));
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadTerminals() {
      try {
        console.log('Loading terminals from Fabric GraphQL...');
        const items = await getTerminals();
        if (cancelled) return;

        const parsed: Terminal[] = items
          .filter((item) => item.name != null && item.latitude != null && item.longitude != null)
          .map((item) => ({
            name: String(item.name),
            latitude: Number(item.latitude),
            longitude: Number(item.longitude),
          }));

        console.log(`Loaded ${parsed.length} terminals from Fabric`);
        setTerminals(parsed);
      } catch (err) {
        console.error('Failed to load terminals:', err);
      }
    }

    loadTerminals().finally(() => {
      if (!cancelled) {
        setIsLoadingTerminals(false);
        setTimeout(() => chatInputRef.current?.focus(), 100);
      }
    });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="flex h-full">
      {/* Map panel - 60% */}
      <div className="w-[60%] h-full border-r">
        <AzureMap terminals={terminals} trucks={trucks} isLoading={isLoadingTerminals} />
      </div>

      {/* Chat panel - 40% */}
      <div className="w-[40%] h-full">
        <ChatInterface inputRef={chatInputRef} onTrucksDetected={handleTrucksDetected} />
      </div>
    </div>
  );
}
