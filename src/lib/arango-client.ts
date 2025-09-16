'use client';

/**
 * Frontend ArangoDB client that interfaces with the existing ADK backend infrastructure.
 * Leverages the EnhancedArangoClient schema and operations already built into the agents.
 */

import type { Presentation, AppState } from './types';
import { resolveAdkBaseUrl } from '@/lib/base-url';

function runtimeBaseUrl(): string {
  return resolveAdkBaseUrl();
}
const DISABLE_ARANGO = process.env.NEXT_PUBLIC_DISABLE_ARANGO === 'true';

interface ArangoResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

interface PresentationState {
  metadata?: {
    presentation_id: string;
    user_id: string;
    title?: string;
    status: AppState;
    created_at: string;
    updated_at: string;
    preferences?: any;
    clarified_goals?: string;
  };
  clarifications?: Array<{
    presentation_id: string;
    sequence: number;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
  outline?: {
    presentation_id: string;
    outline: string[];
    agent_source: string;
    created_at: string;
    updated_at: string;
  };
  slides?: Array<{
    presentation_id: string;
    slide_index: number;
    title: string;
    content: string[];
    speaker_notes: string;
    image_prompt: string;
    image_url?: string;
    use_generated_image?: boolean;
    asset_image_url?: string;
    design_code?: any;
    design_spec?: any;
    constraints_override?: any;
    use_constraints?: boolean;
    version: number;
    agent_source: string;
    created_at: string;
    updated_at: string;
  }>;
  design_spec?: { design_data?: any };
  research_notes?: Array<{
    presentation_id: string;
    note_id?: string;
    query?: string;
    rules?: string[];
    created_at?: string;
    allow_domains?: string[];
    top_k?: number;
    model?: string;
    extractions?: string[];
  }>;
  script?: { script_content?: string };
}

class ArangoClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = runtimeBaseUrl();
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ArangoResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        return {
          success: false,
          error: `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Create a new presentation in ArangoDB
   */
  async createPresentation(presentationId: string, userId: string = 'default'): Promise<ArangoResponse> {
    return this.request('/v1/arango/presentations', {
      method: 'POST',
      body: JSON.stringify({
        presentation_id: presentationId,
        user_id: userId,
        status: 'initial',
      }),
    });
  }

  /**
   * Update presentation status and metadata
   */
  async updatePresentationStatus(
    presentationId: string,
    status: AppState,
    title?: string
  ): Promise<ArangoResponse> {
    return this.request(`/v1/arango/presentations/${presentationId}/status`, {
      method: 'PUT',
      body: JSON.stringify({
        status,
        title,
      }),
    });
  }

  /**
   * Get complete presentation state from all collections
   */
  async getPresentationState(presentationId: string): Promise<ArangoResponse<PresentationState>> {
    return this.request(`/v1/arango/presentations/${presentationId}/state`);
  }

  /**
   * Save presentation data (converted from frontend Presentation type)
   */
  async savePresentation(presentation: Presentation): Promise<ArangoResponse> {
    const operations = [] as any[];

    const metadataPatch: Record<string, any> = {
      presentation_id: presentation.id,
      user_id: 'default',
      title: this.extractTitle(presentation),
      status: this.inferStatus(presentation),
      preferences: presentation.initialInput,
    };
    if (typeof presentation.clarifiedGoals === 'string') {
      metadataPatch.clarified_goals = presentation.clarifiedGoals;
    }
    operations.push({ operation: 'update_metadata', data: metadataPatch });

    const clarifications = (presentation.chatHistory || []).map((msg, index) => ({
      sequence: index + 1,
      role: msg.role === 'user' ? 'user' : 'assistant',
      content: msg.content,
    }));
    operations.push({
      operation: 'save_clarifications',
      data: { presentation_id: presentation.id, clarifications },
    });

    operations.push({
      operation: 'save_outline',
      data: { presentation_id: presentation.id, outline: presentation.outline || [] },
    });

    const slidePayload = (presentation.slides || []).map((slide, index) => ({
      slide_index: index,
      title: slide.title,
      content: slide.content || [],
      speaker_notes: slide.speakerNotes || '',
      image_prompt: slide.imagePrompt || '',
      image_url: slide.imageUrl || undefined,
      use_generated_image: typeof slide.useGeneratedImage === 'boolean' ? slide.useGeneratedImage : undefined,
      asset_image_url: slide.assetImageUrl || undefined,
      design_code: slide.designCode || undefined,
      design_spec: slide.designSpec || undefined,
      constraints_override: slide.constraintsOverride || undefined,
      use_constraints: typeof slide.useConstraints === 'boolean' ? slide.useConstraints : undefined,
    }));
    operations.push({
      operation: 'save_slides',
      data: { presentation_id: presentation.id, slides: slidePayload },
    });

    const researchNotes = (presentation.researchNotebook || []).map((note, index) => ({
      note_id: note.id || `${presentation.id}:note:${index}`,
      query: note.query,
      rules: note.rules || [],
      allow_domains: note.allowDomains || [],
      top_k: typeof note.topK === 'number' ? note.topK : undefined,
      model: note.model,
      created_at: note.createdAt || new Date().toISOString(),
      extractions: note.extractions || [],
    }));
    operations.push({
      operation: 'save_research_notes',
      data: { presentation_id: presentation.id, notes: researchNotes },
    });



    // Persist clarified goals even when clearing them so Arango stays in sync
    operations.push({
      operation: 'save_goals',
      data: {
        presentation_id: presentation.id,
        clarified_goals: presentation.clarifiedGoals || '',
      },
    });

    if ('fullScript' in presentation) {
      operations.push({
        operation: 'save_script',
        data: {
          presentation_id: presentation.id,
          script: presentation.fullScript || '',
        },
      });
    }

    return this.request('/v1/arango/presentations/batch', {
      method: 'POST',
      body: JSON.stringify({ operations }),
    });
  }

  /**
   * Convert ArangoDB state back to frontend Presentation format
   */
  arangoStateToPresentation(state: PresentationState, fallbackPresentation: Presentation): Presentation {
    const presentation: Presentation = {
      ...fallbackPresentation,
      id: state.metadata?.presentation_id || fallbackPresentation.id,
    };

    const metadata = state.metadata || {};
    if (metadata.preferences && typeof metadata.preferences === 'object') {
      presentation.initialInput = { ...presentation.initialInput, ...(metadata.preferences as any) };
    }

    let clarifiedGoals = metadata.clarified_goals || presentation.clarifiedGoals || '';
    const clarifications = state.clarifications ? [...state.clarifications] : [];
    if (clarifications.length) {
      const history = clarifications
        .sort((a, b) => a.sequence - b.sequence)
        .reduce<Presentation['chatHistory']>((acc, clarification) => {
          const content = clarification.content || '';
          if (typeof content === 'string' && content.startsWith('CLARIFIED_GOALS:')) {
            clarifiedGoals = content.replace('CLARIFIED_GOALS:', '').trim();
            return acc;
          }
          acc.push({
            role: clarification.role === 'user' ? 'user' : 'model',
            content,
          });
          return acc;
        }, []);
      presentation.chatHistory = history;
    } else {
      presentation.chatHistory = presentation.chatHistory || [];
    }

    if (clarifiedGoals) {
      presentation.clarifiedGoals = clarifiedGoals;
    }

    if (state.outline?.outline) {
      presentation.outline = [...state.outline.outline];
    } else {
      presentation.outline = presentation.outline || [];
    }

    if (state.slides) {
      presentation.slides = state.slides
        .sort((a, b) => a.slide_index - b.slide_index)
        .map(slide => ({
          id: `${state.metadata?.presentation_id || fallbackPresentation.id}:${slide.slide_index}`,
          title: slide.title,
          content: slide.content || [],
          speakerNotes: slide.speaker_notes || '',
          imagePrompt: slide.image_prompt || '',
          imageUrl: slide.image_url || slide.asset_image_url || undefined,
          assetImageUrl: slide.asset_image_url || undefined,
          useGeneratedImage: typeof slide.use_generated_image === 'boolean' ? slide.use_generated_image : false,
          designCode: slide.design_code || undefined,
          designSpec: slide.design_spec || undefined,
          constraintsOverride: slide.constraints_override || undefined,
          useConstraints: typeof slide.use_constraints === 'boolean' ? slide.use_constraints : undefined,
          imageState: 'done',
        } as any));
    }

    if (state.design_spec?.design_data) {
      (presentation as any).designSpec = state.design_spec.design_data;
    }

    if (state.script && 'script_content' in state.script) {
      presentation.fullScript = state.script.script_content || '';
    }

    if (state.research_notes) {
      presentation.researchNotebook = state.research_notes.map((note: any, index: number) => ({
        id: note.note_id || `${presentation.id}:note:${index}`,
        query: note.query || '',
        rules: Array.isArray(note.rules) ? note.rules.filter(Boolean) : [],
        createdAt: note.created_at || note.updated_at || new Date().toISOString(),
        allowDomains: Array.isArray(note.allow_domains) ? note.allow_domains : undefined,
        topK: typeof note.top_k === 'number' ? note.top_k : undefined,
        model: note.model,
        extractions: Array.isArray(note.extractions) ? note.extractions : undefined,
      }));
    } else if (!presentation.researchNotebook) {
      presentation.researchNotebook = [];
    }

    return presentation;
  }

  /**
   * Extract title from presentation (various fallbacks)
   */
  private extractTitle(presentation: Presentation): string {
    // Try to extract from initial input
    if (presentation.initialInput?.text) {
      const lines = presentation.initialInput.text.split('\n');
      const firstLine = lines[0].trim();
      if (firstLine.length > 0 && firstLine.length < 100) {
        return firstLine;
      }
    }

    // Try first slide title
    if (presentation.slides && presentation.slides.length > 0) {
      return presentation.slides[0].title;
    }

    // Try first outline item
    if (presentation.outline && presentation.outline.length > 0) {
      const first = presentation.outline[0] as any;
      if (typeof first === 'string') {
        return first;
      }
      if (first && typeof first === 'object' && typeof first.title === 'string') {
        return first.title;
      }
    }

    return 'Untitled Presentation';
  }

  /**
   * Infer presentation status from content
   */
  private inferStatus(presentation: Presentation): AppState {
    if (presentation.slides && presentation.slides.length > 0) {
      return 'editing';
    }
    if (presentation.outline && presentation.outline.length > 0) {
      return 'generating';
    }
    if (presentation.clarifiedGoals) {
      return 'approving';
    }
    if (presentation.chatHistory && presentation.chatHistory.length > 0) {
      return 'clarifying';
    }
    return 'initial';
  }

  /**
   * Health check for ArangoDB connection
   */
  async healthCheck(): Promise<ArangoResponse> {
    return this.request('/v1/arango/health');
  }
}

// Singleton instance
export const arangoClient = new ArangoClient();

/**
 * Save presentation to ArangoDB with fallback to localStorage
 */
export async function savePresentation(presentation: Presentation): Promise<void> {
  if (DISABLE_ARANGO) {
    // Fallback to localStorage
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
    // Ensure presentation exists in ArangoDB
    await arangoClient.createPresentation(presentation.id);

    // Save complete presentation state
    const result = await arangoClient.savePresentation(presentation);

    if (!result.success) {
      throw new Error(result.error || 'Failed to save presentation');
    }

    console.log('Successfully saved presentation to ArangoDB:', presentation.id);
  } catch (error) {
    console.error('Failed to save presentation to ArangoDB:', error);

    // Fallback to localStorage
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('presentationDoc', JSON.stringify(presentation));
      }
    } catch (e) {
      console.warn('Failed to persist presentation locally:', e);
    }
  }
}

// --- Project listing and management ---

export async function listPresentations(limit = 50): Promise<{ presentation_id: string; user_id?: string; title?: string; status?: string; created_at?: string; updated_at?: string }[]> {
  const base = runtimeBaseUrl()
  try {
    const res = await fetch(`${base}/v1/arango/presentations?limit=${limit}`)
    if (!res.ok) return []
    const js = await res.json() as any
    if (js && js.success && Array.isArray(js.data)) return js.data
  } catch {}
  return []
}

export async function createPresentationRecord(presentationId: string, userId = 'default'): Promise<boolean> {
  const base = runtimeBaseUrl()
  try {
    const res = await fetch(`${base}/v1/arango/presentations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ presentation_id: presentationId, user_id: userId, status: 'initial' }) })
    return res.ok
  } catch { return false }
}

export async function initProject(presentationId: string, initialInput: any): Promise<boolean> {
  const base = runtimeBaseUrl()
  try {
    const res = await fetch(`${base}/v1/arango/presentations/${encodeURIComponent(presentationId)}/init`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ initialInput })
    })
    return res.ok
  } catch { return false }
}

/**
 * Load presentation from ArangoDB with fallback to localStorage
 */
export async function loadPresentation(presentationId: string): Promise<Presentation | null> {
  if (DISABLE_ARANGO) {
    // Load from localStorage only
    try {
      if (typeof window !== 'undefined') {
        const raw = localStorage.getItem('presentationDoc');
        if (raw) {
          const parsed = JSON.parse(raw) as Presentation;
          if (parsed && parsed.id === presentationId) {
            return parsed;
          }
        }
      }
    } catch (e) {
      console.warn('Failed to load presentation from localStorage:', e);
    }
    return null;
  }

  try {
    const result = await arangoClient.getPresentationState(presentationId);

    if (result.success && result.data) {
      // Convert ArangoDB state to frontend format
      const fallbackPresentation: Presentation = {
        id: presentationId,
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
        fullScript: '',
        researchNotebook: [],
      };

      return arangoClient.arangoStateToPresentation(result.data, fallbackPresentation);
    }
  } catch (error) {
    console.error('Failed to load presentation from ArangoDB:', error);
  }

  // Fallback to localStorage
  try {
    if (typeof window !== 'undefined') {
      const raw = localStorage.getItem('presentationDoc');
      if (raw) {
        const parsed = JSON.parse(raw) as Presentation;
        if (parsed && parsed.id === presentationId) {
          return parsed;
        }
      }
    }
  } catch (e) {
    console.warn('Failed to load presentation from localStorage:', e);
  }

  return null;
}

export default arangoClient;

export async function fetchPresentationGraph(presentationId: string): Promise<{ slides: any[]; assets: any[]; edges: any[] }> {
  const base = runtimeBaseUrl();
  try {
    const res = await fetch(`${base}/v1/arango/presentations/${encodeURIComponent(presentationId)}/graph`);
    if (!res.ok) throw new Error('Graph fetch failed');
    const js = await res.json() as any;
    if (js && js.success && js.data) {
      return js.data;
    }
  } catch (e) {
    console.warn('Graph fetch failed', e);
  }
  return { slides: [], assets: [], edges: [] };
}

