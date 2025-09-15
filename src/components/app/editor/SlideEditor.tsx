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
import { generateSlideContent, critiqueSlide } from '@/lib/actions';
import RichBullets from './RichBullets';
import { Badge } from '@/components/ui/badge';

type SlideEditorProps = {
  slide: Slide;
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void;
  assets?: { name: string; url: string; kind?: 'image' | 'document' | 'other' }[];
  constraints?: { citationsRequired?: boolean; slideDensity?: 'light'|'normal'|'dense'; mustInclude?: string[]; mustAvoid?: string[] };
};

export default function SlideEditor({ slide, updateSlide, assets = [], constraints }: SlideEditorProps) {
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
      const [improved] = await generateSlideContent({ outline: [slide.title], existing: [{ title: slide.title, content: slide.content, speakerNotes: slide.speakerNotes }], assets, constraints });
      const revised = await critiqueSlide({ title: improved.title, content: improved.content as any, speakerNotes: improved.speakerNotes, imagePrompt: improved.imagePrompt });
      updateSlide(slide.id, {
        title: revised.title,
        content: revised.content as any,
        speakerNotes: revised.speakerNotes,
        imagePrompt: improved.imagePrompt,
        assetImageUrl: (improved as any).useAssetImageUrl || (improved as any).assetImageUrl || undefined,
        imageUrl: (improved as any).useAssetImageUrl || (improved as any).assetImageUrl || slide.imageUrl,
        useGeneratedImage: !((improved as any).useAssetImageUrl || (improved as any).assetImageUrl),
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
        {/* Constraints indicator and overrides */}
        {constraints && (
          <div className="flex flex-col gap-2 text-xs p-2 rounded-md border">
            <div className="flex items-center justify-between">
              <div className="flex flex-wrap gap-2">
                {constraints.citationsRequired ? <Badge variant="secondary">Citations required</Badge> : null}
                {constraints.slideDensity ? <Badge variant="outline">Density: {constraints.slideDensity}</Badge> : null}
                {constraints.mustInclude?.length ? <Badge variant="outline" title={(constraints.mustInclude||[]).join(', ')}>Must include: {constraints.mustInclude.length}</Badge> : null}
                {constraints.mustAvoid?.length ? <Badge variant="outline" title={(constraints.mustAvoid||[]).join(', ')}>Avoid: {constraints.mustAvoid.length}</Badge> : null}
              </div>
              <div className="flex items-center gap-2">
                <Switch id={`use-constraints-${slide.id}`} checked={slide.useConstraints !== false} onCheckedChange={(v)=> updateSlide(slide.id, { useConstraints: v })} />
                <label htmlFor={`use-constraints-${slide.id}`} className="text-muted-foreground">Use global constraints</label>
              </div>
            </div>
            {slide.useConstraints === false && (
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-2 col-span-2">
                  <Switch id={`citations-${slide.id}`} checked={!!slide.constraintsOverride?.citationsRequired} onCheckedChange={(v)=> updateSlide(slide.id, { constraintsOverride: { ...(slide.constraintsOverride||{}), citationsRequired: v } })} />
                  <label htmlFor={`citations-${slide.id}`}>Citations required</label>
                </div>
                <div>
                  <Label className="text-[10px] text-muted-foreground">Density</Label>
                  <select className="w-full border rounded p-2 bg-background" value={slide.constraintsOverride?.slideDensity || ''} onChange={(e)=> updateSlide(slide.id, { constraintsOverride: { ...(slide.constraintsOverride||{}), slideDensity: (e.target.value||undefined) as any } })}>
                    <option value="">(default)</option>
                    <option value="light">Light</option>
                    <option value="normal">Normal</option>
                    <option value="dense">Dense</option>
                  </select>
                </div>
                <div>
                  <Label className="text-[10px] text-muted-foreground">Must include (one per line)</Label>
                  <Textarea className="min-h-[64px] text-xs" value={(slide.constraintsOverride?.mustInclude||[]).join('\n')} onChange={(e)=> updateSlide(slide.id, { constraintsOverride: { ...(slide.constraintsOverride||{}), mustInclude: e.target.value.split('\n').map(s=>s.trim()).filter(Boolean) } })} />
                </div>
                <div>
                  <Label className="text-[10px] text-muted-foreground">Avoid (one per line)</Label>
                  <Textarea className="min-h-[64px] text-xs" value={(slide.constraintsOverride?.mustAvoid||[]).join('\n')} onChange={(e)=> updateSlide(slide.id, { constraintsOverride: { ...(slide.constraintsOverride||{}), mustAvoid: e.target.value.split('\n').map(s=>s.trim()).filter(Boolean) } })} />
                </div>
              </div>
            )}
          </div>
        )}
        {/* Constraints indicator */}
        {constraints && (
          <div className="flex flex-wrap gap-2 text-xs">
            {constraints.citationsRequired ? <Badge variant="secondary">Citations required</Badge> : null}
            {constraints.slideDensity ? <Badge variant="outline">Density: {constraints.slideDensity}</Badge> : null}
            {constraints.mustInclude?.length ? <Badge variant="outline" title={(constraints.mustInclude||[]).join(', ')}>Must include: {constraints.mustInclude.length}</Badge> : null}
            {constraints.mustAvoid?.length ? <Badge variant="outline" title={(constraints.mustAvoid||[]).join(', ')}>Avoid: {constraints.mustAvoid.length}</Badge> : null}
          </div>
        )}
        <div className="md-surface md-elevation-1 rounded-xl p-2">
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
          <RichBullets value={slide.content} onChange={(v) => updateSlide(slide.id, { content: v })} />
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
