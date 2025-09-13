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
    console.error('Firestore is not initialized.');
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
  const [presentation, setPresentation] = useState<Presentation>(getInitialState(nanoid()).presentation);
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
      const presRef = doc(db, 'presentations', presentationId);
      const unsubscribe = onSnapshot(presRef, (docSnap) => {
        if (docSnap.exists()) {
          const data = docSnap.data() as Presentation;
          // Merge with initial state to ensure all fields are present
          const fullPresentation = { ...getInitialState(presentationId).presentation, ...data };
          setPresentation(fullPresentation);
          const savedAppState = localStorage.getItem('appState');
          setAppState((savedAppState as AppState) || 'initial');
        } else {
          // If no doc, initialize a new one
          const initialState = getInitialState(presentationId);
          setPresentation(initialState.presentation);
          setAppState(initialState.appState);
        }
        setIsLoaded(true);
      });
      return () => unsubscribe();
    } else if (presentationId) {
      // Handle case where db is not yet initialized
      const initialState = getInitialState(presentationId);
      setPresentation(initialState.presentation);
      setAppState(initialState.appState);
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
    if(isLoaded) {
      localStorage.setItem('appState', appState);
    }
  }, [appState, isLoaded]);

  const resetState = useCallback(() => {
    const newId = nanoid();
    localStorage.setItem('presentationId', newId);
    setPresentationId(newId);
    const initialState = getInitialState(newId);
    setAppState(initialState.appState);
    setPresentation(initialState.presentation);
    savePresentation(initialState.presentation); // Save the new blank state
    localStorage.setItem('appState', 'initial');
  }, []);
  
  const uploadFile = async (file: File) => {
    if (!storage || !presentation.id) {
      throw new Error('Firebase Storage or presentation ID is not available.');
    }
    const storageRef = ref(storage, `presentations/${presentation.id}/${file.name}`);
    await uploadBytes(storageRef, file);
    const downloadURL = await getDownloadURL(storageRef);
    // Convert to dataUrl for consistency with other parts of the app for now
    // In a future step we can refactor to use the URL directly
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
