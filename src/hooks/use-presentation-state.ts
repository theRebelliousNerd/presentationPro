'use client';
import { useState, useEffect, useCallback, Dispatch, SetStateAction, useRef } from 'react';
import { doc, setDoc, onSnapshot } from 'firebase/firestore';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { db, storage } from '@/lib/firebase';
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

const DISABLE_FIRESTORE = process.env.NEXT_PUBLIC_DISABLE_FIRESTORE === 'true';

async function savePresentation(presentation: Presentation) {
  if (DISABLE_FIRESTORE || !db) {
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('presentationDoc', JSON.stringify(presentation));
      }
    } catch (e) {
      console.warn('Failed to persist presentation locally:', e);
    }
    return;
  }
  try {
    const presRef = doc(db, 'presentations', presentation.id);
    await setDoc(presRef, presentation, { merge: true });
  } catch (error) {
    console.error('Failed to save presentation to Firestore:', error);
  }
}

const VALID_APP_STATES: AppState[] = ['initial','clarifying','approving','generating','editing','error'];

export function usePresentationState(presentationIdOverride?: string): {
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

  // Subscribe to Firestore for presentation updates
  useEffect(() => {
    if (presentationId && db && !DISABLE_FIRESTORE) {
      setIsLoaded(true); // Allow UI to render immediately
      const presRef = doc(db, 'presentations', presentationId);
      const unsubscribe = onSnapshot(presRef, (docSnap) => {
        if (docSnap.exists()) {
          const data = docSnap.data() as Presentation;
          const fullPresentation = { ...getInitialState(presentationId).presentation, ...data };
          setPresentation(fullPresentation);
          const savedAppState = localStorage.getItem('appState') as AppState | null;
          if (savedAppState && VALID_APP_STATES.includes(savedAppState)) {
            setAppState(savedAppState);
          } else {
            const derived: AppState = fullPresentation.slides.length > 0
              ? 'editing'
              : fullPresentation.outline.length > 0
              ? 'generating'
              : fullPresentation.clarifiedGoals
              ? 'approving'
              : fullPresentation.chatHistory.length > 0
              ? 'clarifying'
              : 'initial';
            setAppState(derived);
          }

        } else {
          // If no doc, initialize a new one and save it
          const initialState = getInitialState(presentationId);
          setPresentation(initialState.presentation);
          setAppState(initialState.appState);
          savePresentation(initialState.presentation);
        }
      });
      return () => unsubscribe();
    } else if (presentationId) {
      // Local-only mode (no Firestore) for development
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
      } catch {}
      setPresentation(restored);
      const savedAppState = typeof window !== 'undefined' ? (localStorage.getItem('appState') as AppState) : 'initial';
      setAppState(savedAppState || 'initial');
      setIsLoaded(true);
    }
  }, [presentationId]);


  // Save presentation state to Firestore whenever it changes
  useEffect(() => {
    if (isLoaded && presentation.id && !cancelAutosaveRef.current) {
      savePresentation(presentation);
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

    const useLocal = process.env.NEXT_PUBLIC_LOCAL_UPLOADS === 'true' || !storage;
    if (useLocal) {
      // Upload via local API to write files under public/uploads
      const form = new FormData();
      form.append('file', file);
      form.append('presentationId', idToUse!);
      form.append('filename', file.name);
      const res = await fetch('/api/upload', { method: 'POST', body: form });
      if (!res.ok) throw new Error('Local upload failed');
      const data = await res.json();
      return { name: data.name, url: data.url, path: data.path };
    }

    // Default: Firebase Storage
    const safeName = file.name.replace(/[^\w\-.]+/g, '_');
    const path = `presentations/${idToUse}/${safeName}`;
    const storageRef = ref(storage, path);
    await uploadBytes(storageRef, file);
    const url = await getDownloadURL(storageRef);
    return { name: file.name, url, path };
  };

  const duplicatePresentation = async (): Promise<string> => {
    if (!db || !presentation.id) throw new Error('Cannot duplicate without a presentation loaded');
    const newId = nanoid();
    const copy: Presentation = {
      ...presentation,
      id: newId,
    };
    cancelAutosaveRef.current = true;
    try {
      await setDoc(doc(db, 'presentations', newId), copy, { merge: true });
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
