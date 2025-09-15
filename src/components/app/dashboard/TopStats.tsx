'use client'

import { useTokenMeter } from '@/hooks/use-token-meter'
import { usePresentationState } from '@/hooks/use-presentation-state'
import { cn } from '@/lib/utils'

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className={cn('flex-1 min-w-[160px] p-4 rounded-xl md-surface md-elevation-1 border')}
      aria-label={`${label}: ${value}`}
    >
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
      {hint ? <div className="text-[11px] text-muted-foreground mt-1">{hint}</div> : null}
    </div>
  )
}

export default function TopStats() {
  const { presentation } = usePresentationState()
  const totals = useTokenMeter()
  const slides = presentation.slides?.length || 0
  const assets = (presentation.initialInput?.files?.length || 0) + (presentation.initialInput?.styleFiles?.length || 0)
  const tokensIn = totals.tokensPrompt
  const tokensOut = totals.tokensCompletion
  const cost = `$${totals.usd.toFixed(4)}`

  return (
    <section className="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <StatCard label="Slides" value={slides} hint="Generated in current presentation" />
      <StatCard label="Assets" value={assets} hint="Uploaded files & style guides" />
      <StatCard label="Tokens (in/out)" value={`${tokensIn}/${tokensOut}`} hint="Prompt / Completion" />
      <StatCard label="Est. Cost" value={cost} hint="Configured in Settings" />
    </section>
  )
}

