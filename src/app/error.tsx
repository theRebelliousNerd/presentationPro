'use client'

import { useEffect } from 'react'

export default function Error({ error, reset }: { error: Error & { digest?: string }, reset: () => void }) {
  useEffect(() => {
    // Log the error for diagnostics with full stack
    // eslint-disable-next-line no-console
    console.error('App error boundary:', error)
  }, [error])
  return (
    <div className="p-6">
      <div className="text-red-600 font-semibold mb-2">Something went wrong.</div>
      <div className="text-sm text-muted-foreground mb-4 break-words">
        {error?.message || 'Unknown error'}
      </div>
      {error?.stack ? (
        <pre className="text-xs bg-muted p-3 rounded max-h-64 overflow-auto whitespace-pre-wrap break-words">{error.stack}</pre>
      ) : null}
      <button className="mt-4 px-3 py-2 border rounded" onClick={() => reset()}>Reload</button>
    </div>
  )
}

