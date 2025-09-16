export async function POST(req: Request): Promise<Response> {
  try {
    const { path, payload } = await req.json();
    if (!path || typeof path !== 'string' || !path.startsWith('/')) {
      return new Response(JSON.stringify({ error: 'Invalid path' }), { status: 400 });
    }
    const bases = candidateBases();
    let lastErr: any = null;
    for (const base of bases) {
      try {
        const url = `${base}${path}`;
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload || {}),
          cache: 'no-store',
        });
        const text = await res.text();
        return new Response(text, { status: res.status, headers: { 'Content-Type': 'application/json' } });
      } catch (e) {
        lastErr = e;
        continue;
      }
    }
    return new Response(JSON.stringify({ error: `fetch failed`, detail: String(lastErr) }), { status: 502 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: String(e?.message || e) }), { status: 500 });
  }
}

function candidateBases(): string[] {
  const bases: string[] = [];
  const internal = process.env.ADK_BASE_URL;
  if (internal && /^https?:\/\//.test(internal)) bases.push(internal);
  const pub = process.env.NEXT_PUBLIC_ADK_BASE_URL;
  if (pub && /^https?:\/\//.test(pub)) bases.push(pub);
  // Common fallbacks (in container and on host)
  bases.push('http://api-gateway:8088');
  bases.push('http://host.docker.internal:18088');
  bases.push('http://localhost:18088');
  // De-duplicate
  return Array.from(new Set(bases));
}
export const runtime = 'nodejs';
export async function GET(req: Request): Promise<Response> {
  try {
    const urlIn = new URL(req.url);
    const path = urlIn.searchParams.get('path');
    if (!path || !path.startsWith('/')) {
      return new Response(
        JSON.stringify({ ok: true, usage: 'POST { path: "/v1/visioncv/...", payload: {...} } or GET ?path=/v1/visioncv/tools' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }
    const bases = candidateBases();
    let lastErr: any = null;
    for (const base of bases) {
      try {
        const url = `${base}${path}`;
        const res = await fetch(url, { method: 'GET', cache: 'no-store' });
        const text = await res.text();
        return new Response(text, { status: res.status, headers: { 'Content-Type': 'application/json' } });
      } catch (e) {
        lastErr = e;
        continue;
      }
    }
    return new Response(JSON.stringify({ error: 'fetch failed', detail: String(lastErr) }), { status: 502 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: String(e?.message || e) }), { status: 500 });
  }
}
