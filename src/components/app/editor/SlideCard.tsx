'use client';
import Image from 'next/image';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { Slide } from '@/lib/types';
import { ImageIcon, Loader2 } from 'lucide-react';

type SlideCardProps = {
  slide: Slide;
  isActive: boolean;
  onClick: () => void;
};

export default function SlideCard({ slide, isActive, onClick }: SlideCardProps) {
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
  return (
    <Card
      className={cn(
        "cursor-pointer transition-all duration-200 hover:shadow-md hover:border-primary/50",
        isActive ? "border-primary shadow-lg" : "border-border"
      )}
      onClick={onClick}
    >
      <CardContent className="p-2 flex gap-3 items-center">
        <div className="w-24 h-16 rounded-sm bg-muted flex-shrink-0 relative overflow-hidden">
          {slide.imageState === 'loading' && (
            <div className="w-full h-full flex items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}
          {slide.imageState === 'error' && (
            <div className="w-full h-full flex items-center justify-center bg-destructive/10">
              <ImageIcon className="h-5 w-5 text-destructive" />
            </div>
          )}
          {slide.imageUrl && slide.imageState === 'done' && (
            canUseNextImage ? (
              <Image
                src={slide.imageUrl}
                alt={slide.title}
                fill
                className="object-cover"
              />
            ) : (
              <img src={slide.imageUrl} alt={slide.title} className="w-full h-full object-cover" />
            )
          )}
        </div>
        <div className="flex-grow overflow-hidden">
          <p className="text-sm font-semibold truncate">{slide.title}</p>
        </div>
      </CardContent>
    </Card>
  );
}
