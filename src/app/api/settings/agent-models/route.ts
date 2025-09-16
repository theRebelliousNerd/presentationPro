import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { AgentModels, DEFAULT_AGENT_MODELS, AGENT_MODELS_COOKIE } from '@/lib/agent-models';
import { serializeAgentModels, deserializeAgentModels } from '@/lib/server-agent-models';

const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

function sanitizeModels(input: unknown): AgentModels {
  const base: AgentModels = { ...DEFAULT_AGENT_MODELS };
  if (input && typeof input === 'object') {
    for (const key of Object.keys(base) as (keyof AgentModels)[]) {
      const candidate = (input as any)[key];
      if (typeof candidate === 'string' && candidate.trim().length > 0) {
        base[key] = candidate.trim();
      }
    }
  }
  return base;
}

export async function POST(req: Request): Promise<NextResponse> {
  try {
    const body = await req.json().catch(() => ({}));
    const sanitized = sanitizeModels(body?.models ?? body);
    const res = NextResponse.json({ ok: true, models: sanitized });
    res.cookies.set({
      name: AGENT_MODELS_COOKIE,
      value: serializeAgentModels(sanitized),
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      maxAge: COOKIE_MAX_AGE,
    });
    return res;
  } catch (error: any) {
    return NextResponse.json({ ok: false, error: String(error?.message || error) }, { status: 500 });
  }
}

export async function GET(): Promise<NextResponse> {
  try {
    const store = cookies();
    const entry = store.get(AGENT_MODELS_COOKIE);
    const parsed = deserializeAgentModels(entry?.value) || DEFAULT_AGENT_MODELS;
    return NextResponse.json({ ok: true, models: parsed });
  } catch (error: any) {
    return NextResponse.json({ ok: false, error: String(error?.message || error) }, { status: 500 });
  }
}
