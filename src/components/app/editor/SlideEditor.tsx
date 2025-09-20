'use client';
import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Slide } from '@/lib/types';
import ImageDisplay from './ImageDisplay';
import { rephraseNotes, critiqueSlide } from '@/lib/actions';
import { Sparkles, Loader2, Wand2, Search, Crosshair } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { addUsage, estimateTokens } from '@/lib/token-meter';
import { generateSlideContent } from '@/lib/actions';
import RichBullets from './RichBullets';
import { Badge } from '@/components/ui/badge';
import DesignPanel from './design/DesignPanel';
import PlacementSuggestions from './design/PlacementSuggestions';
import QualityBadge, { type QualityMetrics } from './QualityBadge';
import { resolveAdkBaseUrl } from '@/lib/base-url';

type SlideEditorProps = {
  slide: Slide;
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void;
  assets?: { name: string; url: string; kind?: 'image' | 'document' | 'other' }[];
  constraints?: { citationsRequired?: boolean; slideDensity?: 'light'|'normal'|'dense'; mustInclude?: string[]; mustAvoid?: string[] };
  presentationId?: string;
  slideIndex?: number;
  graphics?: { name: string; url: string }[];
  applyTokensToAll?: (tokens: any) => void;
};

export default function SlideEditor({ slide, updateSlide, assets = [], constraints, presentationId, slideIndex, graphics = [], applyTokensToAll }: SlideEditorProps) {
  const [isRephrasing, setIsRephrasing] = useState(false);
  const [showIconPicker, setShowIconPicker] = useState(false);
  const [iconQuery, setIconQuery] = useState('');
  const [iconResults, setIconResults] = useState<{ pack: string; name: string; url: string }[]>([]);
  const [showPatternPicker, setShowPatternPicker] = useState(false);
  const [patternName, setPatternName] = useState('topography');
  const [reviews, setReviews] = useState<{ created_at?: string; agent_source?: string; review_data?: { issues?: string[]; suggestions?: string[] } }[]>([]);
  const [selectedGraphic, setSelectedGraphic] = useState<string>('');
  const [showCompositionGrids, setShowCompositionGrids] = useState(false);
  
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
      const result = await generateSlideContent({ outline: [slide.title], existing: [{ title: slide.title, content: slide.content, speakerNotes: slide.speakerNotes }], assets, constraints, presentationId });
      const improved = (result.slides && result.slides[0]) || { title: slide.title, content: slide.content, speakerNotes: slide.speakerNotes, imagePrompt: slide.imagePrompt } as any;
      const crit = await critiqueSlide({ title: improved.title, content: improved.content as any, speakerNotes: improved.speakerNotes, imagePrompt: improved.imagePrompt });
      updateSlide(slide.id, {
        title: crit.title,
        content: crit.content as any,
        speakerNotes: crit.speakerNotes,
        imagePrompt: improved.imagePrompt,
        assetImageUrl: (improved as any).useAssetImageUrl || (improved as any).assetImageUrl || undefined,
        imageUrl: (improved as any).useAssetImageUrl || (improved as any).assetImageUrl || slide.imageUrl,
        useGeneratedImage: !((improved as any).useAssetImageUrl || (improved as any).assetImageUrl),
        criticReview: crit._review,
      });
      addUsage({ model: 'gemini-2.5-flash', kind: 'completion', tokens: estimateTokens(improved.speakerNotes + improved.content.join('\n')), at: Date.now() } as any);
    } catch (e) {
      console.error('Improve slide failed', e);
    }
  };

  const applySuggestions = async () => {
    await handleImprove();
  }

  // Load review history
  useEffect(() => {
    (async () => {
      try {
        if (!presentationId || typeof slideIndex !== 'number') return;
        const base = resolveAdkBaseUrl();
        const res = await fetch(`${base}/v1/arango/presentations/${encodeURIComponent(presentationId)}/slides/${slideIndex}/reviews?limit=5`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.success && Array.isArray(data.data)) setReviews(data.data);
        }
      } catch {}
    })();
  }, [presentationId, slideIndex, slide.id]);

  return (
    <Card className="flex-grow flex flex-col lg:flex-row gap-3 p-3 overflow-hidden shadow-none rounded-none border-0">
      <div className="lg:w-1/2 h-full flex flex-col gap-4">
        <ImageDisplay slide={slide} updateSlide={updateSlide} />

        {/* Quality Badge - show if we have quality metrics */}
        {slide.qualityMetrics && (
          <QualityBadge
            metrics={slide.qualityMetrics}
            variant="compact"
            showImprovements={true}
          />
        )}

        {/* Toggle for composition grids */}
        {slide.designSpec?.placementCandidates && slide.designSpec.placementCandidates.length > 0 && (
          <div className="flex items-center gap-2">
            <Switch
              id={`show-composition-${slide.id}`}
              checked={showCompositionGrids}
              onCheckedChange={setShowCompositionGrids}
            />
            <label htmlFor={`show-composition-${slide.id}`} className="text-sm text-muted-foreground cursor-pointer">
              Show composition assistant
            </label>
          </div>
        )}

        {/* PlacementSuggestions component */}
        {showCompositionGrids && slide.designSpec?.placementCandidates && slide.designSpec.placementCandidates.length > 0 && (
          <PlacementSuggestions
            slide={slide}
            updateSlide={updateSlide}
            onApplyPlacement={(placement) => {
              // Apply placement to slide's design spec
              updateSlide(slide.id, {
                designSpec: {
                  ...slide.designSpec,
                  appliedPlacement: placement,
                }
              });
              // Optionally trigger a re-render or animation
              console.log('Placement applied:', placement);
            }}
          />
        )}

        <DesignPanel slide={slide} updateSlide={updateSlide} applyTokensToAll={applyTokensToAll} />
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
                <Button size="sm" variant="outline" onClick={()=>setShowIconPicker(v=>!v)}><Search className="mr-2 h-3 w-3"/>Insert Icon</Button>
                <Button size="sm" variant="outline" onClick={handleImprove}><Wand2 className="mr-2 h-3 w-3"/> AI Improve Slide</Button>
                {isRephrasing ? <Loader2 className="h-4 w-4 animate-spin" /> : (
                  <>
                    <Button size="sm" variant="outline" onClick={() => handleRephrase('professional')}><Sparkles className="mr-2 h-3 w-3"/> Professional</Button>
                    <Button size="sm" variant="outline" onClick={() => handleRephrase('concise')}><Sparkles className="mr-2 h-3 w-3"/> Concise</Button>
                  </>
                )}
             </div>
          </div>
          {showIconPicker ? (
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="flex items-center gap-2 mb-2">
                <input className="w-full p-2 border rounded" placeholder="Search icons (e.g., check, info, chart)" value={iconQuery} onChange={(e)=>setIconQuery(e.target.value)} />
                <Button size="sm" onClick={async ()=>{
                  const pack = (typeof window !== 'undefined' && (localStorage.getItem('app.iconPack') as any)) || 'lucide'
                  const base = resolveAdkBaseUrl();
                  const res = await fetch(`${base}/v1/assets/icons/list`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pack, q: iconQuery, limit: 12 }) })
                  if (res.ok) {
                    const arr = await res.json(); setIconResults(arr || [])
                  }
                }}>Search</Button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {iconResults.map((it, idx)=>(
                  <Button key={idx} variant="outline" className="justify-start" onClick={async ()=>{
                    const base = resolveAdkBaseUrl();
                    const res = await fetch(`${base}/v1/assets/icons/get`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pack: it.pack, name: it.name }) })
                    if (res.ok) {
                      const { svg } = await res.json()
                      const inner = svg.replace(/^[\s\S]*?<svg[^>]*>/,'').replace(/<\/svg>[\s\S]*$/,'')
                      const sizeSel = (typeof window !== 'undefined' && (localStorage.getItem('app.iconSize') as any)) || 'medium'
                      const posSel = (typeof window !== 'undefined' && (localStorage.getItem('app.iconPos') as any)) || 'top-right'
                      const size = sizeSel === 'small' ? 80 : sizeSel === 'large' ? 180 : 120
                      const x = posSel === 'top-left' || posSel === 'bottom-left' ? 40 : posSel === 'center' ? Math.max(0, (1280 - size)/2) : Math.max(0, 1280 - size - 40)
                      const y = posSel === 'top-left' || posSel === 'top-right' ? 40 : posSel === 'center' ? Math.max(0, (720 - size)/2) : Math.max(0, 720 - size - 40)
                      const group = `<svg x=\"${x}\" y=\"${y}\" width=\"${size}\" height=\"${size}\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"rgba(255,255,255,0.6)\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\">${inner}</svg>`
                      const prev = slide.designCode?.svg
                      const next = prev && prev.startsWith('<svg') ? `${prev.slice(0, -6)}${group}</svg>` : `<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 1280 720\">${group}</svg>`
                      updateSlide(slide.id, { designCode: { ...(slide.designCode||{}), svg: next }, useGeneratedImage: false, imageUrl: undefined, imageState: 'done' })
                      setShowIconPicker(false)
                    }
                  }}>{it.name}</Button>
                ))}
              </div>
              <div className="flex items-center gap-2 mt-2 text-xs">
                <span>Position</span>
                <select className="border rounded p-1" defaultValue={(typeof window !== 'undefined' && (localStorage.getItem('app.iconPos') as any)) || 'top-right'} onChange={(e)=>{ try { localStorage.setItem('app.iconPos', e.target.value) } catch {} }}>
                  <option value="top-left">Top-Left</option>
                  <option value="top-right">Top-Right</option>
                  <option value="bottom-left">Bottom-Left</option>
                  <option value="bottom-right">Bottom-Right</option>
                  <option value="center">Center</option>
                </select>
                <span>Size</span>
                <select className="border rounded p-1" defaultValue={(typeof window !== 'undefined' && (localStorage.getItem('app.iconSize') as any)) || 'medium'} onChange={(e)=>{ try { localStorage.setItem('app.iconSize', e.target.value) } catch {} }}>
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                </select>
                <span className="text-muted-foreground">(applies on insert)</span>
              </div>
            </div>
          ) : null}
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={()=>setShowPatternPicker(v=>!v)}>
              Insert Pattern
            </Button>
            {showPatternPicker ? (
              <>
                <select className="border rounded p-1 text-sm" value={patternName} onChange={(e)=>setPatternName(e.target.value)}>
                  <option value="topography">Topography</option>
                  <option value="hexagons">Hexagons</option>
                  <option value="diagonal">Diagonal</option>
                  <option value="overlap">Overlapping Circles</option>
                </select>
                <Button size="sm" onClick={async ()=>{
                  const base = resolveAdkBaseUrl();
                  const res = await fetch(`${base}/v1/assets/patterns/get`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: patternName }) })
                  if (res.ok) {
                    const { svg } = await res.json();
                    updateSlide(slide.id, { designCode: { ...(slide.designCode||{}), svg }, useGeneratedImage: false, imageUrl: undefined, imageState: 'done' })
                    setShowPatternPicker(false)
                  }
                }}>Insert</Button>
              </>
            ) : null}
            {graphics && graphics.length ? (
              <>
                <select className="border rounded p-1 text-sm" value={selectedGraphic} onChange={(e)=> setSelectedGraphic(e.target.value)}>
                  <option value="">Select Graphic</option>
                  {graphics.map((g, i)=> (
                    <option key={i} value={g.url}>{g.name}</option>
                  ))}
                </select>
                <Button size="sm" onClick={() => {
                  const url = selectedGraphic || (graphics[0]?.url || '')
                  if (!url) return
                  updateSlide(slide.id, { imageUrl: url, assetImageUrl: url, useGeneratedImage: false, imageState: 'done', designCode: undefined })
                }}>Insert Graphic</Button>
              </>
            ) : null}
          </div>
          <Textarea
            id="speaker-notes"
            value={slide.speakerNotes}
            onChange={(e) => updateSlide(slide.id, { speakerNotes: e.target.value })}
            className="flex-grow"
          />
          {slide.criticReview ? (
            <div className="border rounded-md p-3 bg-muted/30">
              <div className="flex items-center justify-between mb-2">
                <Label>Critic Review</Label>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={applySuggestions}>Apply Suggestions</Button>
                  <Button size="sm" variant="ghost" onClick={()=>updateSlide(slide.id, { criticReview: undefined })}>Dismiss</Button>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="font-medium">Issues</div>
                  <ul className="list-disc pl-5">
                    {(slide.criticReview.issues || []).map((t, i)=>(<li key={i}>{t}</li>))}
                  </ul>
                </div>
                <div>
                  <div className="font-medium">Suggestions</div>
                  <ul className="list-disc pl-5">
                    {(slide.criticReview.suggestions || []).map((t, i)=>(<li key={i}>{t}</li>))}
                  </ul>
                </div>
              </div>
            </div>
          ) : null}
          {reviews && reviews.length ? (
            <div className="border rounded-md p-3 bg-muted/20">
              <div className="font-medium mb-2">Review History</div>
              <div className="space-y-2 max-h-48 overflow-auto pr-2">
                {reviews.map((r, i) => (
                  <div key={i} className="p-2 rounded border bg-background">
                    <div className="text-xs text-muted-foreground mb-1">{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</div>
                    <div className="text-sm"><b>Issues:</b> {(r.review_data?.issues || []).join('; ') || '—'}</div>
                    <div className="text-sm"><b>Suggestions:</b> {(r.review_data?.suggestions || []).join('; ') || '—'}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
