'use client';

import { Slide } from './types';
import JSZip from 'jszip';

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
