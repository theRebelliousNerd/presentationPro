// Model pricing mapping and helpers
// Prices are USD per 1M tokens for prompt/completion, and per-call for image where applicable.
// Reference: https://ai.google.dev/gemini-api/docs/pricing (verify and update as needed)

export type ModelPricing = {
  promptPerM?: number
  completionPerM?: number
  imageCall?: number
}

function norm(model?: string): string {
  const m = (model || '').trim()
  return m.startsWith('googleai/') ? m.slice('googleai/'.length) : m
}

// Default mapping; override via NEXT_PUBLIC_MODEL_PRICING (JSON) if present
const DEFAULTS: Record<string, ModelPricing> = {
  'gemini-2.5-pro': { promptPerM: 3.5, completionPerM: 10 },
  'gemini-2.5-flash': { promptPerM: 0.8, completionPerM: 3 },
  'gemini-2.0-flash': { promptPerM: 0.6, completionPerM: 2.4 },
  'gemini-1.5-flash': { promptPerM: 0.35, completionPerM: 1.05 },
  'gemini-2.5-flash-image-preview': { imageCall: 0.002 },
}

let overrides: Record<string, ModelPricing> | null = null
export function getPricingForModel(model?: string): ModelPricing {
  try {
    if (overrides == null && typeof window !== 'undefined') {
      const raw = (window as any).NEXT_PUBLIC_MODEL_PRICING || process.env.NEXT_PUBLIC_MODEL_PRICING
      if (raw && typeof raw === 'string') overrides = JSON.parse(raw)
    }
  } catch {}
  const key = norm(model)
  const base = (overrides && overrides[key]) || DEFAULTS[key] || {}
  return { ...base }
}

