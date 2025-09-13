'use client';

import { Loader2 } from 'lucide-react';

type GeneratingSpinnerProps = {
  text?: string;
};

export default function GeneratingSpinner({ text = "Loading..." }: GeneratingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 text-center p-8">
      <Loader2 className="h-16 w-16 animate-spin text-primary" />
      <p className="text-xl font-headline text-foreground/80">{text}</p>
    </div>
  );
}
