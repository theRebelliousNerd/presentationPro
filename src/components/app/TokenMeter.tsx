'use client';
import { useTokenMeter } from '@/hooks/use-token-meter';
import { resetUsage } from '@/lib/token-meter';
import { Button } from '@/components/ui/button';

export default function TokenMeter() {
  const totals = useTokenMeter();
  return (
    <div className="flex items-center gap-3 text-sm bg-muted px-3 py-1 rounded-md">
      <div>Tokens: <b>{totals.tokensPrompt + totals.tokensCompletion}</b></div>
      <div>Est: <b>${totals.usd.toFixed(4)}</b></div>
      <Button size="sm" variant="outline" onClick={() => resetUsage()}>Reset</Button>
    </div>
  );
}
