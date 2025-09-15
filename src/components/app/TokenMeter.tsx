'use client';
import { useEffect, useState } from 'react';
import { useTokenMeter } from '@/hooks/use-token-meter';
import { resetUsage, getPricing } from '@/lib/token-meter';
import { Button } from '@/components/ui/button';

export default function TokenMeter() {
  const totals = useTokenMeter();
  // Stabilize pricing between SSR and client to avoid hydration mismatch
  const [isConfigured, setIsConfigured] = useState(false);
  useEffect(() => {
    try {
      const p = getPricing();
      setIsConfigured((p.pricePrompt || 0) > 0 || (p.priceCompletion || 0) > 0 || (p.priceImageCall || 0) > 0);
    } catch {}
  }, []);
  return (
    <div className="flex items-center gap-3 text-sm bg-muted px-3 py-1 rounded-md">
      <div>In: <b>{totals.tokensPrompt}</b></div>
      <div>Out: <b>{totals.tokensCompletion}</b></div>
      <div>Img: <b>{totals.imageCalls}</b></div>
      <div>
        Cost: <b>{isConfigured ? `$${totals.usd.toFixed(4)}` : 'Set pricing'}</b>
      </div>
      <Button size="sm" variant="outline" onClick={() => resetUsage()}>Reset</Button>
    </div>
  );
}
