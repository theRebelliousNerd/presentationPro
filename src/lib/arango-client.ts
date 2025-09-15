'use client';

/**
 * Frontend ArangoDB client that interfaces with the existing ADK backend infrastructure.
 * Leverages the EnhancedArangoClient schema and operations already built into the agents.
 */

import type { Presentation, AppState } from './types';

// Configuration from environment
const ADK_BASE_URL = process.env.NEXT_PUBLIC_ADK_BASE_URL || 'http://localhost:8089';
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
    version: number;
    agent_source: string;
    created_at: string;
    updated_at: string;
  }>;
}

class ArangoClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = ADK_BASE_URL;
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
    const operations = [];

    // Update presentation metadata
    operations.push({
      operation: 'update_metadata',
      data: {
        presentation_id: presentation.id,
        user_id: 'default', // TODO: Get from auth when implemented
        title: this.extractTitle(presentation),
        status: this.inferStatus(presentation),
      },
    });

    // Save clarifications (chat history)
    if (presentation.chatHistory && presentation.chatHistory.length > 0) {
      operations.push({
        operation: 'save_clarifications',
        data: {
          presentation_id: presentation.id,
          clarifications: presentation.chatHistory.map((msg, index) => ({
            sequence: index + 1,
            role: msg.role,
            content: msg.content,
          })),
        },
      });
    }

    // Save outline
    if (presentation.outline && presentation.outline.length > 0) {
      operations.push({
        operation: 'save_outline',
        data: {
          presentation_id: presentation.id,
          outline: presentation.outline.map(slide => slide.title),
        },
      });
    }

    // Save slides
    if (presentation.slides && presentation.slides.length > 0) {
      operations.push({
        operation: 'save_slides',
        data: {
          presentation_id: presentation.id,
          slides: presentation.slides.map((slide, index) => ({
            slide_index: index,
            title: slide.title,
            content: slide.content,
            speaker_notes: slide.speakerNotes || '',
            image_prompt: slide.imagePrompt || '',
          })),
        },
      });
    }

    // Save clarified goals
    if (presentation.clarifiedGoals) {
      operations.push({
        operation: 'save_goals',
        data: {
          presentation_id: presentation.id,
          clarified_goals: presentation.clarifiedGoals,
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

    // Convert clarifications to chat history
    if (state.clarifications) {
      presentation.chatHistory = state.clarifications
        .sort((a, b) => a.sequence - b.sequence)
        .map(clarification => ({
          role: clarification.role,
          content: clarification.content,
        }));
    }

    // Convert outline
    if (state.outline?.outline) {
      presentation.outline = state.outline.outline.map((title, index) => ({
        title,
        description: '',
      }));
    }

    // Convert slides
    if (state.slides) {
      presentation.slides = state.slides
        .sort((a, b) => a.slide_index - b.slide_index)
        .map(slide => ({
          title: slide.title,
          content: slide.content,
          speakerNotes: slide.speaker_notes,
          imagePrompt: slide.image_prompt,
        }));
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
      return presentation.outline[0].title;
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