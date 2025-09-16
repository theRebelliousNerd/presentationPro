import React, { useEffect, useState } from 'react'
import type { Slide } from '@/lib/types'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

type TokenEditorProps = {
  slide: Slide
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void
  onApplyToAll?: (tokens: any) => void
}

export default function TokenEditor({ slide, updateSlide, onApplyToAll }: TokenEditorProps) {
  const [bg, setBg] = useState(slide.designSpec?.tokens?.colors?.bg || '#192940')
  const [primary, setPrimary] = useState(slide.designSpec?.tokens?.colors?.primary || '#73BF50')
  const [muted, setMuted] = useState(slide.designSpec?.tokens?.colors?.muted || '#556273')
  const [text, setText] = useState(slide.designSpec?.tokens?.colors?.text || '#FFFFFF')
  const [spacing, setSpacing] = useState(String(slide.designSpec?.tokens?.spacing ?? 8))
  const [radii, setRadii] = useState(String(slide.designSpec?.tokens?.radii ?? 12))
  const [fontHeadline, setFontHeadline] = useState(slide.designSpec?.tokens?.fonts?.headline || 'Montserrat')
  const [fontBody, setFontBody] = useState(slide.designSpec?.tokens?.fonts?.body || 'Roboto')
  const [titleColor, setTitleColor] = useState(slide.designSpec?.tokens?.textColors?.title || (slide.designSpec?.tokens?.colors?.text || '#FFFFFF'))
  const [bodyColor, setBodyColor] = useState(slide.designSpec?.tokens?.textColors?.body || (slide.designSpec?.tokens?.colors?.text || '#FFFFFF'))

  useEffect(() => {
    setBg(slide.designSpec?.tokens?.colors?.bg || '#192940')
    setPrimary(slide.designSpec?.tokens?.colors?.primary || '#73BF50')
    setMuted(slide.designSpec?.tokens?.colors?.muted || '#556273')
    setText(slide.designSpec?.tokens?.colors?.text || '#FFFFFF')
    setSpacing(String(slide.designSpec?.tokens?.spacing ?? 8))
    setRadii(String(slide.designSpec?.tokens?.radii ?? 12))
    setFontHeadline(slide.designSpec?.tokens?.fonts?.headline || 'Montserrat')
    setFontBody(slide.designSpec?.tokens?.fonts?.body || 'Roboto')
    setTitleColor(slide.designSpec?.tokens?.textColors?.title || (slide.designSpec?.tokens?.colors?.text || '#FFFFFF'))
    setBodyColor(slide.designSpec?.tokens?.textColors?.body || (slide.designSpec?.tokens?.colors?.text || '#FFFFFF'))
  }, [slide.id])

  const apply = () => {
    const tokens = {
      colors: { bg, primary, muted, text },
      textColors: { title: titleColor, body: bodyColor },
      fonts: { headline: fontHeadline, body: fontBody },
      spacing: Number(spacing || '8'),
      radii: Number(radii || '12'),
    }
    const next = { ...(slide.designSpec || {}), tokens }
    updateSlide(slide.id, { designSpec: next })
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label>Background</Label>
          <Input type="color" value={bg} onChange={e=>setBg(e.target.value)} />
        </div>
        <div>
          <Label>Primary</Label>
          <Input type="color" value={primary} onChange={e=>setPrimary(e.target.value)} />
        </div>
        <div>
          <Label>Muted</Label>
          <Input type="color" value={muted} onChange={e=>setMuted(e.target.value)} />
        </div>
        <div>
          <Label>Text</Label>
          <Input type="color" value={text} onChange={e=>setText(e.target.value)} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label>Title Text Color</Label>
          <Input type="color" value={titleColor} onChange={e=>setTitleColor(e.target.value)} />
        </div>
        <div>
          <Label>Body Text Color</Label>
          <Input type="color" value={bodyColor} onChange={e=>setBodyColor(e.target.value)} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label>Headline Font</Label>
          <select className="w-full border rounded p-2 bg-background" value={fontHeadline} onChange={e=>setFontHeadline(e.target.value)}>
            <option value="Montserrat">Montserrat</option>
            <option value="Inter">Inter</option>
            <option value="Source Sans 3">Source Sans 3</option>
            <option value="Roboto">Roboto</option>
          </select>
        </div>
        <div>
          <Label>Body Font</Label>
          <select className="w-full border rounded p-2 bg-background" value={fontBody} onChange={e=>setFontBody(e.target.value)}>
            <option value="Roboto">Roboto</option>
            <option value="Inter">Inter</option>
            <option value="Source Sans 3">Source Sans 3</option>
            <option value="Montserrat">Montserrat</option>
          </select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label>Spacing (px)</Label>
          <Input type="number" value={spacing} onChange={e=>setSpacing(e.target.value)} />
        </div>
        <div>
          <Label>Radius (px)</Label>
          <Input type="number" value={radii} onChange={e=>setRadii(e.target.value)} />
        </div>
      </div>
      <div className="flex gap-2">
        <Button size="sm" onClick={apply}>Apply</Button>
        {onApplyToAll ? <Button size="sm" variant="outline" onClick={()=> onApplyToAll({ colors: { bg, primary, muted, text }, spacing: Number(spacing||'8'), radii: Number(radii||'12') })}>Apply to All Slides</Button> : null}
      </div>
    </div>
  )
}
