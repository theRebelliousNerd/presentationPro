'use client';

import { useRef, useState } from 'react';
import { usePresentationStateArango as usePresentationState } from '@/hooks/use-presentation-state-arango';
import { Slide } from '@/lib/types';
import Header from '@/components/app/Header';
import InitialInput from '@/components/app/InitialInput';
import ClarificationChat from '@/components/app/ClarificationChat';
import OutlineApproval from '@/components/app/OutlineApproval';
import GeneratingSpinner from '@/components/app/GeneratingSpinner';
import Editor from '@/components/app/editor/Editor';
import ErrorState from '@/components/app/ErrorState';
import { generateSlideContent, critiqueSlide, retrieveContext } from '@/lib/actions';
import { nanoid } from 'nanoid';

export default function AppRoot({ presentationIdOverride }: { presentationIdOverride?: string }) {
  const {
    isLoaded,
    appState,
    setAppState,
    presentation,
    setPresentation,
    resetState,
    uploadFile,
    duplicatePresentation,
    saveNow,
  } = usePresentationState(presentationIdOverride);

  const [genProgress, setGenProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });
  const cancelGenerationRef = useRef(false);

  const handleStartClarifying = (values: {
    text: string;
    files: { name: string; url: string; path?: string }[];
    styleFiles: { name: string; url: string; path?: string }[];
    length: string;
    audience: string;
    industry: string;
    subIndustry: string;
    tone: { formality: number; energy: number };
    graphicStyle: string;
  }) => {
    setPresentation((prev) => ({
      ...prev,
      initialInput: { ...prev.initialInput, ...values },
    }));
    setAppState('clarifying');
  };

  const handleOutlineApproved = async (outline: string[]) => {
    const total = outline.length;
    if (total === 0) {
      setAppState('editing');
      return;
    }
    setPresentation(prev => ({ ...prev, outline, slides: [] }));
    setAppState('generating');
    cancelGenerationRef.current = false;
    setGenProgress({ current: 0, total });

    const basePresentation = presentation;
    const allFiles = [...(basePresentation.initialInput.files || []), ...(basePresentation.initialInput.styleFiles || [])];
    const baseAssets = allFiles.map(f => ({
      name: f.name,
      url: f.url,
      kind: f.kind || (/(png|jpg|jpeg|gif|webp|svg)$/i.test(f.name) ? 'image' : /(pdf|docx|md|txt|csv|xls|xlsx)$/i.test(f.name) ? 'document' : 'other'),
    }));

    const slidesBuffer: (Slide | undefined)[] = new Array(total);
    let completed = 0;

    const updateSlidesState = () => {
      setPresentation(prev => ({
        ...prev,
        slides: slidesBuffer.filter((s): s is Slide => Boolean(s)),
      }));
    };

    const generateSlideAt = async (index: number) => {
      if (cancelGenerationRef.current) return;
      const title = outline[index];
      let contextAssets = baseAssets;
      try {
        const chunks = await retrieveContext(basePresentation.id, title, 5);
        if (chunks.length) {
          contextAssets = [
            ...baseAssets,
            ...chunks.map((c) => ({ name: c.name, url: '', kind: 'document' as const, text: c.text } as any)),
          ];
        }
      } catch {}

      if (cancelGenerationRef.current) return;

      const result = await generateSlideContent({ outline: [title], assets: contextAssets, presentationId: basePresentation.id });
      const rawSlide = (result.slides && result.slides[0]) || { title, content: [], speakerNotes: '', imagePrompt: '' } as any;
      if (cancelGenerationRef.current) return;

      const improved = await critiqueSlide({
        title: (rawSlide as any).title,
        content: (rawSlide as any).content,
        speakerNotes: (rawSlide as any).speakerNotes,
        imagePrompt: (rawSlide as any).imagePrompt,
      }, {
        audience: basePresentation.initialInput.audience,
        tone: `formality:${basePresentation.initialInput.tone.formality}/energy:${basePresentation.initialInput.tone.energy}`,
        length: basePresentation.initialInput.length as any,
        assets: allFiles as any,
        presentationId: basePresentation.id,
        slideIndex: index,
      });

      if (cancelGenerationRef.current) return;

      const useAsset = (rawSlide as any).useAssetImageUrl || (rawSlide as any).assetImageUrl;
      slidesBuffer[index] = {
        title: improved.title,
        content: improved.content,
        speakerNotes: improved.speakerNotes,
        imagePrompt: (rawSlide as any).imagePrompt,
        id: nanoid(),
        imageState: 'done',
        assetImageUrl: useAsset || undefined,
        useGeneratedImage: false,
        imageUrl: useAsset || undefined,
      } as Slide;

      updateSlidesState();
      completed += 1;
      setGenProgress({ current: completed, total });
    };

    try {
      const concurrency = Math.min(3, total || 1);
      let nextIndex = 0;

      const runNext = async (): Promise<void> => {
        if (cancelGenerationRef.current) return;
        const currentIndex = nextIndex++;
        if (currentIndex >= total) return;
        await generateSlideAt(currentIndex);
        await runNext();
      };

      await Promise.all(new Array(Math.min(concurrency, total || 1)).fill(null).map(() => runNext()));

      setAppState('editing');
    } catch (error) {
      console.error('Failed to generate slides:', error);
      setAppState('error');
    }
  };

  const renderState = () => {
    if (!isLoaded) {
      return <GeneratingSpinner text="Loading Studio..." />;
    }

    switch (appState) {
      case 'initial':
        return <InitialInput presentation={presentation} onStart={handleStartClarifying} uploadFile={uploadFile} />;
      case 'clarifying':
        return <ClarificationChat
          presentation={presentation}
          setPresentation={setPresentation}
          onClarificationComplete={(goals) => {
            setPresentation(prev => ({...prev, clarifiedGoals: goals}));
            setAppState('approving');
          }}
          uploadFile={uploadFile}
          />;
      case 'approving':
        return <OutlineApproval
          clarifiedGoals={presentation.clarifiedGoals}
          onApprove={handleOutlineApproved}
          onGoBack={() => setAppState('clarifying')}
          />;
      case 'generating':
        return <GeneratingSpinner text="Generating your presentation..." current={genProgress.current} total={genProgress.total} onCancel={() => { cancelGenerationRef.current = true; }} />;
      case 'editing':
        return <Editor
          slides={presentation.slides}
          setSlides={(slides: Slide[]) => setPresentation(prev => ({...prev, slides}))}
          presentation={presentation}
          setPresentation={setPresentation}
          uploadFile={uploadFile}
          />;
      case 'error':
        return <ErrorState onReset={resetState} />
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Header onReset={resetState} onSaveCopy={async () => { await duplicatePresentation(); }} onSaveNow={async () => { await saveNow(); }} />
      <main className="flex-grow flex flex-col items-center justify-center p-8 sm:p-12 md:p-16">
        {renderState()}
      </main>
    </div>
  );
}
