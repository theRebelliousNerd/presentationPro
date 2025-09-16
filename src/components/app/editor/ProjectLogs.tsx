'use client'

import React, { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Label } from '@/components/ui/label'

type LogItem = {
  created_at?: string
  agent?: string
  role?: string
  channel?: string
  content?: string
}

export default function ProjectLogs({ presentationId }: { presentationId: string }) {
  const [items, setItems] = useState<LogItem[]>([])
  const [agent, setAgent] = useState<string>('')
  const [loading, setLoading] = useState(false)

  useEffect(() => { (async () => {
    if (!presentationId) return
    setLoading(true)
    try {
      const base = (process.env.NEXT_PUBLIC_ADK_BASE_URL || process.env.ADK_BASE_URL || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}${window.location.port==='3000'?':18088':(window.location.port?':'+window.location.port:'')}` : '')) as string
      const url = `${base}/v1/arango/presentations/${encodeURIComponent(presentationId)}/messages?limit=100${agent ? `&agent=${encodeURIComponent(agent)}` : ''}`
      const res = await fetch(url)
      if (res.ok) {
        const js = await res.json()
        if (js && js.success && Array.isArray(js.data)) setItems(js.data)
      }
    } catch {}
    setLoading(false)
  })() }, [presentationId, agent])

  return (
    <Card className="bg-card border rounded-md">
      <CardContent className="p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="font-medium">Project Logs</div>
          <div className="flex items-center gap-2">
            <Label className="text-xs text-muted-foreground">Agent</Label>
            <select className="border rounded p-1 text-sm" value={agent} onChange={e=>setAgent(e.target.value)}>
              <option value="">All</option>
              <option value="clarifier">Clarifier</option>
              <option value="outline">Outline</option>
              <option value="slide_writer">Slide Writer</option>
              <option value="critic">Critic</option>
              <option value="notes_polisher">Notes</option>
              <option value="design">Design</option>
              <option value="script_writer">Script</option>
              <option value="research">Research</option>
            </select>
          </div>
        </div>
        <div className="max-h-64 overflow-auto space-y-2">
          {loading ? <div className="text-sm text-muted-foreground">Loading…</div> : null}
          {!loading && (!items || !items.length) ? <div className="text-sm text-muted-foreground">No logs</div> : null}
          {items.map((it, i) => (
            <div key={i} className="border rounded p-2 bg-background">
              <div className="text-xs text-muted-foreground flex items-center justify-between">
                <span>{new Date(it.created_at || '').toLocaleString()}</span>
                <span>{(it.agent || '')} · {(it.role || '')} · {(it.channel || '')}</span>
              </div>
              <div className="text-sm whitespace-pre-wrap">{it.content}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

