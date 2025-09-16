'use client';
import { Dispatch, SetStateAction, DragEvent } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Plus, Trash2 } from 'lucide-react';
import { Slide } from '@/lib/types';
import SlideCard from './SlideCard';
import ResearchHelper from './ResearchHelper';
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
  style?: React.CSSProperties;
};

export default function SlideSidebar({
  slides,
  activeSlideId,
  setActiveSlideId,
  addSlide,
  deleteSlide,
  setSlides,
  style
}: SlideSidebarProps) {

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
      <ResearchHelper onInsert={(rules) => {
        if (!activeSlideId) return;
        const text = rules.map(r => `• ${r}`).join('\n');
        const updated = slides.map(s => s.id === activeSlideId ? { ...s, speakerNotes: (s.speakerNotes ? (s.speakerNotes + '\n\n') : '') + text } : s);
        setSlides(updated);
      }} />
    </aside>
  );
}
