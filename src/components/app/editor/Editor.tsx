'use client';
import { useState, Dispatch, SetStateAction } from 'react';
import { Slide } from '@/lib/types';
import SlideSidebar from './SlideSidebar';
import SlideEditor from './SlideEditor';
import { nanoid } from 'nanoid';
import { downloadScript } from '@/lib/download';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

type EditorProps = {
  slides: Slide[];
  setSlides: Dispatch<SetStateAction<Slide[]>> | ((slides: Slide[]) => void);
};

export default function Editor({ slides, setSlides }: EditorProps) {
  const [activeSlideId, setActiveSlideId] = useState<string | null>(slides[0]?.id || null);

  const activeSlide = slides.find(s => s.id === activeSlideId);
  const activeSlideIndex = slides.findIndex(s => s.id === activeSlideId);

  const updateSlide = (slideId: string, updatedProps: Partial<Slide>) => {
    const newSlides = slides.map(s => s.id === slideId ? { ...s, ...updatedProps } : s);
    setSlides(newSlides);
  };
  
  const addSlide = () => {
    const newSlide: Slide = {
      id: nanoid(),
      title: 'New Slide',
      content: ['- '],
      speakerNotes: '',
      imagePrompt: 'A simple, abstract background with soft gradients and geometric shapes, in a professional and minimalist style.',
      imageState: 'loading',
    };
    const newIndex = activeSlideIndex + 1;
    const newSlides = [...slides.slice(0, newIndex), newSlide, ...slides.slice(newIndex)];
    setSlides(newSlides);
    setActiveSlideId(newSlide.id);
  };

  const deleteSlide = (slideId: string) => {
    if (slides.length <= 1) return;
    const slideIndex = slides.findIndex(s => s.id === slideId);
    const newSlides = slides.filter(s => s.id !== slideId);
    setSlides(newSlides);

    if (activeSlideId === slideId) {
      const newActiveIndex = Math.max(0, slideIndex - 1);
      setActiveSlideId(newSlides[newActiveIndex]?.id || null);
    }
  };

  return (
    <div className="w-full h-[calc(100vh-120px)] flex gap-6">
      <SlideSidebar
        slides={slides}
        activeSlideId={activeSlideId}
        setActiveSlideId={setActiveSlideId}
        addSlide={addSlide}
        deleteSlide={deleteSlide}
        setSlides={setSlides}
      />
      <main className="flex-grow h-full flex flex-col">
        {activeSlide ? (
          <SlideEditor
            key={activeSlide.id}
            slide={activeSlide}
            updateSlide={updateSlide}
          />
        ) : (
          <div className="flex-grow flex items-center justify-center bg-card rounded-lg shadow-inner">
            <p className="text-muted-foreground">Select a slide to edit or add a new one.</p>
          </div>
        )}
        <div className="flex-shrink-0 pt-4">
          <Button onClick={() => downloadScript(slides)}>
            <Download className="mr-2 h-4 w-4" />
            Download Script
          </Button>
        </div>
      </main>
    </div>
  );
}
