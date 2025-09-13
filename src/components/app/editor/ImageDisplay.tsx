'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { ImageIcon, Loader2, RefreshCw, Edit } from 'lucide-react';
import { Slide } from '@/lib/types';
import { generateImage } from '@/lib/actions';
import ImageEditorModal from './ImageEditorModal';
import { addUsage } from '@/lib/token-meter';

type ImageDisplayProps = {
  slide: Slide;
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void;
};

export default function ImageDisplay({ slide, updateSlide }: ImageDisplayProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const canUseNextImage = (() => {
    const url = slide.imageUrl || '';
    if (!url) return false;
    if (url.startsWith('data:') || url.startsWith('blob:')) return false;
    try {
      const h = new URL(url).hostname;
      return ['placehold.co','images.unsplash.com','picsum.photos'].includes(h);
    } catch {
      return false;
    }
  })();

  const triggerImageGeneration = async (prompt: string) => {
    updateSlide(slide.id, { imageState: 'loading' });
    try {
      const { imageUrl } = await generateImage(prompt);
      updateSlide(slide.id, { imageUrl, imageState: 'done' });
      addUsage({ model: 'gemini-2.5-flash-image-preview', kind: 'image_call', count: 1, at: Date.now() } as any);
    } catch (error) {
      console.error("Image generation failed:", error);
      updateSlide(slide.id, { imageState: 'error' });
    }
  };

  useEffect(() => {
    if (slide.useGeneratedImage && slide.imageState === 'loading' && !slide.imageUrl) {
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
      {slide.useGeneratedImage && slide.imageState === 'done' && slide.imageUrl && (
        canUseNextImage ? (
          <Image
            src={slide.imageUrl}
            alt={slide.imagePrompt}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 50vw"
          />
        ) : (
          <img src={slide.imageUrl} alt={slide.imagePrompt} className="w-full h-full object-cover" />
        )
      )}

      {/* Default background when not using generated image or while waiting */}
      {(!slide.useGeneratedImage || !slide.imageUrl) && (
        <div className="absolute inset-0">{renderBackground(slide)}</div>
      )}

      {/* Text overlay preview */}
      <div className="absolute inset-0 p-6 flex flex-col justify-center">
        <h3 className="text-2xl font-headline font-semibold drop-shadow-sm mb-3">{slide.title}</h3>
        <ul className="list-disc pl-5 space-y-1 text-sm max-w-[80%]">
          {(slide.content || []).map((line, idx) => (
            <li key={idx} className="drop-shadow-sm">{line}</li>
          ))}
        </ul>
      </div>

      <div className="absolute inset-0 bg-black/30 flex items-center justify-center gap-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <Button variant="secondary" onClick={handleRegenerate} disabled={slide.imageState === 'loading'}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Regenerate
        </Button>
        <Button variant="secondary" onClick={() => setIsModalOpen(true)} disabled={!slide.useGeneratedImage}>
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

function getTheme() {
  if (typeof window === 'undefined') return 'brand';
  try { return localStorage.getItem('app.theme') || 'brand'; } catch { return 'brand'; }
}

function renderBackground(slide: Slide) {
  // simple gradient + svg shapes
  const idx = Math.abs(hashCode(slide.id)) % 3;
  const theme = getTheme();
  const brandA = theme === 'dark' ? 'from-secondary/40 via-muted/20 to-primary/30' : theme === 'muted' ? 'from-muted/30 via-muted/10 to-secondary/20' : 'from-primary/30 via-accent/20 to-secondary/30';
  const brandB = theme === 'dark' ? 'from-secondary/40 via-secondary/20 to-primary/30' : theme === 'muted' ? 'from-muted/20 via-muted/10 to-accent/20' : 'from-secondary/30 via-muted/10 to-primary/20';
  if (idx === 0) {
    return (
      <div className={`w-full h-full bg-gradient-to-br ${brandA}`}>
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="g1" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="rgba(255,255,255,0.2)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0)" />
            </linearGradient>
          </defs>
          <circle cx="15%" cy="20%" r="120" fill="url(#g1)" />
          <rect x="70%" y="60%" width="260" height="260" fill="rgba(255,255,255,0.05)" rx="16" />
        </svg>
      </div>
    );
  }
  if (idx === 1) {
    return (
      <div className={`w-full h-full bg-gradient-to-tr ${brandB}`}>
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <g fill="rgba(255,255,255,0.06)">
            {Array.from({ length: 20 }).map((_, i) => (
              <circle key={i} cx={(i * 80) % 1200} cy={(i * 60) % 600} r={30} />
            ))}
          </g>
        </svg>
      </div>
    );
  }
  return (
    <div className={`w-full h-full bg-gradient-to-bl ${theme==='dark'?'from-muted/10 to-secondary/30':theme==='muted'?'from-muted/20 to-accent/10':'from-muted/20 to-accent/20'}`}> 
      <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
        <path d="M0,400 C300,300 500,500 1200,350 L1200,700 L0,700 Z" fill="rgba(255,255,255,0.08)" />
      </svg>
    </div>
  );
}

function hashCode(str: string) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  }
  return h;
}
