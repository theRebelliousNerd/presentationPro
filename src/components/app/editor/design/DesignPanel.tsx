import React from 'react'
import type { Slide } from '@/lib/types'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import VariantPicker from './VariantPicker'
import TokenEditor from './TokenEditor'
import DesignLayers from './DesignLayers'
import CodeEditor from './CodeEditor'
import { Button } from '@/components/ui/button'

type DesignPanelProps = {
  slide: Slide
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void
  applyTokensToAll?: (tokens: any) => void
}

export default function DesignPanel({ slide, updateSlide, applyTokensToAll }: DesignPanelProps) {
  return (
    <div className="border rounded-md p-3">
      <div className="font-medium mb-2">Design</div>
      <div className="flex items-center justify-end mb-2">
        <Button size="sm" variant="secondary" onClick={()=>{
          try { window.dispatchEvent(new CustomEvent('slides:bakeImage', { detail: { slideId: slide.id } })) } catch {}
        }}>Bake to Image</Button>
      </div>
      <Tabs defaultValue="variants">
        <TabsList>
          <TabsTrigger value="variants">Variants</TabsTrigger>
          <TabsTrigger value="tokens">Tokens</TabsTrigger>
          <TabsTrigger value="layers">Layers</TabsTrigger>
          <TabsTrigger value="code">Code</TabsTrigger>
        </TabsList>
        <TabsContent value="variants">
          <VariantPicker slide={slide} updateSlide={updateSlide} />
        </TabsContent>
        <TabsContent value="tokens">
          <TokenEditor slide={slide} updateSlide={updateSlide} onApplyToAll={applyTokensToAll} />
        </TabsContent>
        <TabsContent value="layers">
          <DesignLayers slide={slide} />
        </TabsContent>
        <TabsContent value="code">
          <CodeEditor slide={slide} updateSlide={updateSlide} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
