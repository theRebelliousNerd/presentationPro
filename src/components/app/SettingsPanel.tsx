'use client'

import { ReactNode, useEffect, useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { useSearchCache } from '@/hooks/use-search-cache'
import { setPricing } from '@/lib/token-meter'
import { getAgentModels, setAgentModels } from '@/lib/agent-models'
import { getPricingForModel } from '@/lib/model-pricing'

export default function SettingsPanel() {
  const [pricePrompt, setPricePrompt] = useState<string>('0')
  const [priceCompletion, setPriceCompletion] = useState<string>('0')
  const [priceImageCall, setPriceImageCall] = useState<string>('0')
  const [theme, setTheme] = useState<string>('brand')
  const [bgPattern, setBgPattern] = useState<string>('gradient')
  const [typeScale, setTypeScale] = useState<string>('normal')
  const [textModel, setTextModel] = useState<string>('googleai/gemini-2.5-flash')
  const [imageModel, setImageModel] = useState<string>('googleai/gemini-2.5-flash-image-preview')
  const [iconPack, setIconPack] = useState<string>('lucide')
  const [stylePreset, setStylePreset] = useState<string>('brand-gradient')
  const [fontHeadline, setFontHeadline] = useState<string>('montserrat')
  const [fontBody, setFontBody] = useState<string>('roboto')
  const { config: searchCfg, loading: searchLoading, error: searchError, apply: applySearchCfg, clear: clearSearchCache, load: loadSearchCfg } = useSearchCache();
  const [searchEnabled, setSearchEnabled] = useState<boolean>(true)
  const [searchTtl, setSearchTtl] = useState<string>('3600')

  useEffect(() => {
    try {
      const raw = localStorage.getItem('tokenMeter.pricing')
      if (raw) {
        const p = JSON.parse(raw)
        if (p.pricePrompt != null) setPricePrompt(String(p.pricePrompt))
        if (p.priceCompletion != null) setPriceCompletion(String(p.priceCompletion))
        if (p.priceImageCall != null) setPriceImageCall(String(p.priceImageCall))
      }
    } catch {}
    try { const t = localStorage.getItem('app.theme'); if (t) setTheme(t) } catch {}
    try { const p = localStorage.getItem('app.bgPattern'); if (p) setBgPattern(p) } catch {}
    try { const ts = localStorage.getItem('app.typeScale'); if (ts) setTypeScale(ts) } catch {}
    try { const tm = localStorage.getItem('app.model.text'); if (tm) setTextModel(tm) } catch {}
    try { const im = localStorage.getItem('app.model.image'); if (im) setImageModel(im) } catch {}
    try { const ip = localStorage.getItem('app.iconPack'); if (ip) setIconPack(ip) } catch {}
    try { const sp = localStorage.getItem('app.stylePreset'); if (sp) setStylePreset(sp) } catch {}
    try { const fh = localStorage.getItem('app.font.headline'); if (fh) setFontHeadline(fh) } catch {}
    try { const fb = localStorage.getItem('app.font.body'); if (fb) setFontBody(fb) } catch {}
  }, [])

  // Agent models
  const [models, setModels] = useState(getAgentModels())

  useEffect(() => { loadSearchCfg() }, [loadSearchCfg])
  useEffect(() => {
    if (searchCfg) { setSearchEnabled(!!searchCfg.enabled); setSearchTtl(String(searchCfg.cacheTtl || 0)) }
  }, [searchCfg])

  const onSave = () => {
    setPricing({ pricePrompt: Number(pricePrompt||'0'), priceCompletion: Number(priceCompletion||'0'), priceImageCall: Number(priceImageCall||'0') })
    try { localStorage.setItem('app.theme', theme) } catch {}
    try { localStorage.setItem('app.bgPattern', bgPattern) } catch {}
    try { localStorage.setItem('app.typeScale', typeScale) } catch {}
    try { localStorage.setItem('app.model.text', textModel) } catch {}
    try { localStorage.setItem('app.model.image', imageModel) } catch {}
    try { localStorage.setItem('app.iconPack', iconPack) } catch {}
    try { localStorage.setItem('app.stylePreset', stylePreset) } catch {}
    try { localStorage.setItem('app.font.headline', fontHeadline) } catch {}
    try { localStorage.setItem('app.font.body', fontBody) } catch {}
    setAgentModels(models)
    try { window.dispatchEvent(new Event('settings:changed')) } catch {}
  }

  // Auto-sync pricing when model changes (immediate UX)
  useEffect(() => {
    const p = getPricingForModel(textModel)
    const img = getPricingForModel(imageModel)
    if (p.promptPerM != null || p.completionPerM != null || img.imageCall != null) {
      setPricing({
        pricePrompt: p.promptPerM ?? undefined,
        priceCompletion: p.completionPerM ?? undefined,
        priceImageCall: img.imageCall ?? undefined,
      } as any)
    }
  }, [textModel, imageModel])

  return (
    <>
      <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="pp">Text Prompt $/1M tokens</Label>
          <Input id="pp" value={pricePrompt} onChange={e=>setPricePrompt(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="pc">Completion $/1M tokens</Label>
          <Input id="pc" value={priceCompletion} onChange={e=>setPriceCompletion(e.target.value)} />
        </div>
      </div>
      <div>
        <Label htmlFor="pi">Image call $/call</Label>
        <Input id="pi" value={priceImageCall} onChange={e=>setPriceImageCall(e.target.value)} />
      </div>
      <div>
        <Label htmlFor="theme">Theme</Label>
        <select id="theme" className="w-full border rounded p-2 bg-background" value={theme} onChange={e=>setTheme(e.target.value)}>
          <option value="brand">Brand</option>
          <option value="muted">Muted</option>
          <option value="dark">Dark</option>
        </select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="preset">Style Preset</Label>
          <select id="preset" className="w-full border rounded p-2 bg-background" value={stylePreset} onChange={e=>{
            const val = e.target.value
            setStylePreset(val)
            switch(val){
              case 'brand-gradient':
                setTheme('brand'); setBgPattern('gradient'); setTypeScale('normal'); break;
              case 'brand-shapes':
                setTheme('brand'); setBgPattern('shapes'); setTypeScale('normal'); break;
              case 'grid-notes':
                setTheme('brand'); setBgPattern('grid'); setTypeScale('large'); break;
              case 'muted-gradient':
                setTheme('muted'); setBgPattern('gradient'); setTypeScale('normal'); break;
              case 'dark-minimal':
                setTheme('dark'); setBgPattern('gradient'); setTypeScale('normal'); break;
              case 'dots-playful':
                setTheme('brand'); setBgPattern('dots'); setTypeScale('normal'); break;
              case 'wave-subtle':
                setTheme('brand'); setBgPattern('wave'); setTypeScale('normal'); break;
            }
          }}>
            <option value="brand-gradient">Brand Gradient</option>
            <option value="brand-shapes">Brand Shapes</option>
            <option value="grid-notes">Grid (Notes)</option>
            <option value="muted-gradient">Muted Gradient</option>
            <option value="dark-minimal">Dark Minimal</option>
            <option value="dots-playful">Dots Playful</option>
            <option value="wave-subtle">Wave Subtle</option>
          </select>
        </div>
        <div>
          <Label htmlFor="bgpattern">Background Pattern</Label>
          <select id="bgpattern" className="w-full border rounded p-2 bg-background" value={bgPattern} onChange={e=>setBgPattern(e.target.value)}>
            <option value="gradient">Gradient</option>
            <option value="shapes">Shapes</option>
            <option value="grid">Grid</option>
            <option value="dots">Dots</option>
            <option value="wave">Wave</option>
            <option value="topography">Topography</option>
            <option value="hexagons">Hexagons</option>
            <option value="diagonal">Diagonal Lines</option>
            <option value="overlap">Overlapping Circles</option>
          </select>
        </div>
        <div>
          <Label htmlFor="typescale">Slide Type Scale</Label>
          <select id="typescale" className="w-full border rounded p-2 bg-background" value={typeScale} onChange={e=>setTypeScale(e.target.value)}>
            <option value="normal">Normal</option>
            <option value="large">Large</option>
          </select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="textmodel">Text/Chat Model</Label>
          <select id="textmodel" className="w-full border rounded p-2 bg-background" value={textModel} onChange={e=>setTextModel(e.target.value)}>
            <option value="googleai/gemini-2.5-flash">Gemini 2.5 Flash</option>
            <option value="googleai/gemini-2.0-flash">Gemini 2.0 Flash</option>
            <option value="googleai/gemini-1.5-flash">Gemini 1.5 Flash</option>
          </select>
        </div>
        <div>
          <Label htmlFor="imagemodel">Image Model</Label>
          <select id="imagemodel" className="w-full border rounded p-2 bg-background" value={imageModel} onChange={e=>setImageModel(e.target.value)}>
            <option value="googleai/gemini-2.5-flash-image-preview">Gemini 2.5 Flash Image Preview</option>
          </select>
        </div>
      </div>
      <div>
        <Label htmlFor="iconpack">Icon Pack</Label>
        <select id="iconpack" className="w-full border rounded p-2 bg-background" value={iconPack} onChange={e=>setIconPack(e.target.value)}>
          <option value="lucide">Lucide</option>
          <option value="tabler">Tabler</option>
          <option value="heroicons">Heroicons</option>
        </select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="headline-font">Headline Font</Label>
          <select id="headline-font" className="w-full border rounded p-2 bg-background" value={fontHeadline} onChange={e=>setFontHeadline(e.target.value)}>
            <option value="montserrat">Montserrat</option>
            <option value="inter">Inter</option>
            <option value="source">Source Sans 3</option>
            <option value="roboto">Roboto</option>
          </select>
        </div>
        <div>
          <Label htmlFor="body-font">Body Font</Label>
          <select id="body-font" className="w-full border rounded p-2 bg-background" value={fontBody} onChange={e=>setFontBody(e.target.value)}>
            <option value="roboto">Roboto</option>
            <option value="inter">Inter</option>
            <option value="source">Source Sans 3</option>
            <option value="montserrat">Montserrat</option>
          </select>
        </div>
      </div>
      <div className="flex gap-2 justify-end">
        <Button onClick={onSave}>Save</Button>
      </div>
      <div className="mt-6 border-t pt-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="font-medium">Web Search Cache</div>
            <div className="text-sm text-muted-foreground">ADK web search tool cache (dev)</div>
          </div>
          {searchLoading ? <div className="text-sm">Loading…</div> : null}
        </div>
        {searchError ? <div className="text-sm text-red-500 mb-2">{searchError}</div> : null}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="cache-enabled">Enable Cache</Label>
            <select id="cache-enabled" className="w-full border rounded p-2 bg-background" value={String(searchEnabled)} onChange={(e)=>setSearchEnabled(e.target.value === 'true')}>
              <option value="true">Enabled</option>
              <option value="false">Disabled</option>
            </select>
          </div>
          <div>
            <Label htmlFor="cache-ttl">Cache TTL (seconds)</Label>
            <Input id="cache-ttl" value={searchTtl} onChange={(e)=>setSearchTtl(e.target.value)} />
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          <Button variant="secondary" onClick={()=>applySearchCfg({ enabled: searchEnabled, cacheTtl: Number(searchTtl || '0') })}>Apply</Button>
          <Button variant="outline" onClick={()=>clearSearchCache(true)}>Clear Cache</Button>
        </div>
      </div>
      </div>
      
      <div className="mt-6 border-t pt-4">
        <div className="font-medium mb-2">Agent Models</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {Object.entries(models).map(([k, v]) => (
            <div key={k}>
              <Label className="text-xs text-muted-foreground">{k}</Label>
              <select className="w-full border rounded p-2 bg-background" value={v} onChange={e=> setModels(prev => ({ ...prev, [k]: e.target.value }))}>
                <option value="googleai/gemini-2.5-pro">Gemini 2.5 Pro</option>
                <option value="googleai/gemini-2.5-flash">Gemini 2.5 Flash</option>
                <option value="googleai/gemini-2.0-flash">Gemini 2.0 Flash</option>
                <option value="googleai/gemini-1.5-flash">Gemini 1.5 Flash</option>
                <option value="googleai/gemini-2.5-flash-image-preview">Gemini 2.5 Flash Image Preview</option>
              </select>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
