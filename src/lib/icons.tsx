import React from 'react'
import { Lightbulb, Check, ChartBar, ImageIcon } from 'lucide-react'
import { IconBulb, IconCheck, IconChartBar as TablerChartBar, IconPhoto } from '@tabler/icons-react'
import { LightBulbIcon, CheckIcon, ChartBarIcon, PhotoIcon } from '@heroicons/react/24/outline'

export type IconPack = 'lucide' | 'tabler' | 'heroicons'

export function getIconPack(): IconPack {
  if (typeof window === 'undefined') return 'lucide'
  try { return (localStorage.getItem('app.iconPack') as IconPack) || 'lucide' } catch { return 'lucide' }
}

export function RenderIcon({ name, className }: { name: 'lightbulb' | 'check' | 'chart' | 'image'; className?: string }) {
  const pack = getIconPack()
  if (pack === 'tabler') {
    switch(name){
      case 'lightbulb': return <IconBulb className={className} />
      case 'check': return <IconCheck className={className} />
      case 'chart': return <TablerChartBar className={className} />
      case 'image': return <IconPhoto className={className} />
    }
  } else if (pack === 'heroicons') {
    switch(name){
      case 'lightbulb': return <LightBulbIcon className={className} />
      case 'check': return <CheckIcon className={className} />
      case 'chart': return <ChartBarIcon className={className} />
      case 'image': return <PhotoIcon className={className} />
    }
  }
  // default lucide
  switch(name){
    case 'lightbulb': return <Lightbulb className={className} />
    case 'check': return <Check className={className} />
    case 'chart': return <ChartBar className={className} />
    case 'image': return <ImageIcon className={className} />
  }
}

