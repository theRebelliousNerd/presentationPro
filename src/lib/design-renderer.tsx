import React, { useEffect, useMemo, useRef } from 'react'
import type { Slide } from '@/lib/types'

export type DesignRendererProps = {
  slide: Slide
  className?: string
}

// Very conservative renderer for sanitized layout/html/css
export function DesignRenderer({ slide, className }: DesignRendererProps) {
  const spec = slide.designSpec
  const containerRef = useRef<HTMLDivElement>(null)

  const cssVars = useMemo(() => {
    const t = spec?.tokens || {}
    const c = t.colors || {}
    const vars: React.CSSProperties = {}
    if (c.bg) vars['--color-bg' as any] = c.bg
    if (c.primary) vars['--color-primary' as any] = c.primary
    if (c.muted) vars['--color-muted' as any] = c.muted
    if (c.text) vars['--color-text' as any] = c.text
    const tc = t as any
    if (tc.textColors?.title) vars['--color-text-title' as any] = tc.textColors.title
    if (tc.textColors?.body) vars['--color-text-body' as any] = tc.textColors.body
    if (t.fonts?.headline) vars['--font-headline' as any] = t.fonts.headline
    if (t.fonts?.body) vars['--font-body' as any] = t.fonts.body
    if (typeof t.spacing === 'number') vars['--space' as any] = `${t.spacing}px`
    if (typeof t.radii === 'number') vars['--radius' as any] = `${t.radii}px`
    return vars
  }, [spec?.tokens])

  useEffect(() => {
    // Populate slots if declared (title, bullets)
    const root = containerRef.current
    if (!root || !spec?.layout?.slots) return
    try {
      const slots = spec.layout.slots
      if (slots.title) {
        const el = root.querySelector(slots.title)
        if (el) el.textContent = slide.title
      }
      if (slots.bullets && Array.isArray(slide.content)) {
        const el = root.querySelector(slots.bullets)
        if (el) {
          // If it's a UL/OL, render <li> items
          if (el.tagName === 'UL' || el.tagName === 'OL') {
            el.innerHTML = ''
            slide.content.forEach((line) => {
              const li = document.createElement('li')
              li.textContent = line
              el.appendChild(li)
            })
          } else {
            el.textContent = slide.content.join(' • ')
          }
        }
      }
    } catch {}
  }, [slide.id, slide.title, slide.content, spec?.layout?.slots])

  // Background styling
  const bgStyle: React.CSSProperties = useMemo(() => {
    const style: React.CSSProperties = {}
    if (spec?.background?.css) {
      style.backgroundImage = spec.background.css
    }
    return style
  }, [spec?.background?.css])

  return (
    <div ref={containerRef} className={className || ''} style={cssVars}>
      {/* Background layer */}
      <div className="absolute inset-0" style={bgStyle}>
        {spec?.background?.svg ? (
          <div className="w-full h-full" dangerouslySetInnerHTML={{ __html: spec.background.svg }} />
        ) : null}
      </div>
      {/* Layout CSS */}
      {spec?.layout?.css ? (
        <style dangerouslySetInnerHTML={{ __html: spec.layout.css }} />
      ) : null}
      {/* Layout HTML */}
      <div className="absolute inset-0">
        {spec?.layout?.html ? (
          <div className="w-full h-full" dangerouslySetInnerHTML={{ __html: spec.layout.html }} />
        ) : null}
        {/* Optional additional SVG */}
        {spec?.layout?.svg ? (
          <div className="pointer-events-none" dangerouslySetInnerHTML={{ __html: spec.layout.svg }} />
        ) : null}
      </div>
    </div>
  )
}

export default DesignRenderer
