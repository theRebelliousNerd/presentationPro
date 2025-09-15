import { promises as fs } from 'fs';
import path from 'path';
import type { UploadedFileRef } from './types';

async function tryReadLocal(fileRef: UploadedFileRef): Promise<string | null> {
  const p = fileRef.path || (fileRef.url?.startsWith('/uploads') ? path.join(process.cwd(), 'public', fileRef.url) : undefined);
  if (!p) return null;
  try {
    const buf = await fs.readFile(p);
    return buf.toString('utf8');
  } catch {
    return null;
  }
}

async function tryFetchText(url: string): Promise<string | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const ct = res.headers.get('content-type') || '';
    if (!/text|json|csv|markdown|xml/i.test(ct)) return null;
    return await res.text();
  } catch {
    return null;
  }
}

export function inferKind(name: string): 'image' | 'document' | 'other' {
  if (/\.(png|jpe?g|gif|webp|svg)$/i.test(name)) return 'image';
  if (/\.(pdf|docx|md|markdown|txt|csv|xlsx?|json)$/i.test(name)) return 'document';
  return 'other';
}

export async function extractAssetsContext(files: UploadedFileRef[]): Promise<{
  name: string;
  url: string;
  kind: 'image' | 'document' | 'other';
  text?: string;
}[]> {
  const out: { name: string; url: string; kind: 'image'|'document'|'other'; text?: string }[] = [];
  for (const f of files) {
    const kind = f.kind || inferKind(f.name || '');
    const base = { name: f.name, url: f.url, kind } as { name: string; url: string; kind: 'image'|'document'|'other'; text?: string };
    if (kind === 'image') {
      // For images, provide a simple stub description using filename
      base.text = `Image asset “${f.name}”. Use as a background or supporting visual if it matches the slide topic.`;
      out.push(base);
      continue;
    }
    // Try local text read first
    let text: string | null = await tryReadLocal(f);
    if (!text) {
      // If local read fails, try fetch as text
      text = f.url ? await tryFetchText(f.url) : null;
    }
    if (!text && /\.pdf$/i.test(f.name)) {
      // Attempt PDF parse if available
      try {
        const { default: pdfParse } = await import('pdf-parse');
        const p = f.path || (f.url?.startsWith('/uploads') ? path.join(process.cwd(), 'public', f.url) : undefined);
        if (p) {
          const data = await fs.readFile(p);
          const parsed = await (pdfParse as any)(data);
          text = parsed?.text || '';
        }
      } catch {}
    }
    if (!text && /\.docx$/i.test(f.name)) {
      try {
        const { default: mammoth } = await import('mammoth');
        const p = f.path || (f.url?.startsWith('/uploads') ? path.join(process.cwd(), 'public', f.url) : undefined);
        if (p) {
          const buf = await fs.readFile(p);
          const result = await (mammoth as any).extractRawText({ buffer: buf });
          text = result?.value || '';
        }
      } catch {}
    }
    if (!text && /\.xlsx?$/i.test(f.name)) {
      try {
        const XLSX = await import('xlsx');
        const p = f.path || (f.url?.startsWith('/uploads') ? path.join(process.cwd(), 'public', f.url) : undefined);
        if (p) {
          const buf = await fs.readFile(p);
          const wb = XLSX.read(buf);
          const names = wb.SheetNames;
          const first = wb.Sheets[names[0]];
          const csv = XLSX.utils.sheet_to_csv(first);
          text = csv;
        }
      } catch {}
    }
    if (!text) {
      // Fallback minimal context
      text = `File uploaded: ${f.name}.`;
    }
    base.text = text.slice(0, 4000);
    out.push(base);
  }
  return out;
}

