'use client';
import { useState, useEffect, useCallback, Dispatch, SetStateAction } from 'react';
import { doc, setDoc, onSnapshot } from 'firebase/firestore';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { db, storage } from '@/lib/firebase';
import type { AppState, Presentation } from '@/lib/types';
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
    },
    chatHistory: [],
    clarifiedGoals: '',
    outline: [],
    slides: [],
  },
});

async function savePresentation(presentation: Presentation) {
  if (!db) {
    console.warn('Firestore is not initialized yet. Skipping save.');
    return;
  }
  try {
    const presRef = doc(db, 'presentations', presentation.id);
    await setDoc(presRef, presentation, { merge: true });
  } catch (error) {
    console.error('Failed to save presentation to Firestore:', error);
  }
}

export function usePresentationState(): {
  isLoaded: boolean;
  appState: AppState;
  setAppState: Dispatch<SetStateAction<AppState>>;
  presentation: Presentation;
  setPresentation: Dispatch<SetStateAction<Presentation>>;
  resetState: () => void;
  uploadFile: (file: File) => Promise<{ name: string; dataUrl: string; }>;
} {
  const [isLoaded, setIsLoaded] = useState(false);
  const [appState, setAppState] = useState<AppState>('initial');
  const [presentation, setPresentation] = useState<Presentation>(getInitialState('').presentation);
  const [presentationId, setPresentationId] = useState<string | null>(null);

  // Load presentation ID from localStorage or create a new one
  useEffect(() => {
    let currentId = localStorage.getItem('presentationId');
    if (!currentId) {
      currentId = nanoid();
      localStorage.setItem('presentationId', currentId);
    }
    setPresentationId(currentId);
  }, []);

  // Subscribe to Firestore for presentation updates
  useEffect(() => {
    if (presentationId && db) {
      setIsLoaded(true); // Allow UI to render immediately
      const presRef = doc(db, 'presentations', presentationId);
      const unsubscribe = onSnapshot(presRef, (docSnap) => {
        if (docSnap.exists()) {
          const data = docSnap.data() as Presentation;
          const fullPresentation = { ...getInitialState(presentationId).presentation, ...data };
          setPresentation(fullPresentation);
          const savedAppState = localStorage.getItem('appState') as AppState | null;
          // Only set app state from localStorage if it's valid and we are in a consistent state
          if (savedAppState && Object.keys(getInitialState('').presentation).includes(savedAppState)) {
             setAppState(savedAppState);
          } else {
             setAppState(fullPresentation.slides.length > 0 ? 'editing' : (fullPresentation.clarifiedGoals ? 'approving' : (fullPresentation.chatHistory.length > 0 ? 'clarifying' : 'initial')));
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
      // Handle case where db is not yet initialized (e.g. server-side)
      const initialState = getInitialState(presentationId);
      setPresentation(initialState.presentation);
      const savedAppState = typeof window !== 'undefined' ? localStorage.getItem('appState') as AppState : 'initial';
      setAppState(savedAppState || 'initial');
      setIsLoaded(true);
    }
  }, [presentationId]);


  // Save presentation state to Firestore whenever it changes
  useEffect(() => {
    if (isLoaded && presentation.id) {
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
  
  const uploadFile = async (file: File) => {
    if (!storage || !presentation.id) {
      throw new Error('Firebase Storage or presentation ID is not available.');
    }
    const storageRef = ref(storage, `presentations/${presentation.id}/${file.name}`);
    await uploadBytes(storageRef, file);
    const downloadURL = await getDownloadURL(storageRef);
    
    // Convert to dataUrl for consistency for now
    const response = await fetch(downloadURL);
    const blob = await response.blob();
    const dataUrl = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.readAsDataURL(blob);
    });

    return { name: file.name, dataUrl };
  };

  return {
    isLoaded,
    appState,
    setAppState,
    presentation,
    setPresentation,
    resetState,
    uploadFile,
  };
}
