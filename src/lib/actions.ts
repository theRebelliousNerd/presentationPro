'use server';

import { orchClarify, orchOutline, orchWriteSlide, orchPolishNotes, orchDesignPrompt, orchScript, orchIngest, orchRetrieve, withAgentModel, withSlideModels } from '@/lib/orchestrator';

import type { ChatMessage, Presentation, UploadedFileRef } from './types';
import { extractAssetsContext } from '@/lib/ingest';

export interface RefinePresentationGoalsOutput {
  clarifiedGoals: string;
  needsMoreClarification: boolean;
  response: string;
  refinedGoals: string;
  finished: boolean;
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
  newFiles: UploadedFileRef[] = []
): Promise<RefinePresentationGoalsOutput> {
  const result = await orchClarify(withAgentModel('clarifier', { history, initialInput, newFiles }));
  // Map orchestrator response to expected interface
  return {
    clarifiedGoals: result.refinedGoals,
    needsMoreClarification: !result.finished,
    response: result.refinedGoals,
    refinedGoals: result.refinedGoals,
    finished: result.finished
  };
}

export async function getPresentationOutline(clarifiedGoals: string): Promise<{ slideTitles: string[] }> {
  const res = await orchOutline(withAgentModel('outline', { clarifiedContent: clarifiedGoals }));
  return { slideTitles: res.outline, _usage: (res as any).usage } as any;
}

export async function generateSlideContent(input: GenerateSlideContentInput): Promise<GenerateSlideContentOutput> {
  const out = await orchWriteSlide(withSlideModels(input));
  return out.slides || [];
}

export async function generateImage(prompt: string, opts?: { baseImage?: string; imageModel?: string }): Promise<{ imageUrl: string }> {
  // This function would need to be implemented via ADK/orchestrator
  // For now, returning a placeholder
  throw new Error('Image generation not implemented in ADK mode');
}

export async function editImage(prompt: string, baseImage: string): Promise<{ imageUrl: string }> {
  // This function would need to be implemented via ADK/orchestrator
  // For now, returning a placeholder
  throw new Error('Image editing not implemented in ADK mode');
}

export async function rephraseNotes(speakerNotes: string, tone: 'professional' | 'concise'): Promise<{ rephrasedSpeakerNotes: string }> {
  return await orchPolishNotes(withAgentModel('notesPolisher', { speakerNotes, tone }));
}

export async function generateFullScript(slides: { title: string; content?: string[]; speakerNotes?: string }[], assetsInput: UploadedFileRef[] = []): Promise<string> {
  const { script } = await orchScript(withAgentModel('scriptWriter', { slides, assets: assetsInput }));
  return script;
}

export async function craftImagePrompt(slide: { title: string; content?: string[]; speakerNotes?: string }, opts?: { theme?: 'brand'|'muted'|'dark'; pattern?: 'gradient'|'shapes'|'grid'|'dots'|'wave'; screenshotDataUrl?: string; textModel?: string; preferCode?: boolean }): Promise<string | { type: 'code'; code: { css?: string; svg?: string } }> {
  const res = await orchDesignPrompt(withAgentModel('design', { slide, ...opts }));
  if (res.type === 'code') return { type: 'code', code: res.code || {} };
  return res.prompt || '';
}

export async function critiqueSlide(slide: { title: string; content: string[]; speakerNotes?: string; imagePrompt?: string }, opts?: { audience?: string; tone?: string; length?: 'short'|'medium'|'long'; assets?: UploadedFileRef[]; textModel?: string }): Promise<{ title: string; content: string[]; speakerNotes: string }> {
  // The ADK orchestrator handles the write/critic loop internally
  return { title: slide.title, content: slide.content, speakerNotes: slide.speakerNotes || '' };
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