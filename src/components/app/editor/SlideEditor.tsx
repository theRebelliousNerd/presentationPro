'use client';
import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Slide } from '@/lib/types';
import ImageDisplay from './ImageDisplay';
import { rephraseNotes } from '@/lib/actions';
import { Sparkles, Loader2, Wand2 } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { addUsage, estimateTokens } from '@/lib/token-meter';
import { generateSlideContent } from '@/lib/actions';

type SlideEditorProps = {
  slide: Slide;
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void;
};

export default function SlideEditor({ slide, updateSlide }: SlideEditorProps) {
  const [isRephrasing, setIsRephrasing] = useState(false);
  
  const handleRephrase = async (tone: 'professional' | 'concise') => {
    setIsRephrasing(true);
    try {
      if (slide.speakerNotes) {
        addUsage({ model: 'gemini-2.5-flash', kind: 'prompt', tokens: estimateTokens(slide.speakerNotes), at: Date.now() } as any);
      }
      const response = await rephraseNotes(slide.speakerNotes, tone);
      updateSlide(slide.id, { speakerNotes: response.rephrasedSpeakerNotes });
      if (response.rephrasedSpeakerNotes) {
        addUsage({ model: 'gemini-2.5-flash', kind: 'completion', tokens: estimateTokens(response.rephrasedSpeakerNotes), at: Date.now() } as any);
      }
    } catch(e) {
      console.error("Failed to rephrase notes", e);
    } finally {
      setIsRephrasing(false);
    }
  };

  const handleImprove = async () => {
    try {
      addUsage({ model: 'gemini-2.5-flash', kind: 'prompt', tokens: estimateTokens(slide.title + (slide.speakerNotes||'')), at: Date.now() } as any);
      const assets: any[] = [];
      const [improved] = await generateSlideContent({ outline: [slide.title], existing: [{ title: slide.title, content: slide.content, speakerNotes: slide.speakerNotes }], assets });
      updateSlide(slide.id, {
        title: improved.title,
        content: improved.content,
        speakerNotes: improved.speakerNotes,
        imagePrompt: improved.imagePrompt,
      });
      addUsage({ model: 'gemini-2.5-flash', kind: 'completion', tokens: estimateTokens(improved.speakerNotes + improved.content.join('\n')), at: Date.now() } as any);
    } catch (e) {
      console.error('Improve slide failed', e);
    }
  };

  return (
    <Card className="flex-grow flex flex-col lg:flex-row gap-4 p-4 overflow-hidden shadow-inner">
      <div className="lg:w-1/2 h-full flex flex-col gap-4">
        <ImageDisplay slide={slide} updateSlide={updateSlide} />
        <div className="flex items-center gap-3">
          <Switch id={`ai-image-${slide.id}`} checked={slide.useGeneratedImage ?? true} onCheckedChange={(v) => updateSlide(slide.id, { useGeneratedImage: v })} />
          <label htmlFor={`ai-image-${slide.id}`} className="text-sm text-muted-foreground">Use AI-generated image</label>
        </div>
        <div>
          <Label htmlFor="image-prompt">Image Prompt</Label>
          <Textarea
            id="image-prompt"
            value={slide.imagePrompt}
            onChange={(e) => updateSlide(slide.id, { imagePrompt: e.target.value })}
            className="text-sm"
          />
        </div>
      </div>
      <div className="lg:w-1/2 h-full flex flex-col gap-4">
        <div>
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={slide.title}
            onChange={(e) => updateSlide(slide.id, { title: e.target.value })}
            className="text-xl font-headline"
          />
        </div>
        <div>
          <Label htmlFor="content">Content (bullet points)</Label>
          <Textarea
            id="content"
            value={slide.content.join('\n')}
            onChange={(e) => updateSlide(slide.id, { content: e.target.value.split('\n') })}
            className="min-h-[120px]"
          />
        </div>
        <div className="flex-grow flex flex-col gap-2">
          <div className="flex justify-between items-center">
             <Label htmlFor="speaker-notes">Speaker Notes</Label>
             <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={handleImprove}><Wand2 className="mr-2 h-3 w-3"/> AI Improve Slide</Button>
                {isRephrasing ? <Loader2 className="h-4 w-4 animate-spin" /> : (
                  <>
                    <Button size="sm" variant="outline" onClick={() => handleRephrase('professional')}><Sparkles className="mr-2 h-3 w-3"/> Professional</Button>
                    <Button size="sm" variant="outline" onClick={() => handleRephrase('concise')}><Sparkles className="mr-2 h-3 w-3"/> Concise</Button>
                  </>
                )}
             </div>
          </div>
          <Textarea
            id="speaker-notes"
            value={slide.speakerNotes}
            onChange={(e) => updateSlide(slide.id, { speakerNotes: e.target.value })}
            className="flex-grow"
          />
        </div>
      </div>
    </Card>
  );
}
