'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { ImageIcon, Loader2, RefreshCw, Edit } from 'lucide-react';
import { Slide } from '@/lib/types';
import { generateImage } from '@/lib/actions';
import ImageEditorModal from './ImageEditorModal';

type ImageDisplayProps = {
  slide: Slide;
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void;
};

export default function ImageDisplay({ slide, updateSlide }: ImageDisplayProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const triggerImageGeneration = async (prompt: string) => {
    updateSlide(slide.id, { imageState: 'loading' });
    try {
      const { imageUrl } = await generateImage(prompt);
      updateSlide(slide.id, { imageUrl, imageState: 'done' });
    } catch (error) {
      console.error("Image generation failed:", error);
      updateSlide(slide.id, { imageState: 'error' });
    }
  };

  useEffect(() => {
    if (slide.imageState === 'loading' && !slide.imageUrl) {
      triggerImageGeneration(slide.imagePrompt);
    }
  }, [slide.id, slide.imageState, slide.imagePrompt, slide.imageUrl]);

  const handleRegenerate = () => {
    triggerImageGeneration(slide.imagePrompt);
  };

  return (
    <div className="aspect-video w-full bg-muted rounded-lg flex items-center justify-center relative overflow-hidden group">
      {slide.imageState === 'loading' && (
        <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
      )}
      {slide.imageState === 'error' && (
        <div className="text-center text-destructive">
          <ImageIcon className="mx-auto h-10 w-10 mb-2" />
          <p>Image generation failed.</p>
        </div>
      )}
      {slide.imageState === 'done' && slide.imageUrl && (
        <Image
          src={slide.imageUrl}
          alt={slide.imagePrompt}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 50vw"
        />
      )}

      <div className="absolute inset-0 bg-black/50 flex items-center justify-center gap-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <Button variant="secondary" onClick={handleRegenerate} disabled={slide.imageState === 'loading'}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Regenerate
        </Button>
        <Button variant="secondary" onClick={() => setIsModalOpen(true)}>
          <Edit className="mr-2 h-4 w-4" />
          Edit
        </Button>
      </div>

      <ImageEditorModal 
        isOpen={isModalOpen}
        setIsOpen={setIsModalOpen}
        slide={slide}
        updateSlide={updateSlide}
      />
    </div>
  );
}
