'use server';

import { Buffer } from 'node:buffer';
import { cookies } from 'next/headers';
import { AgentModels, DEFAULT_AGENT_MODELS, AGENT_MODELS_COOKIE } from '@/lib/agent-models';

function decodeModels(raw?: string | null): AgentModels | null {
  if (!raw) return null;
  try {
    const json = Buffer.from(raw, 'base64').toString('utf-8');
    const data = JSON.parse(json);
    if (!data || typeof data !== 'object') return null;
    const merged = { ...DEFAULT_AGENT_MODELS } as AgentModels;
    for (const key of Object.keys(merged) as (keyof AgentModels)[]) {
      const value = (data as any)[key];
      if (typeof value === 'string' && value.trim().length) {
        merged[key] = value;
      }
    }
    return merged;
  } catch {
    return null;
  }
}

export async function getServerAgentModels(): Promise<AgentModels> {
  try {
    const store = await cookies();
    const entry = store.get(AGENT_MODELS_COOKIE);
    const parsed = decodeModels(entry?.value);
    if (parsed) return parsed;
  } catch {}
  return DEFAULT_AGENT_MODELS;
}

export async function serializeAgentModels(models: AgentModels): Promise<string> {
  return Buffer.from(JSON.stringify(models), 'utf-8').toString('base64');
}

export async function deserializeAgentModels(raw: string | null | undefined): Promise<AgentModels | null> {
  return decodeModels(raw);
}
