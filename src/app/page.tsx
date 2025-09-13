'use client';

import { usePresentationState } from '@/hooks/use-presentation-state';
import { AppState, Slide } from '@/lib/types';
import Header from '@/components/app/Header';
import InitialInput from '@/components/app/InitialInput';
import ClarificationChat from '@/components/app/ClarificationChat';
import OutlineApproval from '@/components/app/OutlineApproval';
import GeneratingSpinner from '@/components/app/GeneratingSpinner';
import Editor from '@/components/app/editor/Editor';
import ErrorState from '@/components/app/ErrorState';
import { generateSlideContent } from '@/lib/actions';
import { nanoid } from 'nanoid';

export default function Home() {
  const {
    isLoaded,
    appState,
    setAppState,
    presentation,
    setPresentation,
    resetState,
    uploadFile,
  } = usePresentationState();

  const handleStartClarifying = (values: {
    text: string;
    files: { name: string; dataUrl: string }[];
    styleFiles: { name: string; dataUrl: string }[];
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
    try {
      const generatedSlides = await generateSlideContent({ outline });
      const slidesWithIds: Slide[] = generatedSlides.map((slide) => ({
        ...slide,
        id: nanoid(),
        imageState: 'loading',
      }));
      setPresentation(prev => ({...prev, slides: slidesWithIds}));
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
        return <InitialInput onStart={handleStartClarifying} />;
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
        return <GeneratingSpinner text="Generating your presentation..." />;
      case 'editing':
        return <Editor
          slides={presentation.slides}
          setSlides={(slides) => setPresentation(prev => ({...prev, slides}))}
          />;
      case 'error':
        return <ErrorState onReset={resetState} />
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Header onReset={resetState} />
      <main className="flex-grow flex flex-col items-center justify-center p-8 sm:p-12 md:p-16">
        {renderState()}
      </main>
    </div>
  );
}
