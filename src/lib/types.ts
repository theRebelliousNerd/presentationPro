export type ChatMessage = {
  id: string;
  role: 'user' | 'model';
  content: string;
  createdAt?: number;
};

export type Slide = {
  id: string;
  title: string;
  content: string[];
  speakerNotes: string;
  imagePrompt: string;
  imageUrl?: string;
  imageState?: 'loading' | 'error' | 'done';
  useGeneratedImage?: boolean;
  assetImageUrl?: string;
};

export type UploadedFileRef = {
  name: string;
  /** Public download URL to the file in Storage */
  url: string;
  /** Optional storage path for internal reference */
  path?: string;
  kind?: 'image' | 'document' | 'other';
};

export type Presentation = {
  id: string;
  initialInput: {
    text: string;
    files: UploadedFileRef[];
    styleFiles: UploadedFileRef[];
    length: string;
    audience: string;
    industry: string;
    subIndustry: string;
    tone: { formality: number; energy: number };
    graphicStyle: string;
  };
  chatHistory: ChatMessage[];
  clarifiedGoals: string;
  outline: string[];
  slides: Slide[];
  fullScript?: string;
  theme?: 'brand' | 'muted' | 'dark';
};

export type AppState =
  | 'initial'
  | 'clarifying'
  | 'approving'
  | 'generating'
  | 'editing'
  | 'error';
