import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export async function POST(request: Request) {
  try {
    const form = await request.formData();
    const file = form.get('file');
    const presentationId = String(form.get('presentationId') || 'default');

    if (!file || !(file instanceof Blob)) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 });
    }

    const originalName = (form.get('filename') as string) || (file as any).name || 'upload.bin';
    const safeName = originalName.replace(/[^\w\-.]+/g, '_');

    const buffer = Buffer.from(await file.arrayBuffer());
    const uploadDir = path.join(process.cwd(), 'public', 'uploads', presentationId);
    const filePath = path.join(uploadDir, safeName);

    await fs.mkdir(uploadDir, { recursive: true });
    await fs.writeFile(filePath, buffer);

    const urlPath = `/uploads/${presentationId}/${safeName}`;
    return NextResponse.json({ name: originalName, url: urlPath, path: `public${urlPath}` });
  } catch (err: any) {
    console.error('Upload failed', err);
    return NextResponse.json({ error: 'Upload failed' }, { status: 500 });
  }
}

