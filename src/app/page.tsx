'use client';

import { usePresentationState } from '@/hooks/use-presentation-state';
import { Slide } from '@/lib/types';
import Header from '@/components/app/Header';
import DashboardShell from '@/components/app/dashboard/DashboardShell';
import TopStats from '@/components/app/dashboard/TopStats';
import InitialInput from '@/components/app/InitialInput';
import OutlineApproval from '@/components/app/OutlineApproval';
import GeneratingSpinner from '@/components/app/GeneratingSpinner';
import Editor from '@/components/app/editor/Editor';
import ErrorState from '@/components/app/ErrorState';
import { generateSlideContent } from '@/lib/actions';
import { nanoid } from 'nanoid';
import { useRef, useState, useEffect } from 'react';
import { addUsage, estimateTokens } from '@/lib/token-meter';
import ClarificationChat from '@/components/app/ClarificationChat';
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
  } = usePresentationState();

  const [genProgress, setGenProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });
  const cancelGenerationRef = useRef(false);
  const [chatCollapsed, setChatCollapsed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    try { return localStorage.getItem('chat.collapsed') === 'true'; } catch { return false }
  });
  // Auto-collapse when viewport is narrower and no prior preference
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const hasPref = localStorage.getItem('chat.collapsed');
      if (!hasPref) {
        const w = window.innerWidth;
        if (w < 1440) setChatCollapsed(true);
      }
    } catch {}
  }, []);
  useEffect(() => {
    try { localStorage.setItem('chat.collapsed', String(chatCollapsed)); } catch {}
  }, [chatCollapsed]);

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
        const withId: Slide = { ...slide, id: nanoid(), imageState: 'loading', useGeneratedImage: true };
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

  const leftChat = (
    <div className="hidden lg:block">
      {!chatCollapsed ? (
        <ClarificationChat
          compact
          presentation={presentation}
          setPresentation={setPresentation}
          onClarificationComplete={(goals)=>{ setPresentation(prev=>({...prev, clarifiedGoals: goals})); setAppState('approving'); }}
          uploadFile={uploadFile}
        />
      ) : null}
    </div>
  );

  return (
    <DashboardShell>
      <div className="flex flex-col min-h-screen bg-background">
        <Header onReset={resetState} onSaveCopy={async () => { await duplicatePresentation(); }} />
        <main className="flex-grow flex flex-col p-4 sm:p-6 md:p-8 gap-6">
        {/* Top stats */}
        <TopStats />
        {/* Chat toggle (large screens) */}
        <div className="hidden lg:flex fixed left-2 top-[88px] z-20">
          <Button size="sm" variant="outline" onClick={() => setChatCollapsed(v => !v)}>
            {chatCollapsed ? (<><PanelLeftOpen className="h-4 w-4 mr-2"/>Show Chat</>) : (<><PanelLeftClose className="h-4 w-4 mr-2"/>Hide Chat</>)}
          </Button>
        </div>
        <div className="w-full flex gap-6">
          {leftChat}
          <div className="flex-grow flex justify-center">
            <div className="w-full max-w-5xl">
              {/* Clarifying state: if left chat is collapsed on large screens, show chat here */}
              {appState === 'clarifying' ? (
                chatCollapsed ? (
                  <ClarificationChat
                    presentation={presentation}
                    setPresentation={setPresentation}
                    onClarificationComplete={(goals) => { setPresentation(prev => ({...prev, clarifiedGoals: goals})); setAppState('approving'); }}
                    uploadFile={uploadFile}
                  />
                ) : (
                  <div className="hidden lg:block">{/* Content handled by left chat when expanded */}</div>
                )
              ) : (
                <>{renderState()}</>
              )}
            </div>
          </div>
        </div>
        </main>
      </div>
    </DashboardShell>
  );
}

function isImageUrl(u: string) {
  const base = u.split('?')[0].toLowerCase();
  return base.endsWith('.png') || base.endsWith('.jpg') || base.endsWith('.jpeg') || base.endsWith('.webp') || base.endsWith('.gif') || base.endsWith('.svg');
}
