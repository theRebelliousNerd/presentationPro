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
  // Quality metrics from VisionCV
  qualityMetrics?: {
    overall?: number;
    contrast?: {
      score: number;
      ratio: number;
      passes: boolean;
      level?: 'AA' | 'AAA' | 'AA-large';
    };
    blur?: {
      score: number;
      level: number;
      passes: boolean;
    };
    saliency?: {
      score: number;
      hotspots: number;
      distribution: 'concentrated' | 'balanced' | 'scattered';
    };
    brand?: {
      score: number;
      violations: string[];
      passes: boolean;
    };
    placement?: {
      score: number;
      confidence: number;
      suggestions: number;
    };
  };
  // New structured spec for HTML/CSS/SVG-driven designs
  designSpec?: {
    tokens?: {
      colors?: { bg?: string; primary?: string; muted?: string; text?: string };
      textColors?: { title?: string; body?: string };
      fonts?: { headline?: string; body?: string };
      typeScale?: 'normal' | 'large';
      spacing?: number; // base spacing unit in px
      radii?: number;   // base border radius in px
    };
    background?: {
      css?: string; // e.g., linear-gradient string for backgroundImage
      svg?: string; // inline SVG overlay
      intensity?: number; // 0..1
      safeAreas?: { x: number; y: number; w: number; h: number }[];
    };
    layout?: {
      type?: string; // e.g., 'title_bullets_left'
      slots?: { [slotName: string]: string }; // CSS selectors for slot anchors
      html?: string; // sanitized HTML fragment
      css?: string;  // sanitized CSS scoped to container
      svg?: string;  // optional additional SVG elements
      components?: string[]; // optional component names
    };
    accessibility?: { minContrast?: number; warnings?: string[] };
    variantId?: string;
    rationale?: string;
    score?: number;
    placementCandidates?: Array<{
      bounding_box?: { x?: number; y?: number; width?: number; height?: number };
      score?: number;
      mean_saliency?: number;
      thirds_distance?: number;
      area?: number;
    }>;
    placementFrame?: { width: number; height: number };
    selectedPlacement?: number; // Index of selected placement candidate
    appliedPlacement?: { // The actually applied placement
      bounding_box?: { x?: number; y?: number; width?: number; height?: number };
      score?: number;
      mean_saliency?: number;
      thirds_distance?: number;
      area?: number;
    };
  };
  design?: {
    tokens?: Record<string, string>;
    layers?: Array<{ kind?: string; token?: string; css?: string; columns?: number; gutter?: string; weights?: number[] }>;
    image?: { url?: string; prompt?: string; path?: string };
    type?: string;
    prompt?: string;
  };
  qualityMeta?: {
    overallScore?: number;
    accessibilityScore?: number;
    brandScore?: number;
    clarityScore?: number;
    issuesFound?: string[];
    fixesApplied?: string[];
    requiresManualReview?: boolean;
    qualityLevel?: string;
  };
  ragSources?: any[];
  criticReview?: { issues: string[]; suggestions: string[] };
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

export type ResearchNote = {
  id: string;
  query: string;
  rules: string[];
  createdAt: string;
  allowDomains?: string[];
  topK?: number;
  model?: string;
  extractions?: string[];
};

export type Presentation = {
  id: string;
  initialInput: {
    text: string;
    files: UploadedFileRef[];
    styleFiles: UploadedFileRef[];
    graphicsFiles?: UploadedFileRef[];
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
    template?: string;
  };
  chatHistory: ChatMessage[];
  clarifiedGoals: string;
  outline: string[];
  slides: Slide[];
  fullScript?: string;
  researchNotebook?: ResearchNote[];
  theme?: 'brand' | 'muted' | 'dark';
  workflowSessionId?: string;
  workflowState?: any;
  workflowTrace?: any[];
};

export type AppState =
  | 'initial'
  | 'clarifying'
  | 'approving'
  | 'generating'
  | 'editing'
  | 'error';
