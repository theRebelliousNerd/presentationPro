import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { resolveAdkBaseUrl } from '@/lib/base-url';

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const file = form.get('file');
    const presentationId = String(form.get('presentationId') || 'default');
    const category = String(form.get('category') || '').toLowerCase();

    if (!file || !(file instanceof Blob)) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 });
    }

    const originalName = (form.get('filename') as string) || (file as any).name || 'upload.bin';
    const safeName = originalName.replace(/[^\w\-.]+/g, '_');

    // Basic validation: size and allowed extensions
    // Optional override via env MAX_UPLOAD_MB (default 50MB)
    const maxMb = Number(process.env.MAX_UPLOAD_MB || 50);
    const MAX_SIZE_BYTES = Math.max(1, Math.floor(maxMb)) * 1024 * 1024;
    const size = (file as any).size ?? 0;
    if (size > MAX_SIZE_BYTES) {
      return NextResponse.json({ error: `File too large (max ${maxMb}MB)` }, { status: 413 });
    }
    const ext = (safeName.split('.').pop() || '').toLowerCase();
    const allowedExt = new Set(['pdf','docx','md','markdown','txt','csv','png','jpg','jpeg','webp','gif','svg']);
    if (!allowedExt.has(ext)) {
      return NextResponse.json({ error: `Unsupported file type .${ext}` }, { status: 400 });
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    const baseDir = path.join(process.cwd(), 'public', 'uploads', presentationId);
    let sub = '';
    if (category === 'content') sub = 'content';
    else if (category === 'style') sub = 'style';
    else if (category === 'graphics') sub = 'graphics';
    const uploadDir = sub ? path.join(baseDir, sub) : baseDir;
    const filePath = path.join(uploadDir, safeName);

    await fs.mkdir(uploadDir, { recursive: true });
    await fs.writeFile(filePath, buffer);

    const urlPath = `/uploads/${presentationId}/${sub ? sub + '/' : ''}${safeName}`;
    // Optionally register asset in Arango via api-gateway
    try {
      const base = resolveAdkBaseUrl()
      if (base && presentationId) {
        await fetch(`${base}/v1/arango/assets/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ presentationId, category: category || 'content', name: originalName, url: urlPath, path: `public${urlPath}` })
        }).catch(()=>{})
      }
    } catch {}

    return NextResponse.json({ name: originalName, url: urlPath, path: `public${urlPath}` });
  } catch (err: any) {
    console.error('Upload failed', err);
    return NextResponse.json({ error: 'Upload failed' }, { status: 500 });
  }
}
