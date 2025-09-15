'use client'

import { useEffect, useState } from 'react'
import { useSearchCache } from '@/hooks/use-search-cache'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export default function SearchCacheDevPage() {
  const { config, loading, error, apply, clear, load } = useSearchCache()
  const [enabled, setEnabled] = useState(true)
  const [ttl, setTtl] = useState('3600')

  useEffect(() => {
    if (!config && !loading) load()
  }, [config, loading, load])

  useEffect(() => {
    if (config) {
      setEnabled(!!config.enabled)
      setTtl(String(config.cacheTtl || 0))
    }
  }, [config])

  return (
    <main className="max-w-2xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>Web Search Cache</CardTitle>
          <CardDescription>Configure ADK web search caching (dev only)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error ? <div className="text-red-500 text-sm">{error}</div> : null}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Enabled</Label>
              <select className="w-full border rounded p-2 bg-background" value={String(enabled)} onChange={e => setEnabled(e.target.value === 'true')}>
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
            </div>
            <div>
              <Label>TTL (seconds)</Label>
              <Input value={ttl} onChange={e => setTtl(e.target.value)} />
            </div>
          </div>
          <div className="flex gap-2">
            <Button disabled={loading} onClick={() => apply({ enabled, cacheTtl: Number(ttl || '0') })}>Apply</Button>
            <Button disabled={loading} variant="outline" onClick={() => clear(true)}>Clear Cache</Button>
          </div>
          {loading ? <div className="text-sm text-muted-foreground">Loading…</div> : null}
        </CardContent>
      </Card>
    </main>
  )
}

