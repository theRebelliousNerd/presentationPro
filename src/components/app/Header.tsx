'use client';

import { Button } from '@/components/ui/button';
import { Presentation } from 'lucide-react';

type HeaderProps = {
  onReset: () => void;
};

export default function Header({ onReset }: HeaderProps) {
  return (
    <header className="w-full bg-card shadow-sm p-4 border-b">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Presentation className="h-8 w-8 text-primary" />
          <h1 className="text-xl md:text-2xl font-headline font-semibold text-foreground">
            Gemini Presentation Studio
          </h1>
        </div>
        <Button variant="outline" onClick={onReset}>
          Start Over
        </Button>
      </div>
    </header>
  );
}
