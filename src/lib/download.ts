'use client';

import { Slide } from './types';

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
