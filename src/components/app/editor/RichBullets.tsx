'use client';
import { useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';

export default function RichBullets({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const html = value.map(li => `<li>${escapeHtml(li)}</li>`).join('');
    ref.current.innerHTML = `<ul>${html}</ul>`;
  }, []);
  const apply = () => {
    if (!ref.current) return;
    const lis = Array.from(ref.current.querySelectorAll('li')) as HTMLLIElement[];
    const lines = lis.map(li => li.innerText.trim()).filter(Boolean);
    onChange(lines);
  };
  return (
    <div className="border rounded">
      <div className="flex gap-2 p-2 border-b bg-muted/30">
        <Button type="button" size="sm" variant="outline" onClick={() => document.execCommand('bold')}>B</Button>
        <Button type="button" size="sm" variant="outline" onClick={() => document.execCommand('italic')}>I</Button>
        <Button type="button" size="sm" variant="outline" onClick={() => document.execCommand('underline')}>U</Button>
        <Button type="button" size="sm" variant="outline" onClick={() => { if(!ref.current) return; document.execCommand('insertUnorderedList'); }}>• List</Button>
        <Button type="button" size="sm" onClick={apply}>Apply</Button>
      </div>
      <div ref={ref} contentEditable className="min-h-[120px] p-3 outline-none" onBlur={apply} />
    </div>
  );
}

function escapeHtml(s: string) {
  return s.replace(/[&<>"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c] as string));
}

