'use client';

import { useRef, useState } from 'react';
import { usePresentationState } from '@/hooks/use-presentation-state';
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
    setPresentation(prev => ({...prev, outline}));
    setAppState('generating');
    cancelGenerationRef.current = false;
    setGenProgress({ current: 0, total: outline.length });
    try {
      const generated: Slide[] = [];
      // Build assets list from uploaded files to inform AI generation
      const allFiles = [...(presentation.initialInput.files || []), ...(presentation.initialInput.styleFiles || [])];
      const assets = allFiles.map(f => ({
        name: f.name,
        url: f.url,
        kind: f.kind || (/(png|jpg|jpeg|gif|webp|svg)$/i.test(f.name) ? 'image' : /(pdf|docx|md|txt|csv|xls|xlsx)$/i.test(f.name) ? 'document' : 'other'),
      }));
      for (let i = 0; i < outline.length; i++) {
        if (cancelGenerationRef.current) break;
        const title = outline[i];
        // Pull top context chunks from orchestrator graph RAG (if enabled)
        let contextAssets = assets;
        try {
          const chunks = await retrieveContext(presentation.id, title, 5);
          if (chunks.length) {
            contextAssets = [
              ...assets,
              ...chunks.map((c) => ({ name: c.name, url: '', kind: 'document' as const, text: c.text } as any)),
            ];
          }
        } catch {}
        const [rawSlide] = await generateSlideContent({ outline: [title], assets: contextAssets });
        // Critique + revise pass
        const improved = await critiqueSlide({ title: (rawSlide as any).title, content: (rawSlide as any).content, speakerNotes: (rawSlide as any).speakerNotes, imagePrompt: (rawSlide as any).imagePrompt }, {
          audience: presentation.initialInput.audience,
          tone: `formality:${presentation.initialInput.tone.formality}/energy:${presentation.initialInput.tone.energy}`,
          length: presentation.initialInput.length as any,
          assets: allFiles as any,
        });
        const useAsset = (rawSlide as any).useAssetImageUrl || (rawSlide as any).assetImageUrl;
        const withId: Slide = {
          title: improved.title,
          content: improved.content,
          speakerNotes: improved.speakerNotes,
          imagePrompt: (rawSlide as any).imagePrompt,
          id: nanoid(),
          imageState: useAsset ? 'done' : 'loading',
          assetImageUrl: useAsset || undefined,
          useGeneratedImage: !useAsset,
          imageUrl: useAsset || undefined,
        } as Slide;
        generated.push(withId);
        setPresentation(prev => ({ ...prev, slides: [...generated] }));
        setGenProgress({ current: i + 1, total: outline.length });
      }
      setAppState('editing');
    } catch (error) {
      console.error("Failed to generate slides:", error);
      setAppState('error');
    }
  };

  const renderState = () => {
    if (!isLoaded) {
      return <GeneratingSpinner text="Loading Studio..." />;
    }

    switch (appState) {
      case 'initial':
        return <InitialInput onStart={handleStartClarifying} uploadFile={uploadFile} />;
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
