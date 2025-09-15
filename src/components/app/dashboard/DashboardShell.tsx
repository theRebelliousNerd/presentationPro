'use client'

import { ReactNode } from 'react'
import SidebarNav from './SidebarNav'

export default function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen w-full">
      {/* Left rail nav */}
      <SidebarNav />
      {/* Content shifted to accommodate left rail on large screens */}
      <div className="lg:pl-16">{children}</div>
    </div>
  )
}

