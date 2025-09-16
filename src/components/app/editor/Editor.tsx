'use client';
import { useState, useEffect, useRef, Dispatch, SetStateAction } from 'react';
import { Slide, Presentation } from '@/lib/types';
import SlideSidebar from './SlideSidebar';
import SlideEditor from './SlideEditor';
import { nanoid } from 'nanoid';
import { downloadScript } from '@/lib/download';
import { Button } from '@/components/ui/button';
import { Download, Upload, ExternalLink, Trash2, FileImage, FileText } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import ClarificationChat from '@/components/app/ClarificationChat';
// Downloads moved to TopBarCompact
import { Textarea } from '@/components/ui/textarea';
import { generateFullScript } from '@/lib/actions';
import ProjectLogs from './ProjectLogs';

type EditorProps = {
  slides: Slide[];
  setSlides: Dispatch<SetStateAction<Slide[]>> | ((slides: Slide[]) => void);
  presentation?: Presentation;
  setPresentation?: Dispatch<SetStateAction<Presentation>>;
  uploadFile?: (file: File) => Promise<{ name: string; url: string; path?: string }>;
  onActiveSlideChange?: (index: number) => void;
};

export default function Editor({ slides, setSlides, presentation, setPresentation, uploadFile, onActiveSlideChange }: EditorProps) {
  const [activeSlideId, setActiveSlideId] = useState<string | null>(slides[0]?.id || null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [sidebarWidth, setSidebarWidth] = useState<number>(256);
  const resizingRef = useRef<boolean>(false);

  const activeSlide = slides.find(s => s.id === activeSlideId);
  const activeSlideIndex = slides.findIndex(s => s.id === activeSlideId);

  const updateSlide = (slideId: string, updatedProps: Partial<Slide>) => {
    const newSlides = slides.map(s => s.id === slideId ? { ...s, ...updatedProps } : s);
    setSlides(newSlides);
  };

  const applyTokensToAll = (tokens: any) => {
    const newSlides = slides.map(s => {
      const ds = s.designSpec || {}
      const mergedTokens = { ...(ds.tokens || {}), ...(tokens || {}) }
      return { ...s, designSpec: { ...ds, tokens: mergedTokens } }
    })
    setSlides(newSlides)
  }
  
  const addSlide = () => {
    const newSlide: Slide = {
      id: nanoid(),
      title: 'New Slide',
      content: ['- '],
      speakerNotes: '',
      imagePrompt: 'A simple, abstract background with soft gradients and geometric shapes, in a professional and minimalist style.',
      imageState: 'loading',
    };
    const newIndex = activeSlideIndex + 1;
    const newSlides = [...slides.slice(0, newIndex), newSlide, ...slides.slice(newIndex)];
    setSlides(newSlides);
    setActiveSlideId(newSlide.id);
    if (onActiveSlideChange) onActiveSlideChange(newIndex);
  };

  const deleteSlide = (slideId: string) => {
    if (slides.length <= 1) return;
    const slideIndex = slides.findIndex(s => s.id === slideId);
    const newSlides = slides.filter(s => s.id !== slideId);
    setSlides(newSlides);

    if (activeSlideId === slideId) {
      const newActiveIndex = Math.max(0, slideIndex - 1);
      setActiveSlideId(newSlides[newActiveIndex]?.id || null);
      if (onActiveSlideChange) onActiveSlideChange(newActiveIndex);
    }
  };

  // Notify parent on selection changes
  useEffect(() => {
    if (onActiveSlideChange && activeSlideIndex >= 0) onActiveSlideChange(activeSlideIndex)
  }, [activeSlideIndex, onActiveSlideChange])

  // Global toggle from left rail
  useEffect(() => {
    const onToggle = () => setSidebarCollapsed(prev => !prev)
    window.addEventListener('slides:toggle', onToggle as any)
    return () => window.removeEventListener('slides:toggle', onToggle as any)
  }, [])

  // Broadcast collapsed state for left rail icon state
  useEffect(() => {
    try { window.dispatchEvent(new CustomEvent('slides:state', { detail: { collapsed: sidebarCollapsed } })) } catch {}
  }, [sidebarCollapsed])

  // Load/save sidebar width
  useEffect(() => {
    try {
      const saved = localStorage.getItem('slides.sidebarWidth')
      if (saved) {
        const n = parseInt(saved, 10)
        if (!Number.isNaN(n) && n >= 180 && n <= 600) setSidebarWidth(n)
      }
    } catch {}
  }, [])
  useEffect(() => {
    try { localStorage.setItem('slides.sidebarWidth', String(sidebarWidth)) } catch {}
  }, [sidebarWidth])

  // Resizer handlers
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!resizingRef.current || !containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      let w = e.clientX - rect.left
      const min = 180, max = 600
      if (w < min) w = min
      if (w > max) w = max
      setSidebarWidth(w)
    }
    const onUp = () => { resizingRef.current = false }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [])

  return (
    <div ref={containerRef} className="w-full h-[calc(100vh-120px)] flex gap-0">
      {!sidebarCollapsed ? (
        <SlideSidebar
          style={{ width: sidebarWidth }}
          slides={slides}
          activeSlideId={activeSlideId}
          setActiveSlideId={(id)=>{ setActiveSlideId(id); const idx = slides.findIndex(s=>s.id===id); if (onActiveSlideChange && idx>=0) onActiveSlideChange(idx) }}
          addSlide={addSlide}
          deleteSlide={deleteSlide}
          setSlides={setSlides}
        />
      ) : null}
      {!sidebarCollapsed ? (
        <div
          role="separator"
          aria-orientation="vertical"
          className="w-[6px] cursor-col-resize hover:bg-muted/70 active:bg-muted/90"
          onMouseDown={() => { resizingRef.current = true }}
        />
      ) : null}
      <main className="flex-grow h-full flex flex-col">
        {/* Sidebar toggle */}
        <div className="flex items-center gap-2 mb-2">
          <button className="text-xs px-2 py-1 border rounded" onClick={()=> setSidebarCollapsed(prev => !prev)}>
            {sidebarCollapsed ? 'Show Slides' : 'Hide Slides'}
          </button>
        </div>
        <Tabs defaultValue="editor" className="flex flex-col h-full">
          <TabsList className="w-fit">
            <TabsTrigger value="editor">Editor</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="script">Script</TabsTrigger>
            <TabsTrigger value="assets">Assets</TabsTrigger>
          </TabsList>
          <TabsContent value="editor" className="flex-grow flex flex-col">
            {activeSlide ? (
              <SlideEditor
                key={activeSlide.id}
                slide={activeSlide}
                updateSlide={updateSlide}
                slideIndex={activeSlideIndex}
                applyTokensToAll={applyTokensToAll}
                presentationId={presentation?.id}
                graphics={(presentation?.initialInput?.graphicsFiles || []).map(f => ({ name: f.name, url: f.url })) as any}
                assets={[
                  ...((presentation?.initialInput?.files || []).map(f => ({
                  name: f.name,
                  url: f.url,
                  kind: f.kind || (/(png|jpg|jpeg|gif|webp|svg)$/i.test(f.name) ? 'image' : /(pdf|docx|md|txt|csv|xls|xlsx)$/i.test(f.name) ? 'document' : 'other'),
                })) as any),
                  ...((presentation?.initialInput?.graphicsFiles || []).map(f => ({
                    name: f.name,
                    url: f.url,
                    kind: 'image' as const,
                  })) as any),
                ]}
                constraints={presentation ? (
                  (activeSlide.useConstraints === false && activeSlide.constraintsOverride)
                  ? activeSlide.constraintsOverride
                  : {
                      citationsRequired: presentation.initialInput?.citationsRequired,
                      slideDensity: presentation.initialInput?.slideDensity,
                      mustInclude: presentation.initialInput?.mustInclude,
                      mustAvoid: presentation.initialInput?.mustAvoid,
                    }
                ) : undefined}
              />
            ) : (
              <div className="flex-grow flex items-center justify-center bg-card rounded-lg shadow-inner">
                <p className="text-muted-foreground">Select a slide to edit or add a new one.</p>
              </div>
            )}
          </TabsContent>
          <TabsContent value="chat" className="flex-grow">
            {presentation && setPresentation && uploadFile ? (
              <ClarificationChat
                presentation={presentation}
                setPresentation={setPresentation}
                onClarificationComplete={() => { /* remain in editing */ }}
                uploadFile={uploadFile}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">Chat unavailable</div>
            )}
          </TabsContent>
          <TabsContent value="script" className="flex-grow flex flex-col gap-3">
            <div className="flex gap-2">
              <Button
                onClick={async () => {
                  if (!setPresentation || !presentation) return;
                  const assets = (presentation.initialInput?.files || []);
                  const script = await generateFullScript(slides.map(s => ({ title: s.title, content: s.content, speakerNotes: s.speakerNotes })), assets as any);
                  setPresentation(prev => ({ ...(prev as any), fullScript: script }));
                }}
              >Generate Script</Button>
              <Button variant="outline" onClick={() => downloadScript(slides)}>
                <Download className="mr-2 h-4 w-4" />
                Download as .txt
              </Button>
            </div>
            <Textarea className="flex-grow" value={presentation?.fullScript || ''} onChange={(e) => setPresentation && setPresentation(prev => ({ ...(prev as any), fullScript: e.target.value }))} placeholder="Generate to view a full script with references..." />
          </TabsContent>
          <TabsContent value="assets" className="flex-grow flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Manage uploaded assets by category: Content, Style, and Graphics.</div>
              {uploadFile && setPresentation ? (
                <div className="flex items-center gap-2">
                  {/* Hidden inputs */}
                  <input id="asset-upload-content" type="file" multiple className="hidden" onChange={async (e)=>{
                    const files = Array.from(e.target.files || [])
                    if (!files.length) return
                    for (const f of files) {
                      try {
                        const res = await uploadFile(f as File, 'content')
                        setPresentation((prev: any) => ({
                          ...prev,
                          initialInput: {
                            ...(prev.initialInput||{}),
                            files: [ ...((prev.initialInput?.files)||[]), { name: res.name, url: res.url, path: res.path } ],
                          }
                        }))
                      } catch {}
                    }
                    try { (e.target as HTMLInputElement).value = '' } catch {}
                  }} />
                  <input id="asset-upload-style" type="file" multiple className="hidden" onChange={async (e)=>{
                    const files = Array.from(e.target.files || [])
                    if (!files.length) return
                    for (const f of files) {
                      try {
                        const res = await uploadFile(f as File, 'style')
                        setPresentation((prev: any) => ({
                          ...prev,
                          initialInput: {
                            ...(prev.initialInput||{}),
                            styleFiles: [ ...((prev.initialInput?.styleFiles)||[]), { name: res.name, url: res.url, path: res.path } ],
                          }
                        }))
                      } catch {}
                    }
                    try { (e.target as HTMLInputElement).value = '' } catch {}
                  }} />
                  <input id="asset-upload-graphics" type="file" multiple className="hidden" onChange={async (e)=>{
                    const files = Array.from(e.target.files || [])
                    if (!files.length) return
                    for (const f of files) {
                      try {
                        const res = await uploadFile(f as File, 'graphics')
                        setPresentation((prev: any) => ({
                          ...prev,
                          initialInput: {
                            ...(prev.initialInput||{}),
                            graphicsFiles: [ ...((prev.initialInput?.graphicsFiles)||[]), { name: res.name, url: res.url, path: res.path } ],
                          }
                        }))
                      } catch {}
                    }
                    try { (e.target as HTMLInputElement).value = '' } catch {}
                  }} />
                  {/* Action buttons */}
                  <Button size="sm" variant="outline" asChild>
                    <label htmlFor="asset-upload-content" className="cursor-pointer">
                      <Upload className="mr-2 h-4 w-4" /> Upload Content
                    </label>
                  </Button>
                  <Button size="sm" variant="outline" asChild>
                    <label htmlFor="asset-upload-style" className="cursor-pointer">
                      <Upload className="mr-2 h-4 w-4" /> Upload Style
                    </label>
                  </Button>
                  <Button size="sm" asChild>
                    <label htmlFor="asset-upload-graphics" className="cursor-pointer">
                      <Upload className="mr-2 h-4 w-4" /> Upload Graphics
                    </label>
                  </Button>
                  <Button size="sm" variant="secondary" onClick={()=>{ const el = document.getElementById('asset-upload-content') as HTMLInputElement | null; if (!el) return; el.setAttribute('webkitdirectory',''); el.setAttribute('directory',''); try { el.click() } catch {} }}>Upload Content Folder</Button>
                  <Button size="sm" variant="secondary" onClick={()=>{ const el = document.getElementById('asset-upload-style') as HTMLInputElement | null; if (!el) return; el.setAttribute('webkitdirectory',''); el.setAttribute('directory',''); try { el.click() } catch {} }}>Upload Style Folder</Button>
                  <Button size="sm" variant="secondary" onClick={()=>{ const el = document.getElementById('asset-upload-graphics') as HTMLInputElement | null; if (!el) return; el.setAttribute('webkitdirectory',''); el.setAttribute('directory',''); try { el.click() } catch {} }}>Upload Graphics Folder</Button>
                </div>
              ) : null}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded-md p-3 bg-card">
                <div className="font-medium mb-2">Content Files</div>
                <AssetList
                  items={(presentation?.initialInput?.files || []) as any}
                  onRemove={(idx)=> setPresentation && setPresentation(prev => ({
                    ...(prev as any),
                    initialInput: { ...(prev as any).initialInput, files: [...((prev as any).initialInput.files||[]).filter((_: any, i: number)=> i!==idx)] }
                  }))}
                />
              </div>
              <div className="border rounded-md p-3 bg-card">
                <div className="font-medium mb-2">Style Files</div>
                <AssetList
                  items={(presentation?.initialInput?.styleFiles || []) as any}
                  onRemove={(idx)=> setPresentation && setPresentation(prev => ({
                    ...(prev as any),
                    initialInput: { ...(prev as any).initialInput, styleFiles: [...((prev as any).initialInput.styleFiles||[]).filter((_: any, i: number)=> i!==idx)] }
                  }))}
                />
              </div>
              <div className="border rounded-md p-3 bg-card">
                <div className="font-medium mb-2">Graphics (Illustrations)</div>
                <AssetList
                  items={(presentation?.initialInput?.graphicsFiles || []) as any}
                  onRemove={(idx)=> setPresentation && setPresentation(prev => ({
                    ...(prev as any),
                    initialInput: { ...(prev as any).initialInput, graphicsFiles: [...((prev as any).initialInput.graphicsFiles||[]).filter((_: any, i: number)=> i!==idx)] }
                  }))}
                />
              </div>
            </div>
            {/* Project logs */}
            <div className="mt-4">
              {presentation?.id ? <ProjectLogs presentationId={presentation.id} /> : null}
            </div>
          </TabsContent>
        </Tabs>
        {/* Downloads footer removed; centralized in top bar */}
      </main>
    </div>
  );
}

function AssetList({ items, onRemove }: { items: { name: string; url: string }[]; onRemove?: (index: number) => void }) {
  if (!items?.length) return (<div className="text-sm text-muted-foreground">No files uploaded.</div>)
  return (
    <div className="space-y-2 max-h-64 overflow-auto pr-2">
      {items.map((f, i) => {
        const isImg = /\.(png|jpe?g|gif|webp|svg)$/i.test((f.name||'') + ' ' + (f.url||''))
        return (
          <div key={i} className="flex items-center justify-between border rounded p-2 bg-background">
            <div className="flex items-center gap-3 min-w-0">
              {isImg ? <FileImage className="h-4 w-4 text-muted-foreground" /> : <FileText className="h-4 w-4 text-muted-foreground" />}
              <div className="truncate" title={f.name}>{f.name}</div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <a className="text-sm underline flex items-center gap-1" href={f.url} target="_blank" rel="noreferrer">
                <ExternalLink className="h-3 w-3" /> Open
              </a>
              {onRemove ? (
                <Button size="sm" variant="destructive" className="h-7" onClick={()=> onRemove(i)}>
                  <Trash2 className="h-3.5 w-3.5 mr-1" /> Remove
                </Button>
              ) : null}
            </div>
          </div>
        )
      })}
    </div>
  )
}
