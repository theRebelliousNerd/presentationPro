'use client';
import { Dispatch, SetStateAction, DragEvent, useEffect, useMemo, useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Plus, Trash2 } from 'lucide-react';
import { Slide, Presentation } from '@/lib/types';
import SlideCard from './SlideCard';
import ResearchHelper from './ResearchHelper';
import { fetchPresentationGraph } from '@/lib/arango-client';
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
} from "@/components/ui/alert-dialog"

type SlideSidebarProps = {
  slides: Slide[];
  activeSlideId: string | null;
  setActiveSlideId: Dispatch<SetStateAction<string | null>>;
  addSlide: () => void;
  deleteSlide: (slideId: string) => void;
  setSlides: (slides: Slide[]) => void;
  presentation?: Presentation;
  setPresentation?: (updater: (prev: Presentation) => Presentation) => void;
  style?: React.CSSProperties;
};


export default function SlideSidebar({
  slides,
  activeSlideId,
  setActiveSlideId,
  addSlide,
  deleteSlide,
  setSlides,
  presentation,
  setPresentation,
  style
}: SlideSidebarProps) {
  const [graph, setGraph] = useState<{ slides: any[]; assets: any[]; edges: any[] } | null>(null);
  const [graphError, setGraphError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    if (!presentation?.id) {
      setGraph(null);
      return;
    }
    fetchPresentationGraph(presentation.id)
      .then((data) => {
        if (!isMounted) return;
        setGraph(data);
        setGraphError(null);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.warn('Failed to load presentation graph', err);
        setGraphError('Unable to load linked assets');
      });
    return () => { isMounted = false; };
  }, [presentation?.id]);

  const activeSlideIndex = slides.findIndex(s => s.id === activeSlideId);
  const linkedAssets = useMemo(() => {
    if (!graph || activeSlideIndex < 0 || !presentation?.id) return [] as any[];
    const edges = graph.edges || [];
    const assets = graph.assets || [];
    const assetMap = new Map<string, any>();
    assets.forEach((asset: any) => {
      const identifier = asset?.id || asset?._id || (asset?._key ? `assets/${asset._key}` : undefined);
      if (identifier) {
        assetMap.set(identifier, asset);
        assetMap.set(identifier.split('/').pop() || identifier, asset);
      }
    });
    const prefix = `slides/${presentation.id}_${activeSlideIndex}`;
    const results: any[] = [];
    edges.forEach((edge: any) => {
      const fromId = edge?._from || edge?.from;
      if (typeof fromId === 'string' && fromId.startsWith(prefix)) {
        const toId = edge?._to || edge?.to;
        if (typeof toId === 'string') {
          const asset = assetMap.get(toId) || assetMap.get(toId.split('/').pop() || '');
          if (asset && !results.includes(asset)) {
            results.push(asset);
          }
        }
      }
    });
    return results;
  }, [graph, activeSlideIndex, presentation?.id]);



  const handleDragStart = (e: DragEvent<HTMLDivElement>, index: number) => {
    e.dataTransfer.setData("slideIndex", index.toString());
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>, dropIndex: number) => {
    const dragIndex = parseInt(e.dataTransfer.getData("slideIndex"), 10);
    const draggedSlide = slides[dragIndex];

    const newSlides = [...slides];
    newSlides.splice(dragIndex, 1);
    newSlides.splice(dropIndex, 0, draggedSlide);
    setSlides(newSlides);
  };
  
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <aside className="h-full flex-shrink-0 bg-card border-r flex flex-col p-2" style={style}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-headline text-sm font-semibold">Slides</h2>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={addSlide}>
          <Plus className="h-5 w-5" />
        </Button>
      </div>
      <ScrollArea className="flex-grow -mr-2 pr-2">
        <div className="space-y-2">
          {slides.map((slide, index) => (
            <div
              key={slide.id}
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDrop={(e) => handleDrop(e, index)}
              onDragOver={handleDragOver}
              className="group relative"
            >
              <SlideCard
                slide={slide}
                isActive={slide.id === activeSlideId}
                onClick={() => setActiveSlideId(slide.id)}
              />
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="destructive"
                    size="icon"
                    className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                    disabled={slides.length <= 1}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. This will permanently delete this slide.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => deleteSlide(slide.id)}>Delete</AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          ))}
        </div>
      </ScrollArea>
      <ResearchHelper presentation={presentation} onInsert={(rules) => {
        if (!activeSlideId) return;
        const text = rules.map(r => `• ${r}`).join('\n');
        const updated = slides.map(s => s.id === activeSlideId ? { ...s, speakerNotes: (s.speakerNotes ? (s.speakerNotes + '\n\n') : '') + text } : s);
        setSlides(updated);
      }} setPresentation={setPresentation} presentationId={presentation?.id} />
      <div className="mt-4 border-t pt-3">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Linked assets</h3>
          {graphError ? <span className="text-[10px] text-destructive">{graphError}</span> : null}
        </div>
        {linkedAssets.length ? (
          <ul className="space-y-2 text-xs">
            {linkedAssets.map((asset: any, idx) => {
              const key = asset?.id || asset?._id || asset?._key || idx;
              const kind = (asset?.kind || asset?.category || 'document').toString();
              const name = asset?.name || asset?.url || 'Asset';
              return (
                <li key={key} className="p-2 rounded border bg-background/90">
                  <div className="font-medium truncate" title={name}>{name}</div>
                  <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{kind}</div>
                  {asset?.url ? (
                    <a
                      href={asset.url}
                      className="text-[11px] text-primary underline"
                      target="_blank"
                      rel="noreferrer"
                    >
                      View
                    </a>
                  ) : null}
                </li>
              );
            })}
          </ul>
        ) : (
          <div className="text-[11px] text-muted-foreground">No assets linked to this slide yet.</div>
        )}
      </div>
    </aside>
  );
}
