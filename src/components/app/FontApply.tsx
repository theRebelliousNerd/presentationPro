'use client'

import { useEffect } from 'react'

const VARS: Record<string,string> = {
  roboto: 'var(--font-roboto)',
  montserrat: 'var(--font-montserrat)',
  inter: 'var(--font-inter)',
  source: 'var(--font-source)'
}

export default function FontApply(){
  useEffect(() => {
    const apply = () => {
      try {
        const bodyFont = (localStorage.getItem('app.font.body') || 'roboto').toLowerCase()
        const headlineFont = (localStorage.getItem('app.font.headline') || 'montserrat').toLowerCase()
        const root = document.documentElement
        root.style.setProperty('--font-body', VARS[bodyFont] || VARS.roboto)
        root.style.setProperty('--font-headline', VARS[headlineFont] || VARS.montserrat)
      } catch {}
    }
    apply()
    const onChange = () => apply()
    window.addEventListener('settings:changed', onChange)
    window.addEventListener('storage', onChange)
    return () => {
      window.removeEventListener('settings:changed', onChange)
      window.removeEventListener('storage', onChange)
    }
  }, [])
  return null
}
