'use client'

import { ReactNode, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import type { Presentation } from '@/lib/types'

export default function FormsPreviewDialog({ presentation, setPresentation, children }: { presentation: Presentation; setPresentation: (updater: (prev: Presentation)=>Presentation) => void; children: ReactNode }){
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(() => ({ ...presentation.initialInput }))

  const onOpenChange = (v: boolean) => {
    setOpen(v)
    if (v) setDraft({ ...presentation.initialInput })
  }

  const apply = () => {
    setPresentation(prev => ({ ...prev, initialInput: { ...prev.initialInput, ...draft } }))
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="max-w-[90vw] md:max-w-3xl h-[80vh] overflow-auto">
        <DialogHeader>
          <DialogTitle>Review Inferred Fields</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label>Objective</Label>
            <Input value={draft.objective || ''} onChange={e=> setDraft({ ...draft, objective: e.target.value })} />
          </div>
          <div>
            <Label>Audience</Label>
            <Input value={draft.audience || ''} onChange={e=> setDraft({ ...draft, audience: e.target.value })} />
          </div>
          <div>
            <Label>Call to Action</Label>
            <Input value={draft.callToAction || ''} onChange={e=> setDraft({ ...draft, callToAction: e.target.value })} />
          </div>
          <div>
            <Label>Time (min)</Label>
            <Input type="number" value={String(draft.timeConstraintMin || '')} onChange={e=> setDraft({ ...draft, timeConstraintMin: Number(e.target.value||'')||undefined })} />
          </div>
          <div className="md:col-span-2">
            <Label>Key Messages (one per line)</Label>
            <Textarea value={(draft.keyMessages||[]).join('\n')} onChange={e=> setDraft({ ...draft, keyMessages: e.target.value.split('\n').filter(Boolean) })} />
          </div>
          <div>
            <Label>Must Include</Label>
            <Textarea value={(draft.mustInclude||[]).join('\n')} onChange={e=> setDraft({ ...draft, mustInclude: e.target.value.split('\n').filter(Boolean) })} />
          </div>
          <div>
            <Label>Must Avoid</Label>
            <Textarea value={(draft.mustAvoid||[]).join('\n')} onChange={e=> setDraft({ ...draft, mustAvoid: e.target.value.split('\n').filter(Boolean) })} />
          </div>
          <div>
            <Label>Language</Label>
            <Input value={draft.language || ''} onChange={e=> setDraft({ ...draft, language: e.target.value })} />
          </div>
          <div>
            <Label>Locale</Label>
            <Input value={draft.locale || ''} onChange={e=> setDraft({ ...draft, locale: e.target.value })} />
          </div>
          <div>
            <Label>Slide Density</Label>
            <select className="w-full border rounded p-2 bg-background" value={draft.slideDensity || ''} onChange={e=> setDraft({ ...draft, slideDensity: (e.target.value||undefined) as any })}>
              <option value="">(default)</option>
              <option value="light">Light</option>
              <option value="normal">Normal</option>
              <option value="dense">Dense</option>
            </select>
          </div>
          <div>
            <Label>Brand Colors (comma)</Label>
            <Input value={(draft.brandColors||[]).join(', ')} onChange={e=> setDraft({ ...draft, brandColors: e.target.value.split(',').map(s=>s.trim()).filter(Boolean) })} />
          </div>
          <div>
            <Label>Allowed Sources (comma)</Label>
            <Input value={(draft.allowedSources||[]).join(', ')} onChange={e=> setDraft({ ...draft, allowedSources: e.target.value.split(',').map(s=>s.trim()).filter(Boolean) })} />
          </div>
          <div>
            <Label>Banned Sources (comma)</Label>
            <Input value={(draft.bannedSources||[]).join(', ')} onChange={e=> setDraft({ ...draft, bannedSources: e.target.value.split(',').map(s=>s.trim()).filter(Boolean) })} />
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" onClick={()=> setOpen(false)}>Cancel</Button>
          <Button onClick={apply}>Apply</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

