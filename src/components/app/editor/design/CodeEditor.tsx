import React, { useEffect, useState } from 'react'
import type { Slide } from '@/lib/types'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { sanitizeDesignCode, validateDesignCode } from '@/lib/actions'

type CodeEditorProps = {
  slide: Slide
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void
}

export default function CodeEditor({ slide, updateSlide }: CodeEditorProps) {
  const [html, setHtml] = useState(slide.designSpec?.layout?.html || '')
  const [css, setCss] = useState(slide.designSpec?.layout?.css || '')
  const [svg, setSvg] = useState(slide.designSpec?.layout?.svg || '')
  const [status, setStatus] = useState<string>('')
  const [errors, setErrors] = useState<string[]>([])
  const [warnings, setWarnings] = useState<string[]>([])

  useEffect(() => {
    setHtml(slide.designSpec?.layout?.html || '')
    setCss(slide.designSpec?.layout?.css || '')
    setSvg(slide.designSpec?.layout?.svg || '')
  }, [slide.id])

  const validate = async () => {
    setStatus('Validating...')
    try {
      const res = await validateDesignCode(html, css, svg)
      setWarnings(res.warnings || [])
      setErrors(res.errors || [])
      setStatus(res.ok ? 'OK' : 'Issues found')
    } catch (e: any) {
      setStatus('Validation failed')
      setErrors([String(e?.message || e) || 'Validation error'])
    }
  }

  const save = async () => {
    setStatus('Sanitizing...')
    try {
      const res = await sanitizeDesignCode(html, css, svg)
      const next = { ...(slide.designSpec || {}), layout: { ...(slide.designSpec?.layout||{}), html: res.html || html, css: res.css || css, svg: res.svg || svg } }
      updateSlide(slide.id, { designSpec: next })
      setWarnings(res.warnings || [])
      setStatus('Saved')
    } catch (e: any) {
      setStatus('Save failed')
      setErrors([String(e?.message || e) || 'Save error'])
    }
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <Label>Layout HTML</Label>
          <Textarea value={html} onChange={e=>setHtml(e.target.value)} className="min-h-48 font-mono" />
        </div>
        <div>
          <Label>Layout CSS</Label>
          <Textarea value={css} onChange={e=>setCss(e.target.value)} className="min-h-48 font-mono" />
        </div>
      </div>
      <div>
        <Label>Extra SVG (optional)</Label>
        <Textarea value={svg} onChange={e=>setSvg(e.target.value)} className="min-h-24 font-mono" />
      </div>
      <div className="flex gap-2 items-center">
        <Button size="sm" onClick={validate}>Validate</Button>
        <Button size="sm" variant="secondary" onClick={save}>Validate & Save</Button>
        <span className="text-sm text-muted-foreground">{status}</span>
      </div>
      {(warnings && warnings.length) ? (
        <div className="text-sm text-amber-600">Warnings: {warnings.join('; ')}</div>
      ) : null}
      {(errors && errors.length) ? (
        <div className="text-sm text-red-600">Errors: {errors.join('; ')}</div>
      ) : null}
    </div>
  )
}

