'use client';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { getPresentationOutline } from '@/lib/actions';
import { Check, ArrowLeft } from 'lucide-react';

type OutlineApprovalProps = {
  clarifiedGoals: string;
  onApprove: (outline: string[]) => void;
  onGoBack: () => void;
};

export default function OutlineApproval({ clarifiedGoals, onApprove, onGoBack }: OutlineApprovalProps) {
  const [outline, setOutline] = useState<string[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOutline = async () => {
      try {
        const response = await getPresentationOutline(clarifiedGoals);
        setOutline(response.slideTitles);
      } catch (err) {
        setError('Failed to generate an outline. Please try going back and refining your goals.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchOutline();
  }, [clarifiedGoals]);

  return (
    <Card className="w-full max-w-2xl shadow-2xl">
      <CardHeader>
        <CardTitle className="font-headline text-3xl">Proposed Outline</CardTitle>
        <CardDescription>
          Here is the slide-by-slide structure I've generated based on our conversation.
        </CardDescription>
      </CardHeader>
      <CardContent className="min-h-[250px]">
        {isLoading && (
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
          </div>
        )}
        {error && <p className="text-destructive">{error}</p>}
        {outline && (
          <ol className="space-y-3 list-decimal list-inside">
            {outline.map((title, index) => (
              <li key={index} className="p-3 bg-muted rounded-md text-foreground/90">
                {title}
              </li>
            ))}
          </ol>
        )}
      </CardContent>
      <CardFooter className="flex flex-col sm:flex-row gap-4">
        <Button variant="outline" onClick={onGoBack} className="w-full sm:w-auto">
          <ArrowLeft className="mr-2 h-4 w-4" /> Go Back & Edit
        </Button>
        <Button onClick={() => outline && onApprove(outline)} disabled={!outline || isLoading} className="w-full sm:w-auto flex-grow">
          <Check className="mr-2 h-4 w-4" /> Looks Good, Generate Slides
        </Button>
      </CardFooter>
    </Card>
  );
}
