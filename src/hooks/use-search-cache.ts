'use client'

import { useCallback, useEffect, useState } from 'react'
import { orchSearchCacheConfig, orchSearchCacheClear } from '@/lib/orchestrator'

type Config = { enabled: boolean; cacheTtl: number }

export function useSearchCache() {
  const [config, setConfig] = useState<Config | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const cfg = await orchSearchCacheConfig({}) as any
      setConfig({ enabled: !!cfg.enabled, cacheTtl: Number(cfg.cacheTtl || 0) })
    } catch (e: any) {
      setError(e?.message || 'Failed to load search cache config')
    } finally {
      setLoading(false)
    }
  }, [])

  const apply = useCallback(async (next: Partial<Config>) => {
    setLoading(true)
    setError(null)
    try {
      const cfg = await orchSearchCacheConfig({ enabled: next.enabled, cacheTtl: next.cacheTtl }) as any
      setConfig({ enabled: !!cfg.enabled, cacheTtl: Number(cfg.cacheTtl || 0) })
    } catch (e: any) {
      setError(e?.message || 'Failed to update search cache config')
    } finally {
      setLoading(false)
    }
  }, [])

  const clear = useCallback(async (deleteFile = true) => {
    setLoading(true)
    setError(null)
    try {
      await orchSearchCacheClear({ deleteFile })
    } catch (e: any) {
      setError(e?.message || 'Failed to clear search cache')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // lazy load on first use
    if (config == null && !loading) {
      load()
    }
  }, [config, loading, load])

  return { config, loading, error, load, apply, clear }
}

