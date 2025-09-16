'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function ProjectSwitcher({ params }: { params: { id: string } }) {
  const router = useRouter()
  useEffect(() => {
    try { localStorage.setItem('presentationId', params.id) } catch {}
    router.push('/')
  }, [params?.id])
  return null
}

