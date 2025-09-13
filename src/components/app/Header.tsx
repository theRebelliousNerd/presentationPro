'use client';

import { Button } from '@/components/ui/button';
import Image from 'next/image';

type HeaderProps = {
  onReset: () => void;
};

export default function Header({ onReset }: HeaderProps) {
  return (
    <header className="w-full bg-card shadow-sm p-4 border-b">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Image
            src="/logo-png.png"
            alt="Logo"
            width={180}
            height={40}
            className="object-contain"
          />
        </div>
        <Button variant="outline" onClick={onReset}>
          Start Over
        </Button>
      </div>
    </header>
  );
}
