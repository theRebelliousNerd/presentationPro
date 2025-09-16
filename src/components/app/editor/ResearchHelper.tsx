'use client'

import { useEffect, useState } from 'react'
import { nanoid } from 'nanoid'
import { Button } from '@/components/ui/button'
import type { Presentation } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { orchResearchBackgrounds } from '@/lib/orchestrator'

type ResearchHelperProps = {
  onInsert?: (rules: string[]) => void;
  setPresentation?: (updater: (prev: Presentation) => Presentation) => void;
  presentationId?: string;
  presentation?: Presentation;
};

export default function ResearchHelper({ onInsert, setPresentation, presentationId, presentation }: ResearchHelperProps) {
  const [query, setQuery] = useState('presentation background best practices legibility minimalism accessibility')
  const [allowDomains, setAllowDomains] = useState('')
  const [topK, setTopK] = useState(5)
  const [rules, setRules] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [initializedFromSaved, setInitializedFromSaved] = useState(false)

  const savedNotes = (presentation?.researchNotebook || []).slice().sort((a, b) => {
    return new Date(b.createdAt || '').getTime() - new Date(a.createdAt || '').getTime()
  })

  useEffect(() => {
    if (initializedFromSaved) return
    if (!rules.length && savedNotes.length) {
      const latest = savedNotes[0]
      setRules(latest.rules || [])
      setQuery(latest.query || query)
      setAllowDomains((latest.allowDomains || []).join(', '))
      if (typeof latest.topK === 'number') setTopK(latest.topK)
      setInitializedFromSaved(true)
    }
  }, [initializedFromSaved, rules.length, savedNotes, query])

  const fetchRules = async () => {
    setLoading(true)
    setError(null)
    try {
      const mdl = typeof window !== 'undefined' ? localStorage.getItem('app.model.text') || undefined : undefined
      const domains = allowDomains.split(',').map(s => s.trim()).filter(Boolean)
      const res = await orchResearchBackgrounds({ textModel: mdl, query, topK, allowDomains: domains.length ? domains : undefined, presentationId })
      const nextRules = res.rules || []
      setRules(nextRules)
      if (setPresentation) {
        const noteId = nanoid()
        const createdAt = new Date().toISOString()
        setPresentation(prev => ({
          ...prev,
          researchNotebook: [
            ...(prev.researchNotebook || []),
            {
              id: noteId,
              query,
              rules: nextRules,
              createdAt,
              allowDomains: domains.length ? domains : undefined,
              topK,
              model: mdl,
              extractions: Array.isArray(res.extractions) ? res.extractions : undefined,
            },
          ],
        }))
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to fetch research rules')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-6 border-t pt-4">
      <div className="font-headline font-semibold mb-2">Research: Background Rules</div>
      <div className="space-y-2 text-sm">
        <div>
          <Label htmlFor="rq">Query</Label>
          <Input id="rq" value={query} onChange={e => setQuery(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label htmlFor="rk">Top K</Label>
            <Input id="rk" type="number" min={1} max={10} value={String(topK)} onChange={e => setTopK(Number(e.target.value || '5'))} />
          </div>
          <div>
            <Label htmlFor="rd">Allow Domains (comma separated)</Label>
            <Input id="rd" placeholder=".gov, .edu" value={allowDomains} onChange={e => setAllowDomains(e.target.value)} />
          </div>
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={fetchRules} disabled={loading}>{loading ? 'Loading…' : 'Fetch Rules'}</Button>
          <Button size="sm" variant="outline" disabled={!rules.length} onClick={() => onInsert && onInsert(rules)}>Insert into Notes</Button>
        </div>
        {error ? <div className="text-red-500 text-xs">{error}</div> : null}
        <div>
          <Label>Rules</Label>
          <Textarea className="min-h-[120px]" value={(rules || []).map(r => `• ${r}`).join('\n')} readOnly />
        </div>
        {savedNotes.length ? (
          <div className="pt-3 border-t">
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Saved research</div>
            <div className="space-y-2 max-h-52 overflow-auto pr-1">
              {savedNotes.map(note => (
                <div key={note.id} className="border rounded-md p-2 bg-background">
                  <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                    <span>{note.createdAt ? new Date(note.createdAt).toLocaleString() : 'Saved note'}</span>
                    {note.topK ? <span>K={note.topK}</span> : null}
                  </div>
                  <div className="text-sm font-medium truncate" title={note.query}>{note.query || '—'}</div>
                  {note.allowDomains?.length ? (
                    <div className="text-[11px] text-muted-foreground truncate">Domains: {note.allowDomains.join(', ')}</div>
                  ) : null}
                  <div className="mt-2 flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => onInsert && onInsert(note.rules || [])}>Insert</Button>
                    <Button size="sm" variant="ghost" onClick={() => {
                      setRules(note.rules || [])
                      setQuery(note.query || '')
                      setAllowDomains((note.allowDomains || []).join(', '))
                      if (typeof note.topK === 'number') setTopK(note.topK)
                    }}>Load</Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
