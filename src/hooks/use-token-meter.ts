"use client";
import { useEffect, useState } from 'react';
import { getTotals, subscribe } from '@/lib/token-meter';

export function useTokenMeter() {
  const [totals, setTotals] = useState(getTotals());
  useEffect(() => {
    const off = subscribe(() => setTotals(getTotals()));
    return () => { off(); };
  }, []);
  return totals;
}
