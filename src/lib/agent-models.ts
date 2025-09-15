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

const defaultModels: AgentModels = {
  clarifier: 'googleai/gemini-2.5-flash',
  outline: 'googleai/gemini-2.5-flash',
  slideWriter: 'googleai/gemini-2.5-flash',
  critic: 'googleai/gemini-2.5-flash',
  notesPolisher: 'googleai/gemini-2.5-flash',
  design: 'googleai/gemini-2.5-flash',
  scriptWriter: 'googleai/gemini-2.5-flash',
  research: 'googleai/gemini-2.5-flash',
}

const LS_KEY = 'agentModels.v1'

export function getAgentModels(): AgentModels {
  if (typeof window === 'undefined') return defaultModels
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return defaultModels
    const data = JSON.parse(raw)
    return { ...defaultModels, ...(data || {}) }
  } catch {
    return defaultModels
  }
}

export function setAgentModels(next: Partial<AgentModels>) {
  if (typeof window === 'undefined') return
  try {
    const merged = { ...getAgentModels(), ...next }
    localStorage.setItem(LS_KEY, JSON.stringify(merged))
  } catch {}
}

