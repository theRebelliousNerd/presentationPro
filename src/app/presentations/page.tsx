'use client'

import { usePresentationState } from '@/hooks/use-presentation-state'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function PresentationsPage() {
  const { presentation, duplicatePresentation } = usePresentationState()
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
          </div>
        </CardContent>
      </Card>
    </main>
  )
}

