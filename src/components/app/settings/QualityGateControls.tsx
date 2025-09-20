'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Shield,
  Eye,
  Contrast,
  Sparkles,
  Settings2,
  CheckCircle2,
  AlertCircle,
  Zap,
  Palette,
  Target,
  Activity,
  RotateCcw,
  Save,
} from 'lucide-react'

export type QualityGateSettings = {
  enabled: boolean
  features: {
    placement: boolean
    saliency: boolean
    contrast: boolean
    blur: boolean
    brand: boolean
    ocr: boolean
  }
  thresholds: {
    minContrast: number
    maxBlur: number
    minSaliency: number
    placementConfidence: number
    brandConfidence: number
  }
  performance: {
    mode: 'fast' | 'balanced' | 'quality'
    parallelProcessing: boolean
    cacheResults: boolean
  }
}

const DEFAULT_SETTINGS: QualityGateSettings = {
  enabled: true,
  features: {
    placement: true,
    saliency: true,
    contrast: true,
    blur: false,
    brand: false,
    ocr: false,
  },
  thresholds: {
    minContrast: 4.5, // WCAG AA standard
    maxBlur: 0.3,
    minSaliency: 0.6,
    placementConfidence: 0.7,
    brandConfidence: 0.8,
  },
  performance: {
    mode: 'balanced',
    parallelProcessing: true,
    cacheResults: true,
  },
}

type QualityGateControlsProps = {
  onSettingsChange?: (settings: QualityGateSettings) => void
  className?: string
}

export default function QualityGateControls({
  onSettingsChange,
  className = '',
}: QualityGateControlsProps) {
  const [settings, setSettings] = useState<QualityGateSettings>(DEFAULT_SETTINGS)
  const [hasChanges, setHasChanges] = useState(false)

  // Load settings from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('qualityGateSettings')
      if (saved) {
        const parsed = JSON.parse(saved)
        setSettings({ ...DEFAULT_SETTINGS, ...parsed })
      }
    } catch (error) {
      console.error('Failed to load quality gate settings:', error)
    }
  }, [])

  // Update settings handler
  const updateSettings = useCallback(
    (updates: Partial<QualityGateSettings>) => {
      const newSettings = {
        ...settings,
        ...updates,
        features: { ...settings.features, ...(updates.features || {}) },
        thresholds: { ...settings.thresholds, ...(updates.thresholds || {}) },
        performance: { ...settings.performance, ...(updates.performance || {}) },
      }
      setSettings(newSettings)
      setHasChanges(true)

      if (onSettingsChange) {
        onSettingsChange(newSettings)
      }
    },
    [settings, onSettingsChange]
  )

  // Save settings to localStorage
  const saveSettings = useCallback(() => {
    try {
      localStorage.setItem('qualityGateSettings', JSON.stringify(settings))
      setHasChanges(false)
    } catch (error) {
      console.error('Failed to save quality gate settings:', error)
    }
  }, [settings])

  // Reset to defaults
  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS)
    setHasChanges(true)
  }, [])

  // Calculate enabled features count
  const enabledFeaturesCount = Object.values(settings.features).filter(Boolean).length
  const totalFeatures = Object.keys(settings.features).length

  return (
    <Card className={`${className} border-2 border-primary/20`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-primary" />
            <CardTitle className="text-xl font-headline">
              Visual Quality Gates
            </CardTitle>
            {settings.enabled ? (
              <Badge variant="default" className="flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Active
              </Badge>
            ) : (
              <Badge variant="secondary">Disabled</Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {enabledFeaturesCount}/{totalFeatures} features
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Activity className="h-3 w-3" />
              {settings.performance.mode}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Master Enable Switch */}
        <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
          <div className="space-y-1">
            <Label htmlFor="master-enable" className="text-base font-medium">
              Enable Quality Gates
            </Label>
            <p className="text-sm text-muted-foreground">
              Automatically check visual quality metrics during slide generation
            </p>
          </div>
          <Switch
            id="master-enable"
            checked={settings.enabled}
            onCheckedChange={(enabled) => updateSettings({ enabled })}
            className="scale-125"
          />
        </div>

        {settings.enabled && (
          <>
            <Separator />

            <Accordion type="single" collapsible defaultValue="features">
              {/* Feature Toggles */}
              <AccordionItem value="features">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Vision Features
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between">
                      <Label
                        htmlFor="feature-placement"
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <Target className="h-4 w-4 text-primary" />
                        Smart Placement
                      </Label>
                      <Switch
                        id="feature-placement"
                        checked={settings.features.placement}
                        onCheckedChange={(checked) =>
                          updateSettings({
                            features: { ...settings.features, placement: checked },
                          })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label
                        htmlFor="feature-saliency"
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <Eye className="h-4 w-4 text-primary" />
                        Saliency Detection
                      </Label>
                      <Switch
                        id="feature-saliency"
                        checked={settings.features.saliency}
                        onCheckedChange={(checked) =>
                          updateSettings({
                            features: { ...settings.features, saliency: checked },
                          })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label
                        htmlFor="feature-contrast"
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <Contrast className="h-4 w-4 text-primary" />
                        Contrast Check
                      </Label>
                      <Switch
                        id="feature-contrast"
                        checked={settings.features.contrast}
                        onCheckedChange={(checked) =>
                          updateSettings({
                            features: { ...settings.features, contrast: checked },
                          })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label
                        htmlFor="feature-blur"
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <Zap className="h-4 w-4 text-primary" />
                        Blur Detection
                      </Label>
                      <Switch
                        id="feature-blur"
                        checked={settings.features.blur}
                        onCheckedChange={(checked) =>
                          updateSettings({
                            features: { ...settings.features, blur: checked },
                          })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label
                        htmlFor="feature-brand"
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <Palette className="h-4 w-4 text-primary" />
                        Brand Validation
                      </Label>
                      <Switch
                        id="feature-brand"
                        checked={settings.features.brand}
                        onCheckedChange={(checked) =>
                          updateSettings({
                            features: { ...settings.features, brand: checked },
                          })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label
                        htmlFor="feature-ocr"
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <Settings2 className="h-4 w-4 text-primary" />
                        OCR Text Extraction
                      </Label>
                      <Switch
                        id="feature-ocr"
                        checked={settings.features.ocr}
                        onCheckedChange={(checked) =>
                          updateSettings({
                            features: { ...settings.features, ocr: checked },
                          })
                        }
                      />
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Quality Thresholds */}
              <AccordionItem value="thresholds">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Settings2 className="h-4 w-4" />
                    Quality Thresholds
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-6 pt-4">
                  {/* Contrast Threshold */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="flex items-center gap-2">
                        <Contrast className="h-4 w-4" />
                        Minimum Contrast Ratio
                      </Label>
                      <span className="text-sm font-mono text-muted-foreground">
                        {settings.thresholds.minContrast.toFixed(1)}:1
                      </span>
                    </div>
                    <Slider
                      value={[settings.thresholds.minContrast]}
                      onValueChange={([value]) =>
                        updateSettings({
                          thresholds: { ...settings.thresholds, minContrast: value },
                        })
                      }
                      min={3}
                      max={7}
                      step={0.1}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>AA Large (3:1)</span>
                      <span>AA (4.5:1)</span>
                      <span>AAA (7:1)</span>
                    </div>
                  </div>

                  {/* Blur Threshold */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        Maximum Blur Level
                      </Label>
                      <span className="text-sm font-mono text-muted-foreground">
                        {(settings.thresholds.maxBlur * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Slider
                      value={[settings.thresholds.maxBlur]}
                      onValueChange={([value]) =>
                        updateSettings({
                          thresholds: { ...settings.thresholds, maxBlur: value },
                        })
                      }
                      min={0.1}
                      max={0.5}
                      step={0.05}
                      className="w-full"
                    />
                  </div>

                  {/* Saliency Threshold */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="flex items-center gap-2">
                        <Eye className="h-4 w-4" />
                        Minimum Saliency Score
                      </Label>
                      <span className="text-sm font-mono text-muted-foreground">
                        {(settings.thresholds.minSaliency * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Slider
                      value={[settings.thresholds.minSaliency]}
                      onValueChange={([value]) =>
                        updateSettings({
                          thresholds: { ...settings.thresholds, minSaliency: value },
                        })
                      }
                      min={0.4}
                      max={0.9}
                      step={0.05}
                      className="w-full"
                    />
                  </div>

                  {/* Placement Confidence */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="flex items-center gap-2">
                        <Target className="h-4 w-4" />
                        Placement Confidence
                      </Label>
                      <span className="text-sm font-mono text-muted-foreground">
                        {(settings.thresholds.placementConfidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <Slider
                      value={[settings.thresholds.placementConfidence]}
                      onValueChange={([value]) =>
                        updateSettings({
                          thresholds: {
                            ...settings.thresholds,
                            placementConfidence: value,
                          },
                        })
                      }
                      min={0.5}
                      max={0.95}
                      step={0.05}
                      className="w-full"
                    />
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Performance Settings */}
              <AccordionItem value="performance">
                <AccordionTrigger>
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Performance
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-4">
                  <div className="space-y-2">
                    <Label>Processing Mode</Label>
                    <Select
                      value={settings.performance.mode}
                      onValueChange={(mode: 'fast' | 'balanced' | 'quality') =>
                        updateSettings({
                          performance: { ...settings.performance, mode },
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="fast">
                          <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4" />
                            Fast (Lower accuracy)
                          </div>
                        </SelectItem>
                        <SelectItem value="balanced">
                          <div className="flex items-center gap-2">
                            <Settings2 className="h-4 w-4" />
                            Balanced (Recommended)
                          </div>
                        </SelectItem>
                        <SelectItem value="quality">
                          <div className="flex items-center gap-2">
                            <Sparkles className="h-4 w-4" />
                            Quality (Higher accuracy)
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <Label
                      htmlFor="parallel-processing"
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      Parallel Processing
                    </Label>
                    <Switch
                      id="parallel-processing"
                      checked={settings.performance.parallelProcessing}
                      onCheckedChange={(checked) =>
                        updateSettings({
                          performance: {
                            ...settings.performance,
                            parallelProcessing: checked,
                          },
                        })
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label
                      htmlFor="cache-results"
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      Cache Results
                    </Label>
                    <Switch
                      id="cache-results"
                      checked={settings.performance.cacheResults}
                      onCheckedChange={(checked) =>
                        updateSettings({
                          performance: {
                            ...settings.performance,
                            cacheResults: checked,
                          },
                        })
                      }
                    />
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>

            {/* Info Alert */}
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>About Quality Gates</AlertTitle>
              <AlertDescription>
                Quality gates automatically check visual design metrics during slide
                generation. Failed checks will provide suggestions for improvement but
                won't block generation.
              </AlertDescription>
            </Alert>
          </>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={resetSettings}
            className="flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Reset to Defaults
          </Button>

          <Button
            variant={hasChanges ? 'default' : 'secondary'}
            size="sm"
            onClick={saveSettings}
            disabled={!hasChanges}
            className="flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {hasChanges ? 'Save Changes' : 'Saved'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// Export for type usage
export type { QualityGateSettings }