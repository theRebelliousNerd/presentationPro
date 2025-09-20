'use client'

import { usePresentationStateArango as usePresentationState } from '@/hooks/use-presentation-state-arango'
import { useEffect, useState } from 'react'
import { listPresentations, createPresentationRecord } from '@/lib/arango-client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function PresentationsPage() {
  const { presentation, duplicatePresentation } = usePresentationState()
  const router = useRouter()
  const [items, setItems] = useState<any[]>([])
  useEffect(() => { (async()=>{ setItems(await listPresentations(100)) })() }, [])
  const slides = presentation.slides?.length || 0
  const assets = (presentation.initialInput?.files?.length || 0) + (presentation.initialInput?.styleFiles?.length || 0)

  return (
    <main className="max-w-5xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">Presentations</h1>
      <Card className="md-surface md-elevation-1">
        <CardHeader>
          <CardTitle>Current Presentation</CardTitle>
          <CardDescription>ID: {presentation.id}</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-between gap-4">
          <div className="text-sm text-muted-foreground">
            <div>Slides: <b>{slides}</b></div>
            <div>Assets: <b>{assets}</b></div>
          </div>
          <div className="flex gap-2">
            <Link href="/">
              <Button variant="outline">Open</Button>
            </Link>
            <Button onClick={async ()=> { const id = await duplicatePresentation(); alert(`Duplicated as ${id}`) }}>Duplicate</Button>
            <Button variant="secondary" onClick={async ()=>{
              const nid = (Math.random().toString(36).slice(2,10)+Date.now().toString(36))
              await createPresentationRecord(nid)
              try { localStorage.setItem('presentationId', nid) } catch {}
              router.push('/')
            }}>New Presentation</Button>
          </div>
        </CardContent>
      </Card>

      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-2">All Projects</h2>
        {items && items.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {items.map((it, idx)=> (
              <Card key={idx} className="hover:bg-card/70">
                <CardHeader>
                  <CardTitle className="text-base">{it.title || it.presentation_id}</CardTitle>
                  <CardDescription>Status: {it.status || 'unknown'}</CardDescription>
                </CardHeader>
                <CardContent className="flex items-center justify-between">
                  <div className="text-xs text-muted-foreground">{it.updated_at ? new Date(it.updated_at).toLocaleString() : ''}</div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={async ()=>{
                      try{
                        // Clear any existing state to prevent conflicts
                        localStorage.removeItem('appState');
                        localStorage.removeItem('presentationDoc');
                        // Set the new presentation ID
                        localStorage.setItem('presentationId', it.presentation_id);
                        console.log('Loading presentation:', it.presentation_id);
                      } catch(e) {
                        console.error('Failed to set presentation ID:', e);
                      }
                      // Use window.location to ensure full page reload with new state
                      window.location.href = `/?id=${it.presentation_id}`;
                    }}>Open</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">No projects found.</div>
        )}
      </div>
    </main>
  )
}
