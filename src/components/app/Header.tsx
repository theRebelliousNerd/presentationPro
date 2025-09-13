'use client';

import { Button } from '@/components/ui/button';
import Image from 'next/image';

type HeaderProps = {
  onReset: () => void;
};

export default function Header({ onReset }: HeaderProps) {
  return (
    <header className="w-full bg-card shadow-lg p-4 md:p-6 border-b border-border/50">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Image
            src="/logo.png"
            alt="Next-Gen Engineering and Research Development"
            width={200}
            height={48}
            className="object-contain"
            priority
          />
          <div className="hidden md:block border-l border-muted-foreground/30 pl-4 ml-2">
            <h1 className="text-sm font-headline font-semibold text-foreground/80">
              Presentation Studio
            </h1>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={onReset}
          className="font-medium hover:bg-primary/10 hover:text-primary hover:border-primary transition-colors"
        >
          Start Over
        </Button>
      </div>
    </header>
  );
}
