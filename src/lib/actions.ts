'use server';

import { orchClarify, orchOutline, orchWriteSlide, orchPolishNotes, orchDesignPrompt, orchDesignGenerate, orchDesignValidate, orchDesignSanitize, orchScript, orchIngest, orchRetrieve, orchCritiqueSlide, withAgentModel, withSlideModels } from '@/lib/orchestrator';

import type { ChatMessage, Presentation, UploadedFileRef } from './types';
import { extractAssetsContext } from '@/lib/ingest';

export interface RefinePresentationGoalsOutput {
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
}

export type GenerateSlideContentOutput = {
  title: string;
  content: string[];
  speakerNotes: string;
  imagePrompt: string;
}[]

export async function getClarification(
  history: ChatMessage[],
  initialInput: Presentation['initialInput'],
  newFiles: UploadedFileRef[] = [],
  presentationId?: string,
): Promise<RefinePresentationGoalsOutput> {
  const result: any = await orchClarify(withAgentModel('clarifier', { history, initialInput, newFiles, presentationId }));
  // Map orchestrator response and pass through structured patches/usage when present
  return {
    clarifiedGoals: result.refinedGoals,
    needsMoreClarification: !result.finished,
    response: result.refinedGoals,
    refinedGoals: result.refinedGoals,
    finished: result.finished,
    initialInputPatch: result.initialInputPatch,
    usage: result.usage,
  } as RefinePresentationGoalsOutput;
}

export async function getPresentationOutline(clarifiedGoals: string): Promise<{ slideTitles: string[] }> {
  const res = await orchOutline(withAgentModel('outline', { clarifiedContent: clarifiedGoals }));
  return { slideTitles: res.outline, _usage: (res as any).usage } as any;
}

export async function generateSlideContent(input: GenerateSlideContentInput): Promise<GenerateSlideContentOutput> {
  const out = await orchWriteSlide(withSlideModels(input));
  return out.slides || [];
}

function clientBase(): string {
  if (typeof window !== 'undefined') {
    const env = process.env.NEXT_PUBLIC_ADK_BASE_URL;
    if (env && /^https?:\/\//.test(env)) return env;
    const { protocol, hostname, port } = window.location;
    return `${protocol}//${hostname}${port === '3000' ? ':18088' : (port ? ':'+port : '')}`;
  }
  return process.env.ADK_BASE_URL || '';
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
  return await orchPolishNotes(withAgentModel('notesPolisher', { speakerNotes, tone }));
}

export async function generateFullScript(slides: { title: string; content?: string[]; speakerNotes?: string }[], assetsInput: UploadedFileRef[] = []): Promise<string> {
  const { script } = await orchScript(withAgentModel('scriptWriter', { slides, assets: assetsInput }));
  return script;
}

export async function craftImagePrompt(slide: { title: string; content?: string[]; speakerNotes?: string }, opts?: { theme?: 'brand'|'muted'|'dark'; pattern?: 'gradient'|'shapes'|'grid'|'dots'|'wave'|'topography'|'hexagons'; screenshotDataUrl?: string; textModel?: string; preferCode?: boolean; iconPack?: 'lucide'|'tabler'|'heroicons' }): Promise<string | { type: 'code'; code: { css?: string; svg?: string } }> {
  const res = await orchDesignPrompt(withAgentModel('design', { slide, ...opts }));
  if (res.type === 'code') return { type: 'code', code: res.code || {} };
  return res.prompt || '';
}

export async function craftDesign(slide: { title: string; content?: string[]; speakerNotes?: string }, opts?: { theme?: string; pattern?: string; textModel?: string; preferLayout?: boolean; variants?: number; preferCode?: boolean; iconPack?: string }): Promise<{ designSpec?: any; variants?: any[] }> {
  return await orchDesignGenerate(withAgentModel('design', { slide, ...opts }))
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
    const payload = withAgentModel('critic', { slide, ...(opts || {}) });
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
