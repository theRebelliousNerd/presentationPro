"use client";
import { useEffect, useState } from 'react';
import { getTotals, subscribe } from '@/lib/token-meter';

export function useTokenMeter() {
  // Stabilize initial render between SSR and client to avoid hydration mismatch.
  const [totals, setTotals] = useState(() => ({
    tokensPrompt: 0,
    tokensCompletion: 0,
    imageCalls: 0,
    usd: 0,
  }));
  useEffect(() => {
    // Set actual totals on mount and subscribe for changes.
    setTotals(getTotals());
    const off = subscribe(() => setTotals(getTotals()));
    return () => { off(); };
  }, []);
  return totals;
}
