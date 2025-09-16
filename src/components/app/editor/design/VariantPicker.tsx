import React, { useState } from 'react'
import type { Slide } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { craftDesign } from '@/lib/actions'

type VariantPickerProps = {
  slide: Slide
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void
}

export default function VariantPicker({ slide, updateSlide }: VariantPickerProps) {
  const [loading, setLoading] = useState(false)
  const [variants, setVariants] = useState<any[]>([])

  const regenerate = async () => {
    if (loading) return
    setLoading(true)
    try {
      const theme = (typeof window !== 'undefined' && (localStorage.getItem('app.theme') as any)) || 'brand'
      const pattern = (typeof window !== 'undefined' && (localStorage.getItem('app.bgPattern') as any)) || 'gradient'
      const iconPack = (typeof window !== 'undefined' && (localStorage.getItem('app.iconPack') as any)) || 'lucide'
      const res = await craftDesign({ title: slide.title, content: slide.content, speakerNotes: slide.speakerNotes }, { theme, pattern, preferLayout: true, variants: 3, iconPack })
      const vars = (res.variants || []).map(v => ({ ...v, designSpec: v.designSpec || v.designspec || v.spec }))
      setVariants(vars)
      if (res.designSpec) updateSlide(slide.id, { designSpec: res.designSpec })
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('Variant generation failed', e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Button size="sm" onClick={regenerate} disabled={loading}>{loading ? 'Generating…' : 'Regenerate Variants'}</Button>
      </div>
      {variants && variants.length ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {variants.map((v, i) => (
            <div key={i} className="border rounded p-2 bg-background">
              <div className="text-sm mb-1">Score: {(v.score ?? 0).toFixed(2)}</div>
              <div className="text-xs text-muted-foreground mb-2">{v.rationale || '—'}</div>
              <Button size="sm" variant="secondary" onClick={()=> updateSlide(slide.id, { designSpec: v.designSpec })}>Use This</Button>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

