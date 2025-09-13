'use client';

import { Loader2 } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';

type GeneratingSpinnerProps = {
  text?: string;
  current?: number;
  total?: number;
  onCancel?: () => void;
};

export default function GeneratingSpinner({ text = "Loading...", current, total, onCancel }: GeneratingSpinnerProps) {
  const hasProgress = typeof current === 'number' && typeof total === 'number' && total > 0;
  const percent = hasProgress ? Math.min(100, Math.round(((current as number) / (total as number)) * 100)) : undefined;
  return (
    <div className="flex flex-col items-center justify-center gap-4 text-center p-8 w-full max-w-md">
      <Loader2 className="h-16 w-16 animate-spin text-primary" />
      <p className="text-xl font-headline text-foreground/80">{text}</p>
      {hasProgress && (
        <div className="w-full space-y-2">
          <div className="text-sm text-muted-foreground">{current} / {total} slides</div>
          <Progress value={percent} />
        </div>
      )}
      {onCancel && (
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
      )}
    </div>
  );
}
