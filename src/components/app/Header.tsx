'use client';

import { Button } from '@/components/ui/button';
import Image from 'next/image';
import TokenMeter from '@/components/app/TokenMeter';
import TelemetryDetails from '@/components/app/TelemetryDetails';
import { toast } from '@/hooks/use-toast';
import { Settings } from 'lucide-react';
import SettingsDialog from '@/components/app/SettingsDialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

type HeaderProps = {
  onReset: () => void;
  onSaveCopy?: () => Promise<void>;
  onSaveNow?: () => Promise<void>;
};

export default function Header({ onReset, onSaveCopy, onSaveNow }: HeaderProps) {
  const handleSaveCopyAndReset = async () => {
    if (onSaveCopy) {
      await onSaveCopy();
    }
    onReset();
  };

  return (
    <header className="w-full bg-card shadow-lg p-4 md:p-6 border-b border-border/50">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Image
            src="/logo.png"
            alt="Next-Gen Engineering and Research Development"
            width={400}
            height={100}
            className="object-contain h-12 md:h-16 w-auto"
            priority
          />
          <div className="hidden md:block border-l border-muted-foreground/30 pl-4 ml-2">
            <h1 className="text-sm font-headline font-semibold text-foreground/80">
              Presentation Studio
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <TokenMeter />
          <TelemetryDetails />
          <SettingsDialog>
            <Button size="sm" variant="outline"><Settings className="mr-2 h-4 w-4"/>Settings</Button>
          </SettingsDialog>
          {onSaveNow && (
            <Button size="sm" variant="outline" onClick={async () => { await onSaveNow(); toast({ title: 'Saved', description: 'Progress saved.' }); }}>Save</Button>
          )}
          <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              className="font-medium hover:bg-primary/10 hover:text-primary hover:border-primary transition-colors"
            >
              Start Over
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Start over?</AlertDialogTitle>
              <AlertDialogDescription>
                You can save a copy of the current presentation first, or start fresh.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              {onSaveCopy && (
                <AlertDialogAction onClick={handleSaveCopyAndReset}>Save as Copy & Start Over</AlertDialogAction>
              )}
              <AlertDialogAction onClick={onReset}>Start Fresh</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
        </div>
      </div>
    </header>
  );
}
