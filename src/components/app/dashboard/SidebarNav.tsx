'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Home, Presentation, BookText, Settings as SettingsIcon, PanelLeftOpen, PanelLeftClose, Wrench, GitBranch } from 'lucide-react'
import SettingsDialog from '@/components/app/SettingsDialog'
import { useEffect, useState } from 'react'

type NavItem = {
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

const items: NavItem[] = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/presentations', label: 'Presentations', icon: Presentation },
  { href: '/dev/search-cache', label: 'Research', icon: BookText },
  { href: '/dev', label: 'Dev UI', icon: Wrench },
  // Settings handled via modal, not navigation
]

export default function SidebarNav() {
  const pathname = usePathname()
  const [activePanel, setActivePanel] = useState<null | 'chat' | 'reviews' | 'workflow'>(null)
  const [slidesCollapsed, setSlidesCollapsed] = useState<boolean>(false)
  useEffect(() => {
    const onState = (e: any) => {
      const detail = e?.detail || {}
      setActivePanel((detail.panel as any) || null)
    }
    window.addEventListener('panel:state', onState as any)
    return () => window.removeEventListener('panel:state', onState as any)
  }, [])
  useEffect(() => {
    const onSlidesState = (e: any) => {
      const col = !!(e?.detail?.collapsed)
      setSlidesCollapsed(col)
    }
    window.addEventListener('slides:state', onSlidesState as any)
    return () => window.removeEventListener('slides:state', onSlidesState as any)
  }, [])
  return (
    <aside className="hidden lg:flex fixed left-0 top-16 bottom-0 w-16 flex-col items-center gap-4 py-4 border-r bg-card md-surface md-elevation-2 z-30">
      {items.map((it) => {
        const Icon = it.icon
        const isRoot = it.href === '/'
        const active = isRoot ? pathname === it.href : (pathname === it.href || pathname.startsWith(`${it.href}/`))
        return (
          <Link key={it.href} href={it.href} className={cn('flex flex-col items-center gap-1 text-xs px-2 py-1 rounded-md hover:bg-muted transition', active && 'bg-muted text-primary')}
            title={it.label}
            aria-label={it.label}
          >
            <Icon className="h-5 w-5" />
            <span className="hidden xl:block">{it.label}</span>
          </Link>
        )
      })}
      <button
        className={cn('flex flex-col items-center gap-1 text-xs px-2 py-1 rounded-md hover:bg-muted transition')}
        title="Slides"
        aria-label="Slides"
        onClick={()=>{ try { window.dispatchEvent(new CustomEvent('slides:toggle')) } catch {} }}
      >
        {slidesCollapsed ? (
          <PanelLeftOpen className="h-5 w-5" />
        ) : (
          <PanelLeftClose className="h-5 w-5" />
        )}
        <span className="hidden xl:block">Slides</span>
      </button>
      <button
        className={cn('flex flex-col items-center gap-1 text-xs px-2 py-1 rounded-md hover:bg-muted transition', activePanel==='chat' && 'bg-muted text-primary')}
        title="Show Chat"
        aria-label="Show Chat"
        onClick={()=>{
          try { window.dispatchEvent(new CustomEvent('panel:toggle', { detail: { panel: 'chat' } })) } catch {}
        }}
      >
        <span className="relative inline-flex items-center justify-center h-5 w-5 rounded bg-muted">
          {/* chat icon */}
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a4 4 0 0 1-4 4H7l-4 4V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/></svg>
          {activePanel==='chat' ? (
            <span className="absolute -right-1 -top-1 h-4 w-4 text-[10px] rounded-full bg-destructive text-destructive-foreground flex items-center justify-center" onClick={(e)=>{ e.stopPropagation(); try { window.dispatchEvent(new CustomEvent('panel:toggle', { detail: { panel: 'chat' } })) } catch {} }}>x</span>
          ) : null}
        </span>
        <span className="hidden xl:block">Chat</span>
      </button>
      <button
        className={cn('flex flex-col items-center gap-1 text-xs px-2 py-1 rounded-md hover:bg-muted transition', activePanel==='workflow' && 'bg-muted text-primary')}
        title="Workflow"
        aria-label="Workflow"
        onClick={()=>{
          try { window.dispatchEvent(new CustomEvent('panel:toggle', { detail: { panel: 'workflow' } })) } catch {}
        }}
      >
        <span className="relative inline-flex items-center justify-center h-5 w-5 rounded bg-muted">
          <GitBranch className="h-4 w-4" />
          {activePanel==='workflow' ? (
            <span className="absolute -right-1 -top-1 h-4 w-4 text-[10px] rounded-full bg-destructive text-destructive-foreground flex items-center justify-center" onClick={(e)=>{ e.stopPropagation(); try { window.dispatchEvent(new CustomEvent('panel:toggle', { detail: { panel: 'workflow' } })) } catch {} }}>x</span>
          ) : null}
        </span>
        <span className="hidden xl:block">Workflow</span>
      </button>
      <button
        className={cn('flex flex-col items-center gap-1 text-xs px-2 py-1 rounded-md hover:bg-muted transition', activePanel==='reviews' && 'bg-muted text-primary')}
        title="Reviews"
        aria-label="Reviews"
        onClick={()=>{
          try { window.dispatchEvent(new CustomEvent('panel:toggle', { detail: { panel: 'reviews' } })) } catch {}
        }}
      >
        <span className="relative inline-flex items-center justify-center h-5 w-5 rounded bg-muted">
          {/* reviews icon */}
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
          {/* Review count badge */}
          <ReviewsBadge />
          {activePanel==='reviews' ? (
            <span className="absolute -right-1 -top-1 h-4 w-4 text-[10px] rounded-full bg-destructive text-destructive-foreground flex items-center justify-center" onClick={(e)=>{ e.stopPropagation(); try { window.dispatchEvent(new CustomEvent('panel:toggle', { detail: { panel: 'reviews' } })) } catch {} }}>x</span>
          ) : null}
        </span>
        <span className="hidden xl:block">Reviews</span>
      </button>
      <SettingsDialog>
        <button className={cn('flex flex-col items-center gap-1 text-xs px-2 py-1 rounded-md hover:bg-muted transition')}
          title="Settings"
          aria-label="Settings"
        >
          <SettingsIcon className="h-5 w-5" />
          <span className="hidden xl:block">Settings</span>
        </button>
      </SettingsDialog>
    </aside>
  )
}

function ReviewsBadge(){
  const [count, setCount] = useState<number>(0)
  useEffect(() => {
    const onCount = (e: any) => {
      const n = (e?.detail?.count as number) || 0
      setCount(n)
    }
    window.addEventListener('panel:reviewsCount', onCount as any)
    return () => window.removeEventListener('panel:reviewsCount', onCount as any)
  }, [])
  if (!count) return null
  return (
    <span className="absolute -right-1 -bottom-1 h-4 min-w-4 px-1 text-[10px] rounded-full bg-primary text-primary-foreground flex items-center justify-center">{count}</span>
  )
}
