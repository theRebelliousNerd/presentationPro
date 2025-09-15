'use client';
import { useState, Dispatch, SetStateAction } from 'react';
import { Slide, Presentation } from '@/lib/types';
import SlideSidebar from './SlideSidebar';
import SlideEditor from './SlideEditor';
import { nanoid } from 'nanoid';
import { downloadScript } from '@/lib/download';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import ClarificationChat from '@/components/app/ClarificationChat';
import { downloadPresentationHtml, downloadImages, downloadEverything, downloadPptx } from '@/lib/download';
import { Textarea } from '@/components/ui/textarea';
import { generateFullScript } from '@/lib/actions';

type EditorProps = {
  slides: Slide[];
  setSlides: Dispatch<SetStateAction<Slide[]>> | ((slides: Slide[]) => void);
  presentation?: Presentation;
  setPresentation?: Dispatch<SetStateAction<Presentation>>;
  uploadFile?: (file: File) => Promise<{ name: string; url: string; path?: string }>;
};

export default function Editor({ slides, setSlides, presentation, setPresentation, uploadFile }: EditorProps) {
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
        <Tabs defaultValue="editor" className="flex flex-col h-full">
          <TabsList className="w-fit">
            <TabsTrigger value="editor">Editor</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="script">Script</TabsTrigger>
          </TabsList>
          <TabsContent value="editor" className="flex-grow flex flex-col">
            {activeSlide ? (
              <SlideEditor
                key={activeSlide.id}
                slide={activeSlide}
                updateSlide={updateSlide}
                assets={(presentation?.initialInput?.files || []).map(f => ({
                  name: f.name,
                  url: f.url,
                  kind: f.kind || (/(png|jpg|jpeg|gif|webp|svg)$/i.test(f.name) ? 'image' : /(pdf|docx|md|txt|csv|xls|xlsx)$/i.test(f.name) ? 'document' : 'other'),
                }))}
                constraints={presentation ? (
                  (activeSlide.useConstraints === false && activeSlide.constraintsOverride)
                  ? activeSlide.constraintsOverride
                  : {
                      citationsRequired: presentation.initialInput?.citationsRequired,
                      slideDensity: presentation.initialInput?.slideDensity,
                      mustInclude: presentation.initialInput?.mustInclude,
                      mustAvoid: presentation.initialInput?.mustAvoid,
                    }
                ) : undefined}
              />
            ) : (
              <div className="flex-grow flex items-center justify-center bg-card rounded-lg shadow-inner">
                <p className="text-muted-foreground">Select a slide to edit or add a new one.</p>
              </div>
            )}
          </TabsContent>
          <TabsContent value="chat" className="flex-grow">
            {presentation && setPresentation && uploadFile ? (
              <ClarificationChat
                presentation={presentation}
                setPresentation={setPresentation}
                onClarificationComplete={() => { /* remain in editing */ }}
                uploadFile={uploadFile}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">Chat unavailable</div>
            )}
          </TabsContent>
          <TabsContent value="script" className="flex-grow flex flex-col gap-3">
            <div className="flex gap-2">
              <Button
                onClick={async () => {
                  if (!setPresentation || !presentation) return;
                  const assets = (presentation.initialInput?.files || []);
                  const script = await generateFullScript(slides.map(s => ({ title: s.title, content: s.content, speakerNotes: s.speakerNotes })), assets as any);
                  setPresentation(prev => ({ ...(prev as any), fullScript: script }));
                }}
              >Generate Script</Button>
              <Button variant="outline" onClick={() => downloadScript(slides)}>
                <Download className="mr-2 h-4 w-4" />
                Download as .txt
              </Button>
            </div>
            <Textarea className="flex-grow" value={presentation?.fullScript || ''} onChange={(e) => setPresentation && setPresentation(prev => ({ ...(prev as any), fullScript: e.target.value }))} placeholder="Generate to view a full script with references..." />
          </TabsContent>
        </Tabs>
        <div className="flex-shrink-0 pt-4 flex gap-2 flex-wrap">
          <Button onClick={() => downloadScript(slides)}>
            <Download className="mr-2 h-4 w-4" />
            Download Script
          </Button>
          <Button variant="outline" onClick={() => downloadPptx(slides)}>
            <Download className="mr-2 h-4 w-4" />
            Export PowerPoint (.pptx)
          </Button>
          <Button variant="outline" onClick={() => downloadPresentationHtml(slides)}>
            <Download className="mr-2 h-4 w-4" />
            Download Presentation (HTML)
          </Button>
          <Button variant="outline" onClick={() => downloadImages(slides)}>
            <Download className="mr-2 h-4 w-4" />
            Download Images
          </Button>
          <Button variant="outline" onClick={() => downloadEverything(slides)}>
            <Download className="mr-2 h-4 w-4" />
            Download Everything (ZIP)
          </Button>
        </div>
      </main>
    </div>
  );
}
