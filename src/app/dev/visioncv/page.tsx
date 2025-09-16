"use client";
import { useEffect, useRef, useState } from "react";

const defaultTools = [
  { name: "critic.color_contrast", path: "/v1/vision/analyze", sample: { screenshotDataUrl: "data:image/png;base64,..." } },
  { name: "critic.assess_blur", path: "/v1/visioncv/blur", sample: { screenshotDataUrl: "data:image/png;base64,..." } },
  { name: "critic.measure_noise", path: "/v1/visioncv/noise", sample: { screenshotDataUrl: "data:image/png;base64,..." } },
  { name: "critic.check_color_contrast_ratio", path: "/v1/visioncv/contrast_ratio", sample: { fg: "#192940", bg: "#FFFFFF", level: "AA", fontSizePx: 18 } },
  { name: "design.saliency_spectral", path: "/v1/visioncv/saliency", sample: { screenshotDataUrl: "data:image/png;base64,..." } },
  { name: "design.find_empty_regions", path: "/v1/visioncv/empty_regions", sample: { screenshotDataUrl: "data:image/png;base64,..." } },
  { name: "design.extract_palette", path: "/v1/visioncv/palette", sample: { imageDataUrl: "data:image/png;base64,...", colors: 6 } },
  { name: "design.suggest_placement", path: "/v1/visioncv/placement", sample: { screenshotDataUrl: "data:image/png;base64,..." } },
  { name: "design.generate_procedural_texture", path: "/v1/visioncv/procedural_texture", sample: { width: 1024, height: 576, texture_type: "perlin_noise", parameters: { noise_scale: 6, turbulence: 0.5, color_palette_hex: ["#192940", "#73BF50", "#556273"] } } },
  { name: "research.ocr_extract", path: "/v1/visioncv/ocr", sample: { imageDataUrl: "data:image/png;base64,..." } },
  { name: "brand.detect_logo", path: "/v1/visioncv/logo", sample: { target_image_b64: "", reference_logo_b64: "" } },
  { name: "brand.validate_brand_colors", path: "/v1/visioncv/brand_colors", sample: { imageDataUrl: "data:image/png;base64,...", brandPalette: ["#192940","#73BF50","#556273"] } },
  { name: "research.extract_data_from_bar_chart", path: "/v1/visioncv/bar_chart", sample: { imageDataUrl: "data:image/png;base64,..." } },
  { name: "research.extract_data_from_line_graph", path: "/v1/visioncv/line_graph", sample: { imageDataUrl: "data:image/png;base64,..." } },
];

function apiBase(): string {
  // Prefer browser mapping; avoid container-only hostnames like 'api-gateway'
  if (typeof window !== 'undefined') {
    const env = process.env.NEXT_PUBLIC_ADK_BASE_URL as string | undefined;
    if (env && /^https?:\/\//.test(env) && !/api-gateway/i.test(env)) return env;
    const { protocol, hostname, port } = window.location;
    // Map common cases to gateway port 18088 (external mapping of api-gateway:8088)
    if (port === '3000' || port === '' || port === '80' || port === '443') {
      return `${protocol}//${hostname}:18088`;
    }
    return `${protocol}//${hostname}${port ? ':' + port : ''}`;
  }
  return process.env.ADK_BASE_URL || '';
}

export default function VisionCVDev() {
  const [toolList, setToolList] = useState(defaultTools);
  const [tool, setTool] = useState(defaultTools[0]);
  const [body, setBody] = useState(JSON.stringify(defaultTools[0].sample, null, 2));
  const [result, setResult] = useState("{}");
  const [busy, setBusy] = useState(false);
  const base = apiBase();
  const [dragActive, setDragActive] = useState(false);
  const [primaryPreview, setPrimaryPreview] = useState<string | null>(null);
  const [secondaryPreview, setSecondaryPreview] = useState<string | null>(null);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const sample = (tool as any)?.sample as Record<string, any> | undefined;
  const expectsPrimaryImage = !!(sample && (sample.screenshotDataUrl !== undefined || sample.imageDataUrl !== undefined || sample.target_image_b64 !== undefined));
  const expectsSecondaryImage = tool.name.includes('detect_logo');

  const extractImageFromResponse = (data: any): string | null => {
    if (!data || typeof data !== 'object') return null;
    const candidates = [
      data.imageDataUrl,
      data.image_url,
      data.image,
      data.image_b64,
      data.imageB64,
    ];
    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.length > 10) {
        if (candidate.startsWith('data:')) return candidate;
        return `data:image/png;base64,${candidate}`;
      }
    }
    return null;
  };

  const call = async () => {
    setBusy(true);
    setGeneratedImage(null);
    try {
      // Use server-side proxy to avoid client->gateway cross-origin issues
      let parsed: any = {};
      try { parsed = JSON.parse(body) } catch (e) { setResult(JSON.stringify({ error: 'Invalid JSON body' }, null, 2)); setBusy(false); return; }
      const res = await fetch('/api/dev/visioncv/proxy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: tool.path, payload: parsed }) });
      const data = await res.json();
      setResult(JSON.stringify(data, null, 2));
      const preview = extractImageFromResponse(data);
      if (preview) setGeneratedImage(preview);
    } catch (e: any) {
      setResult(JSON.stringify({ error: String(e) }, null, 2));
    }
    setBusy(false);
  };

  // Optional: try to fetch live tool list and merge with defaults
  useEffect(() => {
    const run = async () => {
      try {
        const res = await fetch(`/api/dev/visioncv/proxy?path=/v1/visioncv/tools`, { cache: 'no-store' });
        const data = await res.json().catch(()=>null);
        const toolsFromServer: Array<{ name: string }>|null = data?.tools || null;
        if (Array.isArray(toolsFromServer)) {
          // Map known tool names to proxy paths (fallback to defaults)
          const byName = new Map(defaultTools.map(t=>[t.name, t] as const));
          const merged = toolsFromServer.map(t => byName.get(t.name)).filter(Boolean) as typeof defaultTools;
          if (merged.length) {
            setToolList(merged);
            // If current tool isn't in the merged list, reset
            if (!merged.find(x=>x.name===tool.name)) {
              setTool(merged[0]);
              setBody(JSON.stringify(merged[0].sample, null, 2));
            }
          }
        }
      } catch {}
    };
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateBodyWithPrimary = (dataUrl: string) => {
    setBody(prev => {
      try {
        const obj = JSON.parse(prev || '{}');
        const name = tool.name;
        if (name.includes('contrast_ratio') || name.includes('procedural_texture')) {
          return prev;
        }
        if (name.includes('ocr') || name.includes('bar_chart') || name.includes('line_graph') || name.includes('brand_colors') || name.includes('extract_palette')) {
          obj.imageDataUrl = dataUrl;
        } else if (name.includes('detect_logo')) {
          obj.target_image_b64 = dataUrl;
        } else {
          obj.screenshotDataUrl = dataUrl;
        }
        return JSON.stringify(obj, null, 2);
      } catch {
        return prev;
      }
    });
  };

  const updateBodyWithSecondary = (dataUrl: string) => {
    setBody(prev => {
      try {
        const obj = JSON.parse(prev || '{}');
        obj.reference_logo_b64 = dataUrl;
        return JSON.stringify(obj, null, 2);
      } catch {
        return prev;
      }
    });
  };

  const clearSecondaryImage = () => {
    setSecondaryPreview(null);
    if (!tool.name.includes('detect_logo')) return;
    setBody(prev => {
      try {
        const obj = JSON.parse(prev || '{}');
        obj.reference_logo_b64 = '';
        return JSON.stringify(obj, null, 2);
      } catch {
        return prev;
      }
    });
  };

  const onDropFiles = async (files: FileList | File[]) => {
    if (tool.name.includes('contrast_ratio') || tool.name.includes('procedural_texture')) {
      return;
    }
    const imgs = Array.from(files).filter(f => f.type.startsWith('image/'));
    if (imgs.length === 0) return;
    const primary = imgs[0];
    const pUrl = await fileToDataURL(primary);
    setPrimaryPreview(pUrl);
    updateBodyWithPrimary(pUrl);

    if (tool.name.includes('detect_logo')) {
      if (imgs.length > 1) {
        const secondary = imgs[1];
        const sUrl = await fileToDataURL(secondary);
        setSecondaryPreview(sUrl);
        updateBodyWithSecondary(sUrl);
      } else {
        clearSecondaryImage();
      }
    } else {
      clearSecondaryImage();
    }
  };

  const downloadJSON = (filename: string, text: string) => {
    const blob = new Blob([text], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">VisionCV Dev Panel</h1>
      <div className="flex gap-2 items-center">
        <label className="text-sm">Tool:</label>
        <select className="border rounded px-2 py-1" value={tool.name} onChange={(e)=>{
          const t = toolList.find(x=>x.name===e.target.value) || defaultTools.find(x=>x.name===e.target.value)!;
          setTool(t);
          setBody(JSON.stringify(t.sample, null, 2));
          setPrimaryPreview(null);
          setSecondaryPreview(null);
          setGeneratedImage(null);
        }}>
          {toolList.map(t=> <option key={t.name} value={t.name}>{t.name}</option>)}
        </select>
        <button className="border rounded px-3 py-1 bg-blue-600 text-white disabled:opacity-50" onClick={call} disabled={busy}>Call</button>
      </div>
      <div className="text-xs text-muted-foreground">Base: {base}</div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          {expectsPrimaryImage ? (
            <div
              className={
                `flex flex-col items-center justify-center border-2 border-dashed rounded-md p-6 cursor-pointer select-none `+
                (dragActive ? 'border-blue-500 bg-blue-50' : 'border-muted-foreground/30 hover:border-blue-400')
              }
              onDragOver={(e)=>{ e.preventDefault(); setDragActive(true); }}
              onDragLeave={()=> setDragActive(false)}
              onDrop={async (e)=>{ e.preventDefault(); setDragActive(false); if(e.dataTransfer?.files){ await onDropFiles(e.dataTransfer.files); } }}
              onClick={()=> fileInputRef.current?.click()}
              aria-label="Drop images here or click to select"
            >
              <div className="text-sm font-medium mb-1">Drag & drop images here</div>
              <div className="text-xs text-muted-foreground mb-2">Primary screenshot required{expectsSecondaryImage ? ", optional second image for logo reference" : ''}.</div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple={expectsSecondaryImage}
                className="hidden"
                onChange={async (e)=>{ if(e.target.files){ await onDropFiles(e.target.files); e.currentTarget.value=''; } }}
              />
              <div className="grid grid-cols-2 gap-3 w-full mt-2">
                <div className="flex flex-col items-center gap-2">
                  <div className="text-xs">Primary</div>
                  {primaryPreview ? (
                    <img src={primaryPreview} alt="Primary preview" className="max-h-40 rounded border" />
                  ) : (
                    <div className="h-40 w-full border rounded bg-muted/30 flex items-center justify-center text-xs text-muted-foreground">No image</div>
                  )}
                </div>
                {expectsSecondaryImage && (
                  <div className="flex flex-col items-center gap-2">
                    <div className="text-xs">Logo ref</div>
                    {secondaryPreview ? (
                      <img src={secondaryPreview} alt="Secondary preview" className="max-h-40 rounded border" />
                    ) : (
                      <div className="h-40 w-full border rounded bg-muted/30 flex items-center justify-center text-xs text-muted-foreground">Optional</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-2 border border-dashed border-muted-foreground/30 rounded-md p-6 bg-muted/20">
              <div className="text-sm font-medium">No image upload needed</div>
              <p className="text-xs text-muted-foreground text-center">
                This tool is driven entirely by the JSON parameters below. Adjust them and click Call to test responses.
              </p>
            </div>
          )}
          <div className="mt-3 flex gap-2">
            <button
              className="border rounded px-2 py-1 text-xs"
              onClick={(e)=>{ e.stopPropagation(); setPrimaryPreview(null); clearSecondaryImage(); setGeneratedImage(null); setBody(JSON.stringify(tool.sample, null, 2)); }}
            >Reset</button>
            {result && result !== '{}' && (
              <button
                className="border rounded px-2 py-1 text-xs"
                onClick={(e)=>{ e.stopPropagation(); downloadJSON('visioncv-response.json', result); }}
              >Download JSON</button>
            )}
          </div>

          {tool.name==='brand.validate_brand_colors' ? (
            <div className="mt-3 text-xs">Brand Palette (comma):
              <input
                className="border rounded px-2 py-1 ml-2"
                onChange={(e)=>{
                  try{ const obj=JSON.parse(body||'{}'); obj.brandPalette=(e.target.value||'').split(',').map(s=>s.trim()).filter(Boolean); setBody(JSON.stringify(obj,null,2)); }catch{}
                }}
                placeholder="#192940,#73BF50,#556273"
              />
            </div>
          ) : null}

          <div className="mt-4">
            <div className="text-sm mb-1">Request JSON</div>
            <textarea className="w-full h-64 border rounded p-2 font-mono text-xs" value={body} onChange={(e)=>setBody(e.target.value)} />
          </div>
        </div>

        <div>
          <div className="text-sm mb-1">Response</div>
          {generatedImage ? (
            <div className="mb-3">
              <div className="text-xs text-muted-foreground mb-1">Image preview (from response)</div>
              <img src={generatedImage} alt="Generated output" className="max-h-64 rounded border" />
            </div>
          ) : null}
          <textarea className="w-full h-[28rem] border rounded p-2 font-mono text-xs" value={result} readOnly />
        </div>
      </div>
      <p className="text-xs text-muted-foreground">Note: These routes call the API gateway proxies and require VisionCV to be running in Docker compose.</p>
    </div>
  );
}

function fileToDataURL(f: File): Promise<string> {
  return new Promise((resolve, reject)=>{
    const r = new FileReader(); r.onload = ()=> resolve(String(r.result)); r.onerror = reject; r.readAsDataURL(f);
  })
}
