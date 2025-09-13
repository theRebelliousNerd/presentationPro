'use client';
import { useState, useEffect, useCallback, Dispatch, SetStateAction } from 'react';
import type { AppState, Presentation } from '@/lib/types';

const getInitialState = (): {
  appState: AppState;
  presentation: Presentation;
} => ({
  appState: 'initial',
  presentation: {
    initialInput: { text: '', files: [], length: 'medium', audience: 'general', tone: 'educational', mood: 'neutral', colorScheme: 'default' },
    chatHistory: [],
    clarifiedGoals: '',
    outline: [],
    slides: [],
  },
});

export function usePresentationState(): {
  isLoaded: boolean;
  appState: AppState;
  setAppState: Dispatch<SetStateAction<AppState>>;
  presentation: Presentation;
  setPresentation: Dispatch<SetStateAction<Presentation>>;
  resetState: () => void;
} {
  const [isLoaded, setIsLoaded] = useState(false);
  const [appState, setAppState] = useState<AppState>('initial');
  const [presentation, setPresentation] = useState<Presentation>(
    getInitialState().presentation
  );

  useEffect(() => {
    try {
      const savedState = localStorage.getItem('presentationState');
      if (savedState) {
        const { appState: savedAppState, presentation: savedPresentation } =
          JSON.parse(savedState);
        if (savedAppState && savedPresentation) {
          setAppState(savedAppState);
          // Ensure new fields have default values if not in saved state
          const fullPresentation = { ...getInitialState().presentation, ...savedPresentation };
          setPresentation(fullPresentation);
        }
      }
    } catch (error) {
      console.error('Failed to load state from localStorage:', error);
      const initialState = getInitialState();
      setAppState(initialState.appState);
      setPresentation(initialState.presentation);
    }
    setIsLoaded(true);
  }, []);

  useEffect(() => {
    if (isLoaded) {
      try {
        const stateToSave = JSON.stringify({ appState, presentation });
        localStorage.setItem('presentationState', stateToSave);
      } catch (error) {
        console.error('Failed to save state to localStorage:', error);
      }
    }
  }, [appState, presentation, isLoaded]);

  const resetState = useCallback(() => {
    const initialState = getInitialState();
    setAppState(initialState.appState);
    setPresentation(initialState.presentation);
    try {
      localStorage.removeItem('presentationState');
    } catch (error) {
      console.error('Failed to remove state from localStorage:', error);
    }
  }, []);

  return {
    isLoaded,
    appState,
    setAppState,
    presentation,
    setPresentation,
    resetState,
  };
}
