'use client'

import SettingsPanel from '@/components/app/SettingsPanel'

export default function SettingsPage() {
  return (
    <main className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Settings</h1>
      <SettingsPanel />
    </main>
  )
}

