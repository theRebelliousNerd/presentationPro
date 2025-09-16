'use client';

import { Slide } from './types';
import JSZip from 'jszip';
import type PptxGenJS from 'pptxgenjs';

export function downloadScript(slides: Slide[]) {
  const scriptContent = slides
    .map((slide, index) => {
      return `--- Slide ${index + 1}: ${slide.title} ---\n\n${slide.speakerNotes}\n\n`;
    })
    .join('');

  const blob = new Blob([scriptContent], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'presentation-script.txt';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function downloadPresentationHtml(slides: Slide[]) {
  const html = `<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Presentation</title>
<style>
  body { font-family: Arial, sans-serif; margin: 0; }
  .slide { width: 1280px; height: 720px; margin: 24px auto; position: relative; overflow: hidden; border: 1px solid #ddd; border-radius: 8px; }
  .bg img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
  .content { position:absolute; inset:0; padding: 32px; }
  h2 { margin: 0 0 12px 0; }
  ul { margin: 8px 0 0 20px; }
</style>
</head>
<body>
${slides.map(s => {
  const imgTag = s.imageUrl ? `<div class="bg"><img src="${s.imageUrl}" alt=""/></div>` : '';
  const bullets = (s.content||[]).map(li => `<li>${escapeHtml(li)}</li>`).join('');
  return `<section class="slide">${imgTag}<div class="content"><h2>${escapeHtml(s.title)}</h2><ul>${bullets}</ul></div></section>`;
}).join('\n')}
</body>
</html>`;
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  triggerDownload(blob, 'presentation.html');
}

export async function exportServerHtml(presentation: { slides: Slide[]; id?: string; }): Promise<void> {
  const base = (process.env.NEXT_PUBLIC_ADK_BASE_URL || process.env.ADK_BASE_URL || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}${window.location.port==='3000'?':18088':(window.location.port?':'+window.location.port:'')}` : '')) as string
  try {
    const res = await fetch(`${base}/v1/export/html`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ title: presentation.id || 'Presentation', slides: presentation.slides || [] }) })
    if (!res.ok) throw new Error('Export failed')
    const js = await res.json()
    if (js && js.url) {
      window.open(js.url, '_blank')
    }
  } catch (e) {
    console.error('Server HTML export failed', e)
  }
}

export async function exportServerPdf(presentation: { slides: Slide[]; id?: string; }): Promise<void> {
  const base = (process.env.NEXT_PUBLIC_ADK_BASE_URL || process.env.ADK_BASE_URL || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}${window.location.port==='3000'?':18088':(window.location.port?':'+window.location.port:'')}` : '')) as string
  try {
    const res = await fetch(`${base}/v1/export/pdf`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ title: presentation.id || 'Presentation', slides: presentation.slides || [] }) })
    if (!res.ok) throw new Error('Export failed')
    const js = await res.json()
    if (js && js.url) {
      window.open(js.url, '_blank')
    }
  } catch (e) {
    console.error('Server PDF export failed', e)
  }
}

export async function downloadImages(slides: Slide[]) {
  const zip = new JSZip();
  const folder = zip.folder('images');
  if (folder) {
    for (let i = 0; i < slides.length; i++) {
      const s = slides[i];
      if (!s.imageUrl) continue;
      try {
        const res = await fetch(s.imageUrl);
        const buf = await res.arrayBuffer();
        const ext = guessExt(s.imageUrl);
        folder.file(`slide_${i + 1}${ext}`, buf);
      } catch {}
    }
  }
  const blob = await zip.generateAsync({ type: 'blob' });
  triggerDownload(blob, 'images.zip');
}

export async function downloadEverything(slides: Slide[]) {
  const zip = new JSZip();
  // script
  const scriptContent = slides.map((s, i) => `--- Slide ${i + 1}: ${s.title} ---\n\n${s.speakerNotes}\n\n`).join('');
  zip.file('script.txt', scriptContent);
  // html
  const htmlParts = [`<!doctype html><html><head><meta charset='utf-8'/><title>Presentation</title></head><body>`];
  slides.forEach((s) => {
    htmlParts.push(`<h2>${escapeHtml(s.title)}</h2>`);
    htmlParts.push(`<ul>${(s.content||[]).map(li => `<li>${escapeHtml(li)}</li>`).join('')}</ul>`);
  });
  htmlParts.push('</body></html>');
  zip.file('presentation.html', htmlParts.join(''));
  // images
  const imgFolder = zip.folder('images');
  if (imgFolder) {
    for (let i = 0; i < slides.length; i++) {
      const s = slides[i];
      if (!s.imageUrl) continue;
      try {
        const res = await fetch(s.imageUrl);
        const buf = await res.arrayBuffer();
        const ext = guessExt(s.imageUrl);
        imgFolder.file(`slide_${i + 1}${ext}`, buf);
      } catch {}
    }
  }
  const blob = await zip.generateAsync({ type: 'blob' });
  triggerDownload(blob, 'presentation_all.zip');
}

export async function downloadPptx(slides: Slide[]) {
  const mod = await import('pptxgenjs').catch(() => null);
  if (!mod) {
    console.error('pptxgenjs not installed');
    if (typeof window !== 'undefined') alert('PowerPoint export requires pptxgenjs. Run: npm i pptxgenjs and restart the dev server.');
    return;
    }
  const PptxGen = (mod as any).default as unknown as typeof PptxGenJS;
  const pptx = new (PptxGen as any)();
  pptx.defineLayout({ name: 'LAYOUT_16x9', width: 13.33, height: 7.5 });
  pptx.layout = 'LAYOUT_16x9';
  for (const s of slides) {
    const slide = pptx.addSlide();
    // Background image if present
    if (s.imageUrl) {
      try {
        const dataUrl = await toDataUrl(s.imageUrl);
        slide.addImage({ data: dataUrl, x: 0, y: 0, w: 13.33, h: 7.5 });
      } catch {}
    }
    // Title
    slide.addText(s.title || 'Slide', { x: 0.5, y: 0.4, w: 12.3, h: 1, fontSize: 28, bold: true, color: '003049' });
    // Bullets
    const bullets = (s.content || []).map(t => ({ text: t, options: { bullet: { type: 'number' }, fontSize: 18 } }));
    if (bullets.length) {
      slide.addText(bullets as any, { x: 0.8, y: 1.4, w: 11.5, h: 5.5 });
    }
  }
  await pptx.writeFile({ fileName: 'presentation.pptx' });
}

async function toDataUrl(url: string): Promise<string> {
  const res = await fetch(url);
  const blob = await res.blob();
  return await new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result as string);
    reader.readAsDataURL(blob);
  });
}

function guessExt(url: string) {
  const u = url.split('?')[0];
  const m = u.match(/\.(png|jpg|jpeg|webp|gif|svg)$/i);
  return m ? `.${m[1]}` : '.bin';
}

function escapeHtml(s: string) {
  return s.replace(/[&<>"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c] as string));
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
