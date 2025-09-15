'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Home, Presentation, BookText, Settings } from 'lucide-react'

type NavItem = {
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

const items: NavItem[] = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/presentations', label: 'Presentations', icon: Presentation },
  { href: '/dev/search-cache', label: 'Research', icon: BookText },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export default function SidebarNav() {
  const pathname = usePathname()
  return (
    <aside className="hidden lg:flex fixed left-0 top-16 bottom-0 w-16 flex-col items-center gap-4 py-4 border-r bg-card md-surface md-elevation-2 z-30">
      {items.map((it) => {
        const Icon = it.icon
        const active = pathname === it.href
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
    </aside>
  )
}

