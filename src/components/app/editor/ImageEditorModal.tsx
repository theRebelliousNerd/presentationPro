'use client';
import { useState, ChangeEvent, Dispatch, SetStateAction } from 'react';
import Image from 'next/image';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Slide } from '@/lib/types';
import { editImage } from '@/lib/actions';
import { Loader2, Upload } from 'lucide-react';

type ImageEditorModalProps = {
  isOpen: boolean;
  setIsOpen: Dispatch<SetStateAction<boolean>>;
  slide: Slide;
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void;
};

export default function ImageEditorModal({ isOpen, setIsOpen, slide, updateSlide }: ImageEditorModalProps) {
  const [baseImage, setBaseImage] = useState<string | null>(slide.imageUrl || null);
  const [editPrompt, setEditPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setBaseImage(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleEdit = async () => {
    if (!baseImage || !editPrompt) return;

    setIsLoading(true);
    updateSlide(slide.id, { imageState: 'loading' });
    setIsOpen(false);

    try {
      const { imageUrl } = await editImage(editPrompt, baseImage);
      updateSlide(slide.id, { imageUrl, imageState: 'done' });
    } catch (error) {
      console.error("Image editing failed:", error);
      updateSlide(slide.id, { imageState: 'error' });
    } finally {
      setIsLoading(false);
      setEditPrompt('');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Edit Image with AI</DialogTitle>
          <DialogDescription>
            Upload an image and describe the changes you'd like to make.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="aspect-video w-full bg-muted rounded-lg flex items-center justify-center relative overflow-hidden">
            {baseImage ? (
              <Image src={baseImage} alt="Image preview" fill className="object-contain" />
            ) : (
              <div className="text-center text-muted-foreground p-4">
                <Upload className="mx-auto h-8 w-8 mb-2" />
                <p>Upload an image to start editing</p>
              </div>
            )}
          </div>
          <Button asChild variant="outline">
            <label htmlFor="image-upload">
              <Upload className="mr-2 h-4 w-4" />
              Upload New Image
              <input id="image-upload" type="file" accept="image/*" className="sr-only" onChange={handleImageUpload} />
            </label>
          </Button>
          <Textarea
            placeholder="e.g., 'make the background a futuristic cityscape at night'"
            value={editPrompt}
            onChange={(e) => setEditPrompt(e.target.value)}
            disabled={!baseImage}
          />
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => setIsOpen(false)}>Cancel</Button>
          <Button onClick={handleEdit} disabled={!baseImage || !editPrompt || isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Generate
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
