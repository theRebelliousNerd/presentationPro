'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { orchResearchBackgrounds } from '@/lib/orchestrator'

export default function ResearchHelper({ onInsert }: { onInsert?: (rules: string[]) => void }) {
  const [query, setQuery] = useState('presentation background best practices legibility minimalism accessibility')
  const [allowDomains, setAllowDomains] = useState('')
  const [topK, setTopK] = useState(5)
  const [rules, setRules] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchRules = async () => {
    setLoading(true)
    setError(null)
    try {
      const mdl = typeof window !== 'undefined' ? localStorage.getItem('app.model.text') || undefined : undefined
      const domains = allowDomains.split(',').map(s => s.trim()).filter(Boolean)
      const res = await orchResearchBackgrounds({ textModel: mdl, query, topK, allowDomains: domains.length ? domains : undefined })
      setRules(res.rules || [])
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
      </div>
    </div>
  )
}
