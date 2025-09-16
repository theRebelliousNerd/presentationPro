'use client'

import { usePresentationStateArango as usePresentationState } from '@/hooks/use-presentation-state-arango'
import { useTokenMeter } from '@/hooks/use-token-meter'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Download } from 'lucide-react'
import { downloadScript, downloadPresentationHtml, downloadImages, downloadEverything, downloadPptx, exportServerHtml, exportServerPdf } from '@/lib/download'
import Link from 'next/link'

export default function TopBarCompact() {
  const { presentation } = usePresentationState()
  const totals = useTokenMeter()
  const slides = presentation.slides?.length || 0
  const assets = (presentation.initialInput?.files?.length || 0)
    + (presentation.initialInput?.styleFiles?.length || 0)
    + (presentation.initialInput?.graphicsFiles?.length || 0)
  const tokensIn = totals.tokensPrompt
  const tokensOut = totals.tokensCompletion
  const cost = `$${totals.usd.toFixed(4)}`

  // Breadcrumb-like inline status bar
  return (
    <div className="w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/75">
      <div className="px-3 md:px-4 py-2 text-sm text-muted-foreground flex items-center gap-3 overflow-x-auto justify-between">
        <div className="flex items-center gap-3">
          <span className="whitespace-nowrap"><span className="text-foreground/80">Slides</span>: {slides}</span>
          <span className="opacity-40">/</span>
          <span className="whitespace-nowrap"><span className="text-foreground/80">Assets</span>: {assets}</span>
          <span className="opacity-40">/</span>
          <span className="whitespace-nowrap"><span className="text-foreground/80">Tokens</span>: {tokensIn}/{tokensOut}</span>
          <span className="opacity-40">/</span>
          <span className="whitespace-nowrap"><span className="text-foreground/80">Cost</span>: {cost}</span>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/presentations" className="text-sm underline">Projects</Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" variant="outline"><Download className="h-4 w-4 mr-2"/>Downloads</Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-[200px]">
              <DropdownMenuItem onClick={() => downloadScript(presentation.slides)}>Download Script (.txt)</DropdownMenuItem>
              <DropdownMenuItem onClick={() => downloadPptx(presentation.slides)}>Export PowerPoint (.pptx)</DropdownMenuItem>
              <DropdownMenuItem onClick={() => downloadPresentationHtml(presentation.slides)}>Download HTML</DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportServerHtml(presentation)}>Export HTML (server)</DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportServerPdf(presentation)}>Export PDF (server)</DropdownMenuItem>
              <DropdownMenuItem onClick={() => downloadImages(presentation.slides)}>Download Images</DropdownMenuItem>
              <DropdownMenuItem onClick={() => downloadEverything(presentation.slides)}>Download Everything (ZIP)</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}
