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
  designCode?: { css?: string; svg?: string };
  // Per-slide constraint overrides
  useConstraints?: boolean; // true=use global (default), false=use overrides
  constraintsOverride?: {
    citationsRequired?: boolean;
    slideDensity?: 'light' | 'normal' | 'dense';
    mustInclude?: string[];
    mustAvoid?: string[];
  };
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
    // Advanced clarity fields (optional)
    objective?: string;
    keyMessages?: string[];
    mustInclude?: string[];
    mustAvoid?: string[];
    callToAction?: string;
    audienceExpertise?: 'beginner' | 'intermediate' | 'expert';
    timeConstraintMin?: number;
    successCriteria?: string[];
    citationsRequired?: boolean;
    slideDensity?: 'light' | 'normal' | 'dense';
    language?: string;
    locale?: string;
    readingLevel?: 'basic' | 'intermediate' | 'advanced';
    brandColors?: string[];
    brandFonts?: string[];
    logoUrl?: string;
    presentationMode?: 'in-person' | 'virtual' | 'hybrid';
    screenRatio?: '16:9' | '4:3' | '1:1';
    referenceStyle?: 'apa' | 'mla' | 'chicago' | 'none';
    allowedSources?: string[]; // domains
    bannedSources?: string[];
    accessibility?: { highContrast?: boolean; captions?: boolean; altTextRequired?: boolean };
    animationLevel?: 'none' | 'minimal' | 'moderate' | 'high';
    interactivity?: { polls?: boolean; quizzes?: boolean };
    disclaimers?: string;
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
