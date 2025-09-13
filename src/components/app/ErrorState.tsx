'use client';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

type ErrorStateProps = {
  onReset: () => void;
  message?: string;
};

export default function ErrorState({ onReset, message }: ErrorStateProps) {
  return (
    <Card className="w-full max-w-lg text-center shadow-2xl">
      <CardHeader>
        <div className="mx-auto bg-destructive/10 p-3 rounded-full">
            <AlertTriangle className="h-10 w-10 text-destructive" />
        </div>
        <CardTitle className="font-headline text-3xl mt-4">Oops! Something went wrong.</CardTitle>
        <CardDescription>
          {message || "We encountered an unexpected issue. Please try starting over."}
        </CardDescription>
      </CardHeader>
      <CardContent>
      </CardContent>
      <CardFooter>
        <Button onClick={onReset} className="w-full">
          Start Over
        </Button>
      </CardFooter>
    </Card>
  );
}
