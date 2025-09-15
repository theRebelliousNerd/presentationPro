'use client';

import { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { getPricing } from '@/lib/token-meter';

type Entry = { model: string; kind: 'prompt'|'completion'|'image_call'; tokens?: number; count?: number; at: number };

function readEvents(): Entry[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem('tokenMeter.v1');
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export default function TelemetryDetails() {
  const [open, setOpen] = useState(false);
  const [events, setEvents] = useState<Entry[]>([]);
  const pricing = getPricing();

  useEffect(() => {
    if (open) setEvents(readEvents().slice(-50).reverse());
  }, [open]);

  const costOf = (e: Entry) => {
    if (e.kind === 'image_call') return (pricing.priceImageCall || 0) * (e.count || 1);
    const perM = e.kind === 'prompt' ? (pricing.pricePrompt || 0) : (pricing.priceCompletion || 0);
    return ((e.tokens || 0) / 1_000_000) * perM;
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">Details</Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Telemetry Details</DialogTitle>
        </DialogHeader>
        <div className="max-h-[60vh] overflow-auto text-sm">
          <div className="grid grid-cols-6 gap-2 font-medium pb-2 border-b">
            <div>Time</div>
            <div>Kind</div>
            <div>Model</div>
            <div className="text-right">Tokens</div>
            <div className="text-right">Count</div>
            <div className="text-right">Cost</div>
          </div>
          {events.map((e, i) => (
            <div key={i} className="grid grid-cols-6 gap-2 py-1 border-b border-muted/30">
              <div>{new Date(e.at).toLocaleTimeString()}</div>
              <div>{e.kind}</div>
              <div className="truncate" title={e.model}>{e.model}</div>
              <div className="text-right">{e.tokens ?? '-'}</div>
              <div className="text-right">{e.count ?? '-'}</div>
              <div className="text-right">${costOf(e).toFixed(6)}</div>
            </div>
          ))}
          {events.length === 0 && <div className="text-muted-foreground py-6">No usage yet.</div>}
        </div>
      </DialogContent>
    </Dialog>
  );
}

