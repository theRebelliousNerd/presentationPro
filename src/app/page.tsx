'use client';

import { usePresentationStateArango as usePresentationState } from '@/hooks/use-presentation-state-arango';
import { Slide } from '@/lib/types';
import Header from '@/components/app/Header';
import DashboardShell from '@/components/app/dashboard/DashboardShell';
import TopBarCompact from '@/components/app/dashboard/TopBarCompact';
import InitialInput from '@/components/app/InitialInput';
import OutlineApproval from '@/components/app/OutlineApproval';
import GeneratingSpinner from '@/components/app/GeneratingSpinner';
import Editor from '@/components/app/editor/Editor';
import ErrorState from '@/components/app/ErrorState';
import { generateSlideContent } from '@/lib/actions';
import { initProject } from '@/lib/arango-client';
import { nanoid } from 'nanoid';
import { useRef, useState, useEffect } from 'react';
import { addUsage, estimateTokens } from '@/lib/token-meter';
import ClarificationChat from '@/components/app/ClarificationChat';
import PanelController from '@/components/app/PanelController';
import { Button } from '@/components/ui/button';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';

export default function Home() {
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
  } = usePresentationState();

  const [genProgress, setGenProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });
  const cancelGenerationRef = useRef(false);
  const [activeSlideIndex, setActiveSlideIndex] = useState<number | null>(null);

  const handleStartClarifying = async (values: {
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
    // Ensure project in Arango with folders + nodes
    try { if (presentation.id) await initProject(presentation.id, values as any) } catch {}
    setPresentation((prev) => ({
      ...prev,
      initialInput: { ...prev.initialInput, ...values },
    }));
    // Immediate autosave on start
    try { setTimeout(() => { saveNow().catch(()=>{}) }, 0) } catch {}
    setAppState('clarifying');
  };

  // Auto-open chat panel when entering clarifying
  useEffect(() => {
    if (appState === 'clarifying') {
      try { window.dispatchEvent(new CustomEvent('panel:toggle', { detail: { panel: 'chat' } })) } catch {}
    }
  }, [appState])

  const handleOutlineApproved = async (outline: string[]) => {
    setPresentation(prev => ({...prev, outline}));
    setAppState('generating');
    cancelGenerationRef.current = false;
    setGenProgress({ current: 0, total: outline.length });
    try {
      const generated: Slide[] = [];
      for (let i = 0; i < outline.length; i++) {
        if (cancelGenerationRef.current) break;
        const title = outline[i];
        // Generate one slide at a time for better progress control
        addUsage({ model: 'gemini-2.5-flash', kind: 'prompt', tokens: estimateTokens(title) + 1500, at: Date.now() } as any);
        const assets = [
          ...(presentation.initialInput.files || []).map(f => ({ name: f.name, url: f.url, kind: f.kind || (isImageUrl(f.url) ? 'image' : 'document') })),
          ...(presentation.initialInput.styleFiles || []).map(f => ({ name: f.name, url: f.url, kind: f.kind || (isImageUrl(f.url) ? 'image' : 'document') })),
        ];
        const constraints = {
          citationsRequired: presentation.initialInput.citationsRequired,
          slideDensity: presentation.initialInput.slideDensity,
          mustInclude: presentation.initialInput.mustInclude,
          mustAvoid: presentation.initialInput.mustAvoid,
        } as any;
        const [slide] = await generateSlideContent({ outline: [title], assets, constraints });
        const withId: Slide = { ...slide, id: nanoid(), imageState: 'done', useGeneratedImage: false };
        if ((slide as any).useAssetImageUrl) {
          withId.imageUrl = (slide as any).useAssetImageUrl;
          withId.assetImageUrl = (slide as any).useAssetImageUrl;
          withId.useGeneratedImage = false;
          withId.imageState = 'done';
        }
        generated.push(withId);
        const completionText = [slide.title, ...(slide.content||[]), slide.speakerNotes].join('\n');
        addUsage({ model: 'gemini-2.5-flash', kind: 'completion', tokens: estimateTokens(completionText), at: Date.now() } as any);
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
        return <InitialInput presentation={presentation} onStart={handleStartClarifying} uploadFile={uploadFile} />;
      case 'clarifying':
        return (
          <div className="text-center text-muted-foreground py-16">
            <div className="text-lg">Open Chat from the left sidebar to refine your goals.</div>
          </div>
        );
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
          onActiveSlideChange={(idx)=> setActiveSlideIndex(idx)}
          />;
      case 'error':
        return <ErrorState onReset={resetState} />
      default:
        return null;
    }
  };

  const leftChat = null;

  return (
    <DashboardShell>
      <div className="flex flex-col min-h-screen bg-background">
        <Header onReset={resetState} onSaveCopy={async () => { await duplicatePresentation(); }} onSaveNow={async () => { await saveNow(); }} />
        <main className="flex-grow flex flex-col p-2 md:p-3 gap-3">
        {/* Compact status bar */}
        <TopBarCompact />
        <div className="w-full flex gap-6">
          {leftChat}
          <div className={appState === 'editing' ? 'flex-grow flex' : 'flex-grow flex justify-center'}>
            <div className={appState === 'editing' ? 'w-full' : 'w-full max-w-5xl'}>
              {/* Clarifying state: if left chat is collapsed on large screens, show chat here */}
              {appState === 'clarifying' ? (
                <ClarificationChat
                  presentation={presentation}
                  setPresentation={setPresentation}
                  onClarificationComplete={(goals) => { setPresentation(prev => ({...prev, clarifiedGoals: goals})); setAppState('approving'); }}
                  uploadFile={uploadFile}
                />
              ) : (
                <>{renderState()}</>
              )}
            </div>
          </div>
        </div>
        </main>
      </div>
      <PanelController
        presentation={presentation as any}
        setPresentation={(updater:any)=> setPresentation(prev => (updater as any)(prev))}
        appState={appState}
        setAppState={setAppState as any}
        uploadFile={uploadFile}
        activeSlideIndex={activeSlideIndex ?? undefined}
      />
    </DashboardShell>
  );
}

function isImageUrl(u: string) {
  const base = u.split('?')[0].toLowerCase();
  return base.endsWith('.png') || base.endsWith('.jpg') || base.endsWith('.jpeg') || base.endsWith('.webp') || base.endsWith('.gif') || base.endsWith('.svg');
}
