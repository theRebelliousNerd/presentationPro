'use client';
import { ReactNode, useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { setPricing } from '@/lib/token-meter';

export default function SettingsDialog({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [pricePrompt, setPricePrompt] = useState<string>('0');
  const [priceCompletion, setPriceCompletion] = useState<string>('0');
  const [priceImageCall, setPriceImageCall] = useState<string>('0');
  const [theme, setTheme] = useState<string>('brand');

  useEffect(() => {
    try {
      const raw = localStorage.getItem('tokenMeter.pricing');
      if (raw) {
        const p = JSON.parse(raw);
        if (p.pricePrompt != null) setPricePrompt(String(p.pricePrompt));
        if (p.priceCompletion != null) setPriceCompletion(String(p.priceCompletion));
        if (p.priceImageCall != null) setPriceImageCall(String(p.priceImageCall));
      }
    } catch {}
    try {
      const t = localStorage.getItem('app.theme');
      if (t) setTheme(t);
    } catch {}
  }, [open]);

  const onSave = () => {
    setPricing({
      pricePrompt: Number(pricePrompt || '0'),
      priceCompletion: Number(priceCompletion || '0'),
      priceImageCall: Number(priceImageCall || '0'),
    });
    try {
      localStorage.setItem('app.theme', theme);
    } catch {}
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>Configure token pricing and theme palette (dev-only overrides).</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="pp">Text Prompt $/1M tokens</Label>
              <Input id="pp" value={pricePrompt} onChange={(e) => setPricePrompt(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="pc">Completion $/1M tokens</Label>
              <Input id="pc" value={priceCompletion} onChange={(e) => setPriceCompletion(e.target.value)} />
            </div>
          </div>
          <div>
            <Label htmlFor="pi">Image call $/call</Label>
            <Input id="pi" value={priceImageCall} onChange={(e) => setPriceImageCall(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="theme">Theme</Label>
            <select id="theme" className="w-full border rounded p-2 bg-background" value={theme} onChange={(e)=>setTheme(e.target.value)}>
              <option value="brand">Brand</option>
              <option value="muted">Muted</option>
              <option value="dark">Dark</option>
            </select>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={onSave}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

