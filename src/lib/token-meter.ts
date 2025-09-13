// Simple token and cost tracker for client-side estimation
// Not exact — configure pricing via NEXT_PUBLIC_PRICE_* env vars.

export type UsageEntry = {
  model: 'gemini-2.5-flash' | 'gemini-2.5-flash-image-preview' | 'other';
  kind: 'prompt' | 'completion' | 'image_call';
  tokens?: number; // for text
  count?: number; // for image calls
  at: number;
};

type Totals = {
  tokensPrompt: number;
  tokensCompletion: number;
  imageCalls: number;
  usd: number;
};

const storeKey = 'tokenMeter.v1';

function readPricing() {
  const envPrompt = Number(process.env.NEXT_PUBLIC_PRICE_GEMINI_25_FLASH_PROMPT || '0');
  const envCompletion = Number(process.env.NEXT_PUBLIC_PRICE_GEMINI_25_FLASH_COMPLETION || '0');
  const envImage = Number(process.env.NEXT_PUBLIC_PRICE_GEMINI_25_FLASH_IMAGE_CALL || '0');
  if (typeof window === 'undefined') return { pricePrompt: envPrompt, priceCompletion: envCompletion, priceImageCall: envImage };
  try {
    const raw = localStorage.getItem('tokenMeter.pricing');
    if (raw) {
      const o = JSON.parse(raw) as Partial<{ pricePrompt: number; priceCompletion: number; priceImageCall: number }>;
      return {
        pricePrompt: o.pricePrompt ?? envPrompt,
        priceCompletion: o.priceCompletion ?? envCompletion,
        priceImageCall: o.priceImageCall ?? envImage,
      };
    }
  } catch {}
  return { pricePrompt: envPrompt, priceCompletion: envCompletion, priceImageCall: envImage };
}

let { pricePrompt, priceCompletion, priceImageCall } = readPricing();

export function setPricing(p: { pricePrompt?: number; priceCompletion?: number; priceImageCall?: number }) {
  try {
    const merged = { pricePrompt, priceCompletion, priceImageCall, ...p };
    localStorage.setItem('tokenMeter.pricing', JSON.stringify(merged));
    pricePrompt = merged.pricePrompt;
    priceCompletion = merged.priceCompletion;
    priceImageCall = merged.priceImageCall;
    subs.forEach(cb => cb());
  } catch {}
}

let subs = new Set<() => void>();

function load(): UsageEntry[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(storeKey);
    if (!raw) return [];
    return JSON.parse(raw) as UsageEntry[];
  } catch {
    return [];
  }
}

function save(entries: UsageEntry[]) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(storeKey, JSON.stringify(entries));
  } catch {}
}

export function estimateTokens(text: string): number {
  // rough heuristic ~4 chars per token
  const len = (text || '').length;
  return Math.max(1, Math.round(len / 4));
}

export function addUsage(entry: UsageEntry) {
  const list = load();
  list.push({ ...entry, at: Date.now() });
  save(list);
  subs.forEach(cb => cb());
}

export function resetUsage() {
  save([]);
  subs.forEach(cb => cb());
}

export function getTotals(): Totals {
  const list = load();
  let tokensPrompt = 0;
  let tokensCompletion = 0;
  let imageCalls = 0;
  for (const e of list) {
    if (e.kind === 'prompt') tokensPrompt += e.tokens || 0;
    if (e.kind === 'completion') tokensCompletion += e.tokens || 0;
    if (e.kind === 'image_call') imageCalls += e.count || 1;
  }
  // USD
  const usdText = (tokensPrompt / 1_000_000) * pricePrompt + (tokensCompletion / 1_000_000) * priceCompletion;
  const usdImage = imageCalls * priceImageCall;
  return {
    tokensPrompt,
    tokensCompletion,
    imageCalls,
    usd: Number((usdText + usdImage).toFixed(6)),
  };
}

export function subscribe(cb: () => void) {
  subs.add(cb);
  return () => { subs.delete(cb); };
}
