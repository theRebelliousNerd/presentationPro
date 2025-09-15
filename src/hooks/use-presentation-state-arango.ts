'use client';
import { useState, useEffect, useCallback, Dispatch, SetStateAction, useRef } from 'react';
import { savePresentation, loadPresentation, arangoClient } from '@/lib/arango-client';
import type { AppState, Presentation, UploadedFileRef } from '@/lib/types';
import { nanoid } from 'nanoid';

const getInitialState = (id: string): {
  appState: AppState;
  presentation: Presentation;
} => ({
  appState: 'initial',
  presentation: {
    id: id,
    initialInput: {
      text: '',
      files: [],
      styleFiles: [],
      length: 'medium',
      audience: 'general',
      industry: '',
      subIndustry: '',
      tone: { formality: 2, energy: 2 },
      graphicStyle: 'modern',
      // Advanced clarity defaults
      objective: '',
      keyMessages: [],
      mustInclude: [],
      mustAvoid: [],
      callToAction: '',
      audienceExpertise: 'intermediate',
      timeConstraintMin: undefined,
      successCriteria: [],
      citationsRequired: false,
      slideDensity: 'normal',
      language: 'en',
      locale: 'en-US',
      readingLevel: 'intermediate',
      brandColors: [],
      brandFonts: [],
      logoUrl: '',
      presentationMode: 'in-person',
      screenRatio: '16:9',
      referenceStyle: 'none',
      allowedSources: [],
      bannedSources: [],
      accessibility: { highContrast: false, captions: false, altTextRequired: false },
      animationLevel: 'minimal',
      interactivity: { polls: false, quizzes: false },
      disclaimers: '',
    },
    chatHistory: [],
    clarifiedGoals: '',
    outline: [],
    slides: [],
  },
});

const DISABLE_ARANGO = process.env.NEXT_PUBLIC_DISABLE_ARANGO === 'true';

const VALID_APP_STATES: AppState[] = ['initial','clarifying','approving','generating','editing','error'];

export function usePresentationStateArango(presentationIdOverride?: string): {
  isLoaded: boolean;
  appState: AppState;
  setAppState: Dispatch<SetStateAction<AppState>>;
  presentation: Presentation;
  setPresentation: Dispatch<SetStateAction<Presentation>>;
  resetState: () => void;
  uploadFile: (file: File) => Promise<UploadedFileRef>;
  duplicatePresentation: () => Promise<string>;
  saveNow: () => Promise<void>;
} {
  const [isLoaded, setIsLoaded] = useState(false);
  const [appState, setAppState] = useState<AppState>('initial');
  const [presentation, setPresentation] = useState<Presentation>(getInitialState('').presentation);
  const [presentationId, setPresentationId] = useState<string | null>(null);
  const cancelAutosaveRef = useRef(false);

  // Load presentation ID from localStorage or create a new one
  useEffect(() => {
    if (presentationIdOverride) {
      setPresentationId(presentationIdOverride);
      return;
    }
    let currentId = localStorage.getItem('presentationId');
    if (!currentId) {
      currentId = nanoid();
      localStorage.setItem('presentationId', currentId);
    }
    setPresentationId(currentId);
  }, [presentationIdOverride]);

  // Load presentation from ArangoDB or localStorage
  useEffect(() => {
    if (presentationId) {
      const loadPresentationData = async () => {
        try {
          setIsLoaded(true); // Allow UI to render immediately

          if (!DISABLE_ARANGO) {
            // Try to load from ArangoDB
            const arangoPresentation = await loadPresentation(presentationId);

            if (arangoPresentation) {
              setPresentation(arangoPresentation);

              // Determine app state from loaded data
              const savedAppState = localStorage.getItem('appState') as AppState | null;
              if (savedAppState && VALID_APP_STATES.includes(savedAppState)) {
                setAppState(savedAppState);
              } else {
                const derived: AppState = arangoPresentation.slides.length > 0
                  ? 'editing'
                  : arangoPresentation.outline.length > 0
                  ? 'generating'
                  : arangoPresentation.clarifiedGoals
                  ? 'approving'
                  : arangoPresentation.chatHistory.length > 0
                  ? 'clarifying'
                  : 'initial';
                setAppState(derived);
              }
              return;
            }
          }

          // Fallback to localStorage or create new
          const initialState = getInitialState(presentationId);
          let restored = initialState.presentation;

          try {
            if (typeof window !== 'undefined') {
              const raw = localStorage.getItem('presentationDoc');
              if (raw) {
                const parsed = JSON.parse(raw) as Presentation;
                if (parsed && parsed.id === presentationId) {
                  restored = { ...restored, ...parsed };
                }
              }
            }
          } catch (e) {
            console.warn('Failed to load from localStorage:', e);
          }

          setPresentation(restored);
          const savedAppState = typeof window !== 'undefined' ? (localStorage.getItem('appState') as AppState) : 'initial';
          setAppState(savedAppState || 'initial');

        } catch (error) {
          console.error('Failed to load presentation:', error);

          // Fallback to initial state
          const initialState = getInitialState(presentationId);
          setPresentation(initialState.presentation);
          setAppState(initialState.appState);
        } finally {
          setIsLoaded(true);
        }
      };

      loadPresentationData();
    }
  }, [presentationId]);

  // Save presentation state to ArangoDB whenever it changes
  useEffect(() => {
    if (isLoaded && presentation.id && !cancelAutosaveRef.current) {
      const autoSave = async () => {
        try {
          await savePresentation(presentation);
        } catch (error) {
          console.error('Auto-save failed:', error);
        }
      };

      // Debounce auto-save
      const timeoutId = setTimeout(autoSave, 1000);
      return () => clearTimeout(timeoutId);
    }
  }, [presentation, isLoaded]);

  // Save app state to localStorage
  useEffect(() => {
    if(isLoaded && appState) {
      localStorage.setItem('appState', appState);
    }
  }, [appState, isLoaded]);

  const resetState = useCallback(() => {
    setIsLoaded(false);
    const newId = nanoid();
    localStorage.setItem('presentationId', newId);
    const initialState = getInitialState(newId);
    savePresentation(presentation); // Save old presentation one last time
    setPresentation(initialState.presentation);
    setAppState(initialState.appState);
    setPresentationId(newId);
    savePresentation(initialState.presentation); // Save the new blank state
    localStorage.setItem('appState', 'initial');
    setIsLoaded(true);
  }, [presentation]);

  const uploadFile = async (file: File): Promise<UploadedFileRef> => {
    // Ensure we have a presentation ID for namespacing uploads
    let idToUse = presentation.id;
    if (!idToUse) {
      idToUse = presentationId || nanoid();
      try {
        localStorage.setItem('presentationId', idToUse);
      } catch {}
      setPresentation(prev => ({ ...prev, id: idToUse! }));
      setPresentationId(idToUse);
    }

    // Always use local uploads for ArangoDB setup
    const form = new FormData();
    form.append('file', file);
    form.append('presentationId', idToUse!);
    form.append('filename', file.name);
    const res = await fetch('/api/upload', { method: 'POST', body: form });
    if (!res.ok) throw new Error('Local upload failed');
    const data = await res.json();
    return { name: data.name, url: data.url, path: data.path };
  };

  const duplicatePresentation = async (): Promise<string> => {
    if (!presentation.id) throw new Error('Cannot duplicate without a presentation loaded');

    const newId = nanoid();
    const copy: Presentation = {
      ...presentation,
      id: newId,
    };

    cancelAutosaveRef.current = true;
    try {
      await savePresentation(copy);

      // Update localStorage to point to new presentation
      localStorage.setItem('presentationId', newId);

    } finally {
      cancelAutosaveRef.current = false;
    }

    return newId;
  };

  const saveNow = async () => {
    await savePresentation(presentation);
  };

  return {
    isLoaded,
    appState,
    setAppState,
    presentation,
    setPresentation,
    resetState,
    uploadFile,
    duplicatePresentation,
    saveNow,
  };
}