// Agent-specific model configuration with localStorage persistence

export type AgentModels = {
  clarifier: string
  outline: string
  slideWriter: string
  critic: string
  notesPolisher: string
  design: string
  scriptWriter: string
  research: string
}

export const DEFAULT_AGENT_MODELS: AgentModels = {
  clarifier: 'googleai/gemini-2.5-flash',
  outline: 'googleai/gemini-2.5-flash',
  slideWriter: 'googleai/gemini-2.5-flash',
  critic: 'googleai/gemini-2.5-flash',
  notesPolisher: 'googleai/gemini-2.5-flash',
  design: 'googleai/gemini-2.5-flash',
  scriptWriter: 'googleai/gemini-2.5-flash',
  research: 'googleai/gemini-2.5-flash',
}

export const AGENT_MODELS_COOKIE = 'agentModels';
const LS_KEY = 'agentModels.v1';

export function getAgentModels(): AgentModels {
  if (typeof window === 'undefined') return DEFAULT_AGENT_MODELS
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return DEFAULT_AGENT_MODELS
    const data = JSON.parse(raw)
    return { ...DEFAULT_AGENT_MODELS, ...(data || {}) }
  } catch {
    return DEFAULT_AGENT_MODELS
  }
}

export function setAgentModels(next: Partial<AgentModels>) {
  if (typeof window === 'undefined') return
  try {
    const merged = { ...getAgentModels(), ...next }
    localStorage.setItem(LS_KEY, JSON.stringify(merged))
    void fetch('/api/settings/agent-models', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ models: merged }),
      credentials: 'include',
    }).catch(() => {})
  } catch {}
}

