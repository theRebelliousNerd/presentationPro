export type ChatMessage = {
  role: 'user' | 'model';
  content: string;
};

export type Slide = {
  id: string;
  title: string;
  content: string[];
  speakerNotes: string;
  imagePrompt: string;
  imageUrl?: string;
  imageState?: 'loading' | 'error' | 'done';
};

export type Presentation = {
  initialInput: {
    text: string;
    files: { name: string; dataUrl: string }[];
    length: string;
    audience: string;
  };
  chatHistory: ChatMessage[];
  clarifiedGoals: string;
  outline: string[];
  slides: Slide[];
};

export type AppState =
  | 'initial'
  | 'clarifying'
  | 'approving'
  | 'generating'
  | 'editing'
  | 'error';
