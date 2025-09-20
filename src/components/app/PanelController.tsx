'use client'

import { useEffect, useState } from 'react'
import ClarificationChat from '@/components/app/ClarificationChat'
import WorkflowPanel from '@/components/app/WorkflowPanel'
import { Presentation } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { orchListReviews } from '@/lib/orchestrator'
import { resolveAdkBaseUrl } from '@/lib/base-url'

type PanelKind = 'chat' | 'reviews' | 'workflow' | null

export default function PanelController({
  presentation,
  setPresentation,
  appState,
  setAppState,
  uploadFile,
  activeSlideIndex,
}: {
  presentation: Presentation
  setPresentation: (updater: (prev: Presentation) => Presentation) => void
  appState: string
  setAppState: (s: any) => void
  uploadFile: (file: File) => Promise<any>
  activeSlideIndex?: number | null
}) {
  const [open, setOpen] = useState<PanelKind>(null)
  const [reviews, setReviews] = useState<{ created_at?: string; agent_source?: string; review_data?: any }[]>([])
  const [limit, setLimit] = useState(10)
  const [offset, setOffset] = useState(0)
  const [refreshTick, setRefreshTick] = useState(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const onToggle = (e: any) => {
      const detail = (e && e.detail) || {}
      const kind: PanelKind = detail && (detail.panel as PanelKind)
      setOpen(prev => (prev === kind ? null : kind))
    }
    window.addEventListener('panel:toggle', onToggle as any)
    return () => window.removeEventListener('panel:toggle', onToggle as any)
  }, [])

  // Broadcast panel state so other components (sidebar) can reflect active state
  useEffect(() => {
    try { window.dispatchEvent(new CustomEvent('panel:state', { detail: { panel: open } })) } catch {}
  }, [open])

  // Keyboard shortcuts: c = chat, r = reviews, esc = close
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null
      const tag = (target?.tagName || '').toLowerCase()
      const editable = (target as any)?.isContentEditable
      if (tag === 'input' || tag === 'textarea' || tag === 'select' || editable) return
      if (e.key === 'c' || e.key === 'C') {
        e.preventDefault(); setOpen(prev => (prev === 'chat' ? null : 'chat')); return
      }
      if (e.key === 'r' || e.key === 'R') {
        e.preventDefault(); setOpen(prev => (prev === 'reviews' ? null : 'reviews')); return
      }
      if (e.key === 'Escape') { setOpen(null); return }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    const fetchReviews = async () => {
      if (open !== 'reviews' || !presentation?.id || activeSlideIndex == null) return
      setLoading(true)
      try {
        const base = resolveAdkBaseUrl()
        const res = await fetch(`${base}/v1/arango/presentations/${encodeURIComponent(presentation.id)}/slides/${activeSlideIndex}/reviews?limit=${limit}&offset=${offset}`)
        if (res.ok) {
          const data = await res.json()
          if (data && data.success && Array.isArray(data.data)) setReviews(data.data)
        }
      } catch {}
      setLoading(false)
    }
    fetchReviews()
  }, [open, presentation?.id, activeSlideIndex, limit, offset, refreshTick])

  // Broadcast count for sidebar badge (last fetch)
  useEffect(() => {
    try { window.dispatchEvent(new CustomEvent('panel:reviewsCount', { detail: { count: reviews?.length || 0 } })) } catch {}
  }, [reviews])

  if (!open) return null

  return (
    <>
    {/* overlay */}
    <div className="fixed inset-0 z-40 bg-black/20" onClick={()=>setOpen(null)} />
    <div className="fixed top-16 bottom-0 left-16 z-50">
      <div className="h-full w-[360px] md:w-[420px] lg:w-[460px] bg-card border-r md-surface md-elevation-2 overflow-hidden">
        {open === 'chat' ? (
          <div className="h-full p-3">
            <ClarificationChat
              compact
              presentation={presentation}
              setPresentation={setPresentation as any}
              onClarificationComplete={(goals)=>{ setPresentation(prev=>({ ...prev, clarifiedGoals: goals } as any)); setAppState('approving') }}
              uploadFile={uploadFile}
            />
          </div>
        ) : null}
        {open === 'workflow' ? (
          <div className="h-full p-3">
            <WorkflowPanel presentation={presentation} />
          </div>
        ) : null}
        {open === 'reviews' ? (
          <div className="h-full flex flex-col p-3 gap-3">
            <div className="flex items-center justify-between">
              <div className="font-headline font-semibold">Review History</div>
              <Button size="sm" variant="outline" onClick={()=>{ setOpen(null) }}>Close</Button>
            </div>
            <div className="text-sm text-muted-foreground">Slide {activeSlideIndex != null ? activeSlideIndex + 1 : '-'} | {presentation?.id || ''}</div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={()=>{ setOffset(prev => Math.max(0, prev - limit)) }} disabled={offset<=0}>Prev</Button>
              <Button size="sm" variant="outline" onClick={()=>{ setOffset(prev => prev + limit) }}>Next</Button>
              <Button size="sm" onClick={()=> setRefreshTick(x=>x+1)}>Refresh</Button>
            </div>
            <div className="flex-1 overflow-auto space-y-2 pr-2">
              {loading ? (
                <div className="text-sm text-muted-foreground">Loading…</div>
              ) : reviews.length ? (
                reviews.map((r, i) => (
                  <div key={i} className="p-2 rounded border bg-background">
                    <div className="text-xs text-muted-foreground mb-1">{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</div>
                    <div className="text-sm"><b>Issues:</b> {(r.review_data?.issues || []).join('; ') || '—'}</div>
                    <div className="text-sm"><b>Suggestions:</b> {(r.review_data?.suggestions || []).join('; ') || '—'}</div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-muted-foreground">No reviews yet for this slide.</div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
    </>
  )
}
