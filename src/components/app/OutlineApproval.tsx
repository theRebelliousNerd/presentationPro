'use client';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { getPresentationOutline } from '@/lib/actions';
import type { Presentation } from '@/lib/types';
import { addUsage, estimateTokens } from '@/lib/token-meter';
import { Check, ArrowLeft, ArrowDown, ArrowUp, Plus, Trash2 } from 'lucide-react';
import { Input } from '@/components/ui/input';

type OutlineApprovalProps = {
  clarifiedGoals: string;
  initialInput?: Presentation['initialInput'];
  presentationId?: string;
  sessionId?: string;
  workflowState?: any;
  onWorkflowMeta?: (meta: { workflowSessionId?: string; workflowState?: any; workflowTrace?: any[] }) => void;
  onApprove: (outline: string[]) => void;
  onGoBack: () => void;
};

export default function OutlineApproval({ clarifiedGoals, initialInput, presentationId, sessionId, workflowState, onWorkflowMeta, onApprove, onGoBack }: OutlineApprovalProps) {
  const [outline, setOutline] = useState<string[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOutline = async () => {
      try {
        if (clarifiedGoals) {
          addUsage({ model: 'gemini-2.5-flash', kind: 'prompt', tokens: estimateTokens(clarifiedGoals), at: Date.now() } as any);
        }
        const response = await getPresentationOutline(clarifiedGoals, {
          presentationId,
          length: initialInput?.length,
          audience: initialInput?.audience,
          tone: initialInput?.tone,
          template: initialInput?.template,
          sessionId,
          workflowState,
        });
        onWorkflowMeta?.({
          workflowSessionId: response.workflowSessionId,
          workflowState: response.workflowState,
          workflowTrace: response.workflowTrace,
        });
        setOutline(response.slideTitles);
        const usage = (response as any)._usage;
        if (usage && usage.completionTokens) {
          addUsage({ model: usage.model || 'gemini-2.5-flash', kind: 'completion', tokens: usage.completionTokens, at: Date.now() } as any);
        } else {
          const outText = response.slideTitles.join('\n');
          addUsage({ model: 'gemini-2.5-flash', kind: 'completion', tokens: estimateTokens(outText), at: Date.now() } as any);
        }
      } catch (err) {
        setError('Failed to generate an outline. Please try going back and refining your goals.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchOutline();
  }, [clarifiedGoals, initialInput, presentationId]);

  return (
    <Card className="w-full max-w-2xl shadow-2xl">
      <CardHeader>
        <CardTitle className="font-headline text-3xl">Proposed Outline</CardTitle>
        <CardDescription>
          Review and edit the slide-by-slide structure before generating content.
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
          <div className="space-y-3">
            {outline.map((title, index) => (
              <div key={index} className="p-3 bg-muted rounded-md grid grid-cols-[1fr_auto] gap-2 items-center">
                <Input
                  value={title}
                  onChange={(e) => {
                    const newOutline = [...outline];
                    newOutline[index] = e.target.value;
                    setOutline(newOutline);
                  }}
                  className="bg-background"
                />
                <div className="flex gap-1">
                  <Button variant="outline" size="icon" disabled={index===0} onClick={() => {
                    const newOutline = [...outline];
                    const [item] = newOutline.splice(index,1);
                    newOutline.splice(index-1,0,item);
                    setOutline(newOutline);
                  }}>
                    <ArrowUp className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" disabled={index===outline.length-1} onClick={() => {
                    const newOutline = [...outline];
                    const [item] = newOutline.splice(index,1);
                    newOutline.splice(index+1,0,item);
                    setOutline(newOutline);
                  }}>
                    <ArrowDown className="h-4 w-4" />
                  </Button>
                  <Button variant="destructive" size="icon" onClick={() => {
                    const newOutline = outline.filter((_,i)=>i!==index);
                    setOutline(newOutline);
                  }}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setOutline([...(outline||[]), 'New Slide'] )}>
                <Plus className="mr-2 h-4 w-4" /> Add Slide
              </Button>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex flex-col sm:flex-row gap-4">
        <Button variant="outline" onClick={onGoBack} className="w-full sm:w-auto">
          <ArrowLeft className="mr-2 h-4 w-4" /> Go Back & Edit
        </Button>
        <Button onClick={() => outline && onApprove(outline.filter(t=>t.trim().length>0))} disabled={!outline || outline.length===0 || isLoading} className="w-full sm:w-auto flex-grow">
          <Check className="mr-2 h-4 w-4" /> Looks Good, Generate Slides
        </Button>
      </CardFooter>
    </Card>
  );
}
