// ADK/A2A orchestrator client for presentation generation.

type Fetcher = typeof fetch;
import { resolveAdkBaseUrl } from '@/lib/base-url';

function baseUrl() {
  return resolveAdkBaseUrl();
}

async function withRetry<T>(fn: () => Promise<T>, attempts = 2, delayMs = 400): Promise<T> {
  let lastErr: any
  for (let i = 0; i <= attempts; i++) {
    try { return await fn() } catch (e) { lastErr = e }
    if (i < attempts) await new Promise(r => setTimeout(r, delayMs * (i + 1)))
  }
  throw lastErr
}

async function postJSON<T>(path: string, body: any, fetcher: Fetcher = fetch): Promise<T> {
  const call = () => fetcher(`${baseUrl()}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const res = await withRetry(call, 1, 500);
  if (!res.ok) {
    throw new Error(`Orchestrator error ${res.status}: ${await res.text()}`);
  }
  return (await res.json()) as T;
}

export async function orchClarify(input: any): Promise<{ refinedGoals: string; finished: boolean }> { return postJSON('/v1/clarify', input); }
export async function orchOutline(input: any): Promise<{ outline: string[] }> { return postJSON('/v1/outline', input); }
export async function orchWriteSlide(input: any): Promise<{ slides: any[] }> { return postJSON('/v1/slide/write', input); }
export async function orchCritiqueSlide(input: any): Promise<{ slide: any }> { return postJSON('/v1/slide/critique', input); }
export async function orchPolishNotes(input: any): Promise<{ rephrasedSpeakerNotes: string }> { return postJSON('/v1/slide/polish_notes', input); }
export async function orchDesignPrompt(input: any): Promise<{ type: 'prompt'|'code'; prompt?: string; code?: { css?: string; svg?: string }; usage?: any }> { return postJSON('/v1/slide/design', input); }
// New: full design generation (structured designSpec and variants)
export async function orchDesignGenerate(input: any): Promise<{ designSpec?: any; variants?: any[]; usage?: any }> { return postJSON('/v1/slide/design', input); }
export async function orchScript(input: any): Promise<{ script: string }> { return postJSON('/v1/script/generate', input); }
export async function orchIngest(input: any): Promise<{ ok: boolean }> { return postJSON('/v1/ingest', input); }
export async function orchRetrieve(input: any): Promise<{ chunks: { name: string; text: string; url?: string }[] }> { return postJSON('/v1/retrieve', input); }
export async function orchVisionAnalyze(input: { screenshotDataUrl: string }): Promise<{ mean: number; variance: number; recommendDarken: boolean; overlay: number }> { return postJSON('/v1/vision/analyze', input); }
export async function orchResearchBackgrounds(input: { textModel?: string; query?: string; topK?: number; allowDomains?: string[] }): Promise<{ rules: string[]; usage?: any }> { return postJSON('/v1/research/backgrounds', input); }

export async function orchSearchCacheConfig(input: { enabled?: boolean; cacheTtl?: number }): Promise<{ enabled: boolean; cacheTtl: number }> { return postJSON('/v1/search/cache/config', input); }
export async function orchSearchCacheClear(input: { deleteFile?: boolean; path?: string } = {}): Promise<{ ok: boolean }> { return postJSON('/v1/search/cache/clear', input); }

// Design validation/sanitization
export async function orchDesignValidate(input: { html?: string; css?: string; svg?: string }): Promise<{ ok: boolean; warnings?: string[]; errors?: string[] }> { return postJSON('/v1/design/validate', input); }
export async function orchDesignSanitize(input: { html?: string; css?: string; svg?: string }): Promise<{ html?: string; css?: string; svg?: string; warnings?: string[] }> { return postJSON('/v1/design/sanitize', input); }

// Helpers to attach models based on agent

// Reviews listing from Arango
export async function orchListReviews(presentationId: string, slideIndex: number, limit = 10): Promise<{ data?: { created_at?: string; agent_source?: string; review_data?: any }[]; success?: boolean; error?: string }> {
  const call = () => fetch(`${baseUrl()}/v1/arango/presentations/${encodeURIComponent(presentationId)}/slides/${slideIndex}/reviews?limit=${limit}`);
  const res = await withRetry(call, 1, 500);
  if (!res.ok) throw new Error(`Orchestrator error ${res.status}: ${await res.text()}`);
  return await res.json();
}
