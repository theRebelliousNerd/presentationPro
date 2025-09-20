'use server';

import { orchOutline, orchWriteSlide, orchPolishNotes, orchDesignPrompt, orchDesignGenerate, orchDesignValidate, orchDesignSanitize, orchScript, orchIngest, orchRetrieve, orchCritiqueSlide, orchWorkflowPresentation } from '@/lib/orchestrator';

import type { ChatMessage, Presentation, UploadedFileRef } from './types';
import type { AgentModels } from '@/lib/agent-models';
import { extractAssetsContext } from '@/lib/ingest';
import { resolveAdkBaseUrl } from '@/lib/base-url';
import { getServerAgentModels } from '@/lib/server-agent-models';

export interface WorkflowMetadata {
  workflowSessionId?: string;
  workflowState?: any;
  workflowTrace?: any[];
}

export interface RefinePresentationGoalsOutput extends WorkflowMetadata {
  clarifiedGoals: string;
  needsMoreClarification: boolean;
  response: string;
  refinedGoals: string;
  finished: boolean;
  initialInputPatch?: Partial<Presentation['initialInput']>;
  usage?: any;
}

export interface GenerateSlideContentInput {
  clarifiedContent?: string;
  outline: string[];
  audience?: string;
  tone?: string;
  length?: 'short' | 'medium' | 'long';
  assets?: UploadedFileRef[];
  textModel?: string;
  constraints?: any;
  existing?: { title: string; content: string[]; speakerNotes: string }[];
  presentationId?: string;
  sessionId?: string;
  workflowState?: any;
}

export type SlideGenerationResult = {
  title: string;
  content: string[];
  speakerNotes: string;
  imagePrompt: string;
  imageUrl?: string;
  useGeneratedImage?: boolean;
  design?: {
    tokens?: Record<string, string>;
    layers?: Array<{ kind?: string; token?: string; css?: string; columns?: number; gutter?: string; weights?: number[] }>;
    image?: { url?: string; prompt?: string; path?: string };
    type?: string;
    prompt?: string;
  };
  qualityMetrics?: {
    overall?: number;
    contrast?: { score: number; ratio?: number; passes: boolean; level?: 'AA' | 'AAA' | 'AA-large' };
    brand?: { score: number; violations?: string[]; passes: boolean };
    saliency?: { score: number; hotspots?: number; distribution?: 'concentrated' | 'balanced' | 'scattered' };
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
};
export type GenerateSlideContentOutput = SlideGenerationResult[]

async function currentAgentModels(): Promise<AgentModels> {
  return await getServerAgentModels();
}

async function attachAgentModel<K extends keyof AgentModels>(agent: K, payload: any) {
  const models = await currentAgentModels();
  const model = models[agent] || models.clarifier;
  if (payload && payload.textModel) return payload;
  return { ...payload, textModel: model };
}

async function attachSlideModels(payload: any) {
  const models = await currentAgentModels();
  return {
    ...payload,
    writerModel: payload?.writerModel || models.slideWriter,
    criticModel: payload?.criticModel || models.critic,
  };
}

interface WorkflowClarifyResult {
  finished: boolean;
  refinedGoals: string;
  initialInputPatch?: Partial<Presentation['initialInput']>;
  usage?: any;
}

function mapClarifyFromWorkflow(result: WorkflowRunResult): WorkflowClarifyResult {
  const clarifyFinal = (result.final as any)?.clarify ?? {};
  const clarifyState = (result.state as any)?.clarify ?? {};
  const finished = Boolean(clarifyFinal.finished ?? clarifyState.finished ?? false);
  const refinedGoals = clarifyFinal.refinedGoals ?? clarifyState.response ?? '';
  const initialInputPatch = clarifyFinal.initialInputPatch ?? clarifyState.initialInputPatch;
  const usage = clarifyFinal.usage ?? clarifyState.telemetry;
  return { finished, refinedGoals, initialInputPatch, usage };
}

function mapOutlineFromWorkflow(result: WorkflowRunResult): string[] {
  const outlineRaw = (result.state as any)?.outline?.raw ?? {};
  const outlineList: any[] = outlineRaw.outline ?? [];
  if (Array.isArray(outlineList) && outlineList.length > 0) {
    return outlineList.map((item: any) => (typeof item === 'string' ? item : item?.title || '')).filter(Boolean);
  }
  const outlineSections = (result.state as any)?.outline?.sections ?? [];
  if (Array.isArray(outlineSections) && outlineSections.length > 0) {
    return outlineSections.map((section: any) => section?.title || '').filter(Boolean);
  }
  return [];
}

function mapSlidesFromWorkflow(result: WorkflowRunResult): GenerateSlideContentOutput {
  const slides = (result.final as any)?.slides ?? (result.state as any)?.slides ?? [];
  if (!Array.isArray(slides) || slides.length === 0) return [];
  return slides.map((slide: any) => {
    const design = slide?.design || {};
    const designTokens = design && typeof design.tokens === 'object' ? design.tokens : undefined;
    const designLayers = Array.isArray(design?.layers) ? design.layers : undefined;
    const designImage = design && typeof design.image === 'object' ? design.image : undefined;
    const quality = slide?.quality_metrics || slide?.qualityMetrics;
    const ragSources = slide?.ragSources || slide?.metadata?.ragSources || [];
    const imageUrl = slide?.image_url || slide?.imageUrl || designImage?.url;
    const imagePrompt = slide?.image_prompt || slide?.imagePrompt || design?.prompt || '';

    const qualityMetrics = quality ? {
      overall: quality.overall_score ?? quality.overallScore,
      contrast: quality.accessibility_score != null ? {
        score: quality.accessibility_score,
        ratio: undefined,
        passes: (quality.accessibility_score ?? 0) >= 90,
        level: (quality.accessibility_score ?? 0) >= 95 ? 'AAA' : 'AA',
      } : undefined,
      brand: quality.brand_score != null ? {
        score: quality.brand_score,
        violations: quality.issues_found || [],
        passes: (quality.brand_score ?? 0) >= 85,
      } : undefined,
      saliency: quality.clarity_score != null ? {
        score: quality.clarity_score,
        hotspots: 0,
        distribution: (quality.clarity_score ?? 0) >= 90 ? 'balanced' : 'scattered',
      } : undefined,
    } : undefined;

    const qualityMeta = quality ? {
      overallScore: quality.overall_score,
      accessibilityScore: quality.accessibility_score,
      brandScore: quality.brand_score,
      clarityScore: quality.clarity_score,
      issuesFound: quality.issues_found,
      fixesApplied: quality.fixes_applied,
      requiresManualReview: quality.requires_manual_review,
      qualityLevel: quality.quality_level,
    } : undefined;

    const normalizedDesign = designTokens || designLayers || designImage || design?.type || design?.prompt
      ? {
          tokens: designTokens,
          layers: designLayers,
          image: designImage,
          type: design?.type,
          prompt: design?.prompt,
        }
      : undefined;

    return {
      title: slide?.title || 'Untitled slide',
      content: slide?.content || slide?.bullets || [],
      speakerNotes: slide?.speakerNotes || slide?.speaker_notes || '',
      imagePrompt,
      imageUrl,
      useGeneratedImage: !imageUrl,
      design: normalizedDesign,
      qualityMetrics,
      qualityMeta,
      ragSources,
    };
  });
}

export interface GetClarificationParams {
  history: ChatMessage[];
  initialInput: Presentation['initialInput'];
  newFiles?: UploadedFileRef[];
  presentationId?: string;
  sessionId?: string;
  workflowState?: any;
}

export async function getClarification({ history, initialInput, newFiles = [], presentationId, sessionId, workflowState }: GetClarificationParams): Promise<RefinePresentationGoalsOutput> {
  const workflow = await runPresentationWorkflow({
    history,
    initialInput,
    newFiles,
    presentationId,
    sessionId,
    state: workflowState,
  });
  const clarify = mapClarifyFromWorkflow(workflow);
  return {
    clarifiedGoals: clarify.refinedGoals,
    needsMoreClarification: !clarify.finished,
    response: clarify.refinedGoals,
    refinedGoals: clarify.refinedGoals,
    finished: clarify.finished,
    initialInputPatch: clarify.initialInputPatch,
    usage: clarify.usage,
    workflowSessionId: workflow.sessionId,
    workflowState: workflow.state,
    workflowTrace: workflow.trace,
  } as RefinePresentationGoalsOutput;
}

export async function getPresentationOutline(clarifiedGoals: string, opts: { presentationId?: string; length?: string; audience?: string; tone?: Presentation['initialInput']['tone']; template?: string; sessionId?: string; workflowState?: any } = {}): Promise<{ slideTitles: string[]; workflowSessionId?: string; workflowState?: any; workflowTrace?: any[] }> {
  const workflow = await runPresentationWorkflow({
    presentationId: opts.presentationId,
    history: [],
    initialInput: {
      text: clarifiedGoals,
      audience: opts.audience,
      tone: opts.tone as any,
      length: opts.length,
      template: opts.template,
    } as Presentation['initialInput'],
    newFiles: [],
    sessionId: opts.sessionId,
    state: opts.workflowState,
  });
  const titles = mapOutlineFromWorkflow(workflow);
  if (titles.length > 0) {
    return { slideTitles: titles, workflowSessionId: workflow.sessionId, workflowState: workflow.state, workflowTrace: workflow.trace } as any;
  }
  const tonePayload = opts.tone ? { formality: opts.tone.formality, energy: opts.tone.energy } : undefined;
  const payload = {
    clarifiedContent: clarifiedGoals,
    presentationId: opts.presentationId,
    length: opts.length,
    audience: opts.audience,
    tone: tonePayload,
    template: opts.template,
  };
  const res = await orchOutline(await attachAgentModel('outline', payload));
  return { slideTitles: res.outline, _usage: (res as any).usage, workflowSessionId: opts.sessionId, workflowState: opts.workflowState, workflowTrace: workflow.trace } as any;
}

export async function generateSlideContent(input: GenerateSlideContentInput): Promise<{ slides: GenerateSlideContentOutput; workflowSessionId?: string; workflowState?: any; workflowTrace?: any[] }> {
  const workflow = await runPresentationWorkflow({
    presentationId: input.presentationId,
    history: [],
    initialInput: {
      text: input.clarifiedContent || '',
      audience: input.audience,
      tone: input.tone as any,
      length: input.length,
    } as Presentation['initialInput'],
    newFiles: input.assets || [],
    sessionId: input.sessionId,
    state: input.workflowState,
  });
  const slides = mapSlidesFromWorkflow(workflow);
  if (slides.length > 0) {
    return { slides, workflowSessionId: workflow.sessionId, workflowState: workflow.state, workflowTrace: workflow.trace } as any;
  }
  const out = await orchWriteSlide(await attachSlideModels(input));
  return { slides: out.slides || [] } as any;
}

function clientBase(): string {
  return resolveAdkBaseUrl();
}

export async function generateImage(prompt: string, opts?: { baseImage?: string; imageModel?: string; slide?: { title?: string; content?: string[]; speakerNotes?: string }; theme?: 'brand'|'muted'|'dark'; pattern?: 'gradient'|'shapes'|'grid'|'dots'|'wave' }): Promise<{ imageUrl: string }> {
  const payload: any = {
    title: opts?.slide?.title || '',
    content: opts?.slide?.content || [],
    speakerNotes: opts?.slide?.speakerNotes || '',
    theme: opts?.theme || (typeof window !== 'undefined' ? (localStorage.getItem('app.theme') || 'brand') : 'brand'),
    pattern: opts?.pattern || (typeof window !== 'undefined' ? (localStorage.getItem('app.bgPattern') || 'gradient') : 'gradient'),
    prompt: prompt,
    baseImage: opts?.baseImage,
    imageModel: opts?.imageModel,
  };
  const res = await fetch(`${clientBase()}/v1/image/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Image generate failed: ${await res.text()}`);
  const data = await res.json();
  return { imageUrl: data.imageUrl };
}

export async function editImage(prompt: string, baseImage: string): Promise<{ imageUrl: string }> {
  const res = await fetch(`${clientBase()}/v1/image/edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instruction: prompt, baseImage }),
  });
  if (!res.ok) throw new Error(`Image edit failed: ${await res.text()}`);
  const data = await res.json();
  return { imageUrl: data.imageUrl };
}

export async function saveImageDataUrl(dataUrl: string): Promise<{ imageUrl: string }> {
  const res = await fetch(`${clientBase()}/v1/image/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataUrl }),
  })
  if (!res.ok) throw new Error(`Image save failed: ${await res.text()}`)
  const data = await res.json()
  return { imageUrl: data.imageUrl }
}

export async function rephraseNotes(speakerNotes: string, tone: 'professional' | 'concise'): Promise<{ rephrasedSpeakerNotes: string }> {
  return await orchPolishNotes(attachAgentModel('notesPolisher', { speakerNotes, tone }));
}

export async function generateFullScript(slides: { title: string; content?: string[]; speakerNotes?: string }[], assetsInput: UploadedFileRef[] = []): Promise<string> {
  const workflow = await runPresentationWorkflow({
    presentationId: undefined,
    history: [],
    initialInput: { text: '' } as Presentation['initialInput'],
    newFiles: assetsInput,
    assets: assetsInput,
  });
  const script = (workflow.final as any)?.script || workflow.state?.script;
  if (script) return script;
  const { script: generated } = await orchScript(attachAgentModel('scriptWriter', { slides, assets: assetsInput }));
  return generated;
}

export async function craftImagePrompt(slide: { title: string; content?: string[]; speakerNotes?: string }, opts?: { theme?: 'brand'|'muted'|'dark'; pattern?: 'gradient'|'shapes'|'grid'|'dots'|'wave'|'topography'|'hexagons'; screenshotDataUrl?: string; textModel?: string; preferCode?: boolean; iconPack?: 'lucide'|'tabler'|'heroicons' }): Promise<string | { type: 'code'; code: { css?: string; svg?: string } }> {
  const res = await orchDesignPrompt(attachAgentModel('design', { slide, ...opts }));
  if (res.type === 'code') return { type: 'code', code: res.code || {} };
  return res.prompt || '';
}

export async function craftDesign(slide: { title: string; content?: string[]; speakerNotes?: string }, opts?: { theme?: string; pattern?: string; textModel?: string; preferLayout?: boolean; variants?: number; preferCode?: boolean; iconPack?: string }): Promise<{ designSpec?: any; variants?: any[] }> {
  return await orchDesignGenerate(attachAgentModel('design', { slide, ...opts }))
}

export async function validateDesignCode(html?: string, css?: string, svg?: string): Promise<{ ok: boolean; warnings?: string[]; errors?: string[] }> {
  return await orchDesignValidate({ html, css, svg })
}

export async function sanitizeDesignCode(html?: string, css?: string, svg?: string): Promise<{ html?: string; css?: string; svg?: string; warnings?: string[] }> {
  return await orchDesignSanitize({ html, css, svg })
}

export async function critiqueSlide(
  slide: { title: string; content: string[]; speakerNotes?: string; imagePrompt?: string },
  opts?: { audience?: string; tone?: string; length?: 'short'|'medium'|'long'; assets?: UploadedFileRef[]; textModel?: string; presentationId?: string; slideIndex?: number }
): Promise<{ title: string; content: string[]; speakerNotes: string; _review?: { issues: string[]; suggestions: string[] } }> {
  try {
    const payload = attachAgentModel('critic', { slide, ...(opts || {}) });
    const res = await orchCritiqueSlide(payload);
    const out = (res && (res as any).slide) || slide;
    const review = (res as any).review as { issues: string[]; suggestions: string[] } | undefined;
    return { title: out.title || slide.title, content: out.content || slide.content, speakerNotes: out.speakerNotes || slide.speakerNotes || '', _review: review };
  } catch {
    return { title: slide.title, content: slide.content, speakerNotes: slide.speakerNotes || '' } as any;
  }
}

export async function ingestAssets(presentationId: string, assets: UploadedFileRef[]) {
  // Enrich with extracted text
  let enriched: any[] = [];
  try {
    enriched = await extractAssetsContext(assets);
  } catch {}
  const payload = {
    assets: (enriched.length ? enriched : assets).map((a: any) => ({
      presentationId,
      name: a.name,
      url: a.url,
      text: a.text,
      kind: a.kind,
    })),
  };
  return await orchIngest(payload);
}

export async function retrieveContext(presentationId: string, query: string, limit = 5): Promise<{ name: string; text: string }[]> {
  try {
    const { chunks } = await orchRetrieve({ presentationId, query, limit });
    return chunks;
  } catch {
    return [];
  }
}


export interface WorkflowRunResult {
  sessionId?: string;
  state: any;
  final?: any;
  trace: any[];
}

export async function runPresentationWorkflow(input: {
  history: ChatMessage[];
  initialInput: Presentation["initialInput"];
  newFiles?: UploadedFileRef[];
  assets?: UploadedFileRef[];
  presentationId?: string;
  sessionId?: string;
  state?: any;
}): Promise<WorkflowRunResult> {
  const payload: Record<string, any> = {
    presentationId: input.presentationId,
    history: input.history,
    initialInput: input.initialInput,
    newFiles: input.newFiles || [],
    assets: input.assets || [],
  };
  if (input.sessionId) payload.sessionId = input.sessionId;
  if (input.state) payload.state = input.state;
  const result = await orchWorkflowPresentation(payload);
  return {
    sessionId: result?.state?.metadata?.sessionId || result?.session_id || result?.sessionId,
    state: result?.state,
    final: result?.final,
    trace: result?.trace || [],
  };
}

