'use client'

import { ReactNode, useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import SettingsPanel from '@/components/app/SettingsPanel'

export default function SettingsDialog({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="w-[96vw] sm:max-w-[80vw] lg:max-w-[65vw] max-h-[85vh] overflow-y-auto" aria-describedby="settings-dialog-description">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription id="settings-dialog-description">Adjust pricing, AI models, preferences, and developer options for this workspace.</DialogDescription>
        </DialogHeader>
        <SettingsPanel />
      </DialogContent>
    </Dialog>
  )
}
