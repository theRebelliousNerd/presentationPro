'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { ImageIcon, Loader2, RefreshCw, Edit, Palette } from 'lucide-react';
import { Slide } from '@/lib/types';
import { craftImagePrompt, generateImage } from '@/lib/actions';
import ImageEditorModal from './ImageEditorModal';
import { addUsage } from '@/lib/token-meter';
import * as htmlToImage from 'html-to-image';
import { orchVisionAnalyze } from '@/lib/orchestrator';
import { backgroundContainerClasses, getBgPattern, getTheme, renderPatternSvg, getTypeScale } from '@/lib/backgrounds';

type ImageDisplayProps = {
  slide: Slide;
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void;
};

export default function ImageDisplay({ slide, updateSlide }: ImageDisplayProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDesigning, setIsDesigning] = useState(false);
  const [overlay, setOverlay] = useState(0);
  const containerRef = useState<React.RefObject<HTMLDivElement>>()[0] || ((): React.RefObject<HTMLDivElement> => {
    // create a stable ref without re-renders
    const r = { current: null as any } as React.RefObject<HTMLDivElement>;
    return r;
  })();
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

  const triggerImageGeneration = async (prompt: string, baseImage?: string) => {
    updateSlide(slide.id, { imageState: 'loading' });
    try {
      const imageModel = (typeof window !== 'undefined' && localStorage.getItem('app.model.image')) || undefined;
      const { imageUrl } = await generateImage(prompt, { baseImage, imageModel: imageModel || undefined });
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

  const handleDesignRegenerate = async () => {
    if (isDesigning) return;
    setIsDesigning(true);
    try {
      // Capture a quick screenshot of the slide area (without hover UI)
      const node = containerRef.current as any;
      let dataUrl: string | undefined = undefined;
      if (node) {
        dataUrl = await htmlToImage.toPng(node, { pixelRatio: 1 });
        try {
          const vis = await orchVisionAnalyze({ screenshotDataUrl: dataUrl });
          setOverlay(vis.recommendDarken ? vis.overlay : 0);
        } catch {}
      }
      const theme = (typeof window !== 'undefined' && (localStorage.getItem('app.theme') as any)) || 'brand';
      const pattern = (typeof window !== 'undefined' && (localStorage.getItem('app.bgPattern') as any)) || 'gradient';
      const textModel = (typeof window !== 'undefined' && (localStorage.getItem('app.model.text') as any)) || undefined;
      const design = await craftImagePrompt({ title: slide.title, content: slide.content, speakerNotes: slide.speakerNotes }, { theme: theme as any, pattern: pattern as any, screenshotDataUrl: dataUrl, textModel, preferCode: true });
      if (typeof design === 'string') {
        updateSlide(slide.id, { imagePrompt: design });
        await triggerImageGeneration(design, dataUrl);
      } else if (design && design.type === 'code') {
        updateSlide(slide.id, { designCode: design.code, useGeneratedImage: false, imageUrl: undefined, imageState: 'done' });
      }
    } catch (e) {
      console.error('Design regenerate failed', e);
    } finally {
      setIsDesigning(false);
    }
  };

  return (
    <div ref={containerRef as any} className="aspect-video w-full bg-muted rounded-lg flex items-center justify-center relative overflow-hidden group">
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

      {/* If using an uploaded asset image, render it */}
      {!slide.useGeneratedImage && slide.imageUrl && (
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
      {(((slide.useGeneratedImage && !slide.imageUrl) || (!slide.useGeneratedImage && !slide.imageUrl))) && (
        <div className="absolute inset-0">{renderBackgroundNew(slide)}</div>
      )}
      {overlay > 0 && (
        <div className="absolute inset-0" style={{ backgroundColor: `rgba(0,0,0,${overlay})` }} />
      )}

      {/* Text overlay preview */}
      <div className="absolute inset-0 p-6 md:p-8 flex flex-col justify-center">
        <h3 className={`font-headline font-semibold drop-shadow-sm mb-3 md:mb-4 ${getTypeScale()==='large' ? 'text-4xl md:text-5xl' : 'text-3xl md:text-4xl'}`}>{slide.title}</h3>
        <ul className={`list-disc pl-5 space-y-1.5 max-w-[80%] leading-snug ${getTypeScale()==='large' ? 'text-lg md:text-xl' : 'text-base md:text-lg'}`}>
          {(slide.content || []).map((line, idx) => (
            <li key={idx} className="drop-shadow-sm">{line}</li>
          ))}
        </ul>
      </div>

      <div className="absolute inset-0 bg-black/30 flex items-center justify-center gap-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <Button variant="secondary" onClick={handleRegenerate} disabled={slide.imageState === 'loading' || isDesigning}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Regenerate
        </Button>
        <Button variant="secondary" onClick={handleDesignRegenerate} disabled={slide.imageState === 'loading' || isDesigning}>
          {isDesigning ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Palette className="mr-2 h-4 w-4" />}
          Design Boost
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

function renderBackgroundNew(slide: Slide) {
  const theme = getTheme();
  const pattern = getBgPattern();
  const code = slide.designCode;
  if (code?.svg || code?.css) {
    return (
      <div className="w-full h-full" style={{ backgroundImage: code.css }}>
        {code.svg && <div className="w-full h-full" dangerouslySetInnerHTML={{ __html: code.svg }} />}
      </div>
    );
  }
  return (
    <div className={backgroundContainerClasses(theme, pattern)}>
      {renderPatternSvg(pattern)}
    </div>
  );
}
