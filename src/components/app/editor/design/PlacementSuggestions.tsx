'use client'

import React, { useState, useCallback, useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Grid3x3,
  Move,
  Crosshair,
  Maximize2,
  Eye,
  EyeOff,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Target,
  Layers,
  Ruler,
} from 'lucide-react'
import type { Slide } from '@/lib/types'

type PlacementCandidate = {
  bounding_box?: { x?: number; y?: number; width?: number; height?: number }
  score?: number
  mean_saliency?: number
  thirds_distance?: number
  area?: number
}

type PlacementSuggestionsProps = {
  slide: Slide
  updateSlide: (slideId: string, updatedProps: Partial<Slide>) => void
  onApplyPlacement?: (placement: PlacementCandidate) => void
}

// Golden ratio constant
const PHI = 1.618033988749895

export default function PlacementSuggestions({
  slide,
  updateSlide,
  onApplyPlacement,
}: PlacementSuggestionsProps) {
  const [showRuleOfThirds, setShowRuleOfThirds] = useState(true)
  const [showGoldenRatio, setShowGoldenRatio] = useState(false)
  const [showSaliencyMap, setShowSaliencyMap] = useState(false)
  const [selectedPlacement, setSelectedPlacement] = useState<number | null>(null)
  const [confidenceThreshold, setConfidenceThreshold] = useState([0.7])

  const candidates = useMemo(() => {
    const raw = slide.designSpec?.placementCandidates || []
    return raw
      .filter((c) => (c.score || 0) >= confidenceThreshold[0])
      .sort((a, b) => (b.score || 0) - (a.score || 0))
  }, [slide.designSpec?.placementCandidates, confidenceThreshold])

  const frameSize = useMemo(() => {
    const frame = slide.designSpec?.placementFrame
    return {
      width: frame?.width || 1280,
      height: frame?.height || 720,
    }
  }, [slide.designSpec?.placementFrame])

  const handleApplyPlacement = useCallback(
    (candidate: PlacementCandidate, index: number) => {
      setSelectedPlacement(index)

      // Update slide with placement information
      updateSlide(slide.id, {
        designSpec: {
          ...slide.designSpec,
          selectedPlacement: index,
          appliedPlacement: candidate,
        },
      })

      // Callback for parent component
      if (onApplyPlacement) {
        onApplyPlacement(candidate)
      }
    },
    [slide.id, slide.designSpec, updateSlide, onApplyPlacement]
  )

  const getPlacementQuality = (score: number): {
    label: string
    color: 'destructive' | 'warning' | 'default' | 'success'
    icon: React.ReactNode
  } => {
    if (score >= 0.9) {
      return {
        label: 'Excellent',
        color: 'success',
        icon: <CheckCircle2 className="h-3 w-3" />,
      }
    } else if (score >= 0.75) {
      return {
        label: 'Good',
        color: 'default',
        icon: <Target className="h-3 w-3" />,
      }
    } else if (score >= 0.6) {
      return {
        label: 'Fair',
        color: 'warning',
        icon: <AlertCircle className="h-3 w-3" />,
      }
    }
    return {
      label: 'Poor',
      color: 'destructive',
      icon: <AlertCircle className="h-3 w-3" />,
    }
  }

  const renderCompositionGrid = useCallback(() => {
    const { width, height } = frameSize
    const thirdWidth = width / 3
    const thirdHeight = height / 3

    // Golden ratio divisions
    const goldenWidth = width / PHI
    const goldenHeight = height / PHI

    return (
      <svg
        className="absolute inset-0 pointer-events-none"
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: '100%' }}
      >
        {/* Rule of Thirds */}
        {showRuleOfThirds && (
          <g stroke="#73BF50" strokeWidth="1" opacity="0.5">
            <line x1={thirdWidth} y1="0" x2={thirdWidth} y2={height} />
            <line x1={thirdWidth * 2} y1="0" x2={thirdWidth * 2} y2={height} />
            <line x1="0" y1={thirdHeight} x2={width} y2={thirdHeight} />
            <line x1="0" y1={thirdHeight * 2} x2={width} y2={thirdHeight * 2} />

            {/* Power points */}
            <circle cx={thirdWidth} cy={thirdHeight} r="8" fill="#73BF50" opacity="0.8" />
            <circle cx={thirdWidth * 2} cy={thirdHeight} r="8" fill="#73BF50" opacity="0.8" />
            <circle cx={thirdWidth} cy={thirdHeight * 2} r="8" fill="#73BF50" opacity="0.8" />
            <circle cx={thirdWidth * 2} cy={thirdHeight * 2} r="8" fill="#73BF50" opacity="0.8" />
          </g>
        )}

        {/* Golden Ratio */}
        {showGoldenRatio && (
          <g stroke="#F9AC14" strokeWidth="1" opacity="0.4" strokeDasharray="4 2">
            <line x1={goldenWidth} y1="0" x2={goldenWidth} y2={height} />
            <line x1={width - goldenWidth} y1="0" x2={width - goldenWidth} y2={height} />
            <line x1="0" y1={goldenHeight} x2={width} y2={goldenHeight} />
            <line x1="0" y1={height - goldenHeight} x2={width} y2={height - goldenHeight} />

            {/* Golden spiral hint */}
            <rect
              x={0}
              y={0}
              width={goldenWidth}
              height={goldenHeight}
              fill="none"
              stroke="#F9AC14"
              strokeWidth="2"
              opacity="0.3"
            />
          </g>
        )}

        {/* Placement candidates */}
        {candidates.map((candidate, index) => {
          const bbox = candidate.bounding_box
          if (!bbox?.x || !bbox?.y || !bbox?.width || !bbox?.height) return null

          const isSelected = selectedPlacement === index
          const quality = getPlacementQuality(candidate.score || 0)

          return (
            <g key={index}>
              <rect
                x={bbox.x}
                y={bbox.y}
                width={bbox.width}
                height={bbox.height}
                fill={isSelected ? '#73BF50' : '#556273'}
                fillOpacity={isSelected ? 0.2 : 0.1}
                stroke={isSelected ? '#73BF50' : '#556273'}
                strokeWidth={isSelected ? 2 : 1}
                strokeDasharray={isSelected ? '0' : '4 4'}
                className="cursor-pointer transition-all duration-200 hover:fill-opacity-30"
                onClick={() => handleApplyPlacement(candidate, index)}
              />

              {/* Score indicator */}
              <text
                x={bbox.x + bbox.width / 2}
                y={bbox.y + bbox.height / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                fill={isSelected ? '#73BF50' : '#556273'}
                fontSize="12"
                fontWeight="bold"
                className="pointer-events-none"
              >
                {(candidate.score || 0).toFixed(2)}
              </text>
            </g>
          )
        })}
      </svg>
    )
  }, [
    frameSize,
    showRuleOfThirds,
    showGoldenRatio,
    candidates,
    selectedPlacement,
    handleApplyPlacement,
  ])

  if (!slide.designSpec?.placementCandidates?.length) {
    return null
  }

  return (
    <Card className="p-4 space-y-4 border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Crosshair className="h-5 w-5 text-primary" />
          <h3 className="font-headline font-semibold text-lg">
            Visual Composition Assistant
          </h3>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Sparkles className="h-4 w-4 text-primary animate-pulse" />
              </TooltipTrigger>
              <TooltipContent>
                <p>AI-powered placement suggestions based on visual design principles</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <Badge variant="secondary" className="flex items-center gap-1">
          <Layers className="h-3 w-3" />
          {candidates.length} suggestions
        </Badge>
      </div>

      {/* Composition Grid Controls */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div className="flex items-center gap-2">
          <Switch
            id="rule-of-thirds"
            checked={showRuleOfThirds}
            onCheckedChange={setShowRuleOfThirds}
          />
          <Label
            htmlFor="rule-of-thirds"
            className="flex items-center gap-1 cursor-pointer"
          >
            <Grid3x3 className="h-4 w-4 text-primary" />
            Rule of Thirds
          </Label>
        </div>

        <div className="flex items-center gap-2">
          <Switch
            id="golden-ratio"
            checked={showGoldenRatio}
            onCheckedChange={setShowGoldenRatio}
          />
          <Label
            htmlFor="golden-ratio"
            className="flex items-center gap-1 cursor-pointer"
          >
            <Maximize2 className="h-4 w-4 text-[#F9AC14]" />
            Golden Ratio
          </Label>
        </div>

        <div className="flex items-center gap-2">
          <Switch
            id="saliency-map"
            checked={showSaliencyMap}
            onCheckedChange={setShowSaliencyMap}
          />
          <Label
            htmlFor="saliency-map"
            className="flex items-center gap-1 cursor-pointer"
          >
            {showSaliencyMap ? (
              <Eye className="h-4 w-4 text-secondary" />
            ) : (
              <EyeOff className="h-4 w-4 text-muted-foreground" />
            )}
            Saliency Map
          </Label>
        </div>
      </div>

      {/* Confidence Threshold */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Confidence Threshold
          </Label>
          <span className="text-sm font-mono text-muted-foreground">
            {(confidenceThreshold[0] * 100).toFixed(0)}%
          </span>
        </div>
        <Slider
          value={confidenceThreshold}
          onValueChange={setConfidenceThreshold}
          min={0.5}
          max={1}
          step={0.05}
          className="w-full"
        />
      </div>

      {/* Visual Preview */}
      <div className="relative bg-muted/20 rounded-lg overflow-hidden" style={{
        aspectRatio: `${frameSize.width} / ${frameSize.height}`,
      }}>
        {renderCompositionGrid()}
      </div>

      {/* Placement Candidates List */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Move className="h-4 w-4" />
          Placement Options
        </Label>

        <div className="grid gap-2">
          {candidates.slice(0, 4).map((candidate, index) => {
            const quality = getPlacementQuality(candidate.score || 0)
            const isSelected = selectedPlacement === index
            const bbox = candidate.bounding_box

            return (
              <Card
                key={index}
                className={`p-3 cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? 'border-primary bg-primary/10 shadow-lg'
                    : 'hover:border-primary/50 hover:bg-muted/50'
                }`}
                onClick={() => handleApplyPlacement(candidate, index)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex flex-col items-center">
                      <Badge variant={quality.color} className="flex items-center gap-1">
                        {quality.icon}
                        {quality.label}
                      </Badge>
                      <span className="text-2xl font-bold font-mono mt-1">
                        {(candidate.score || 0).toFixed(2)}
                      </span>
                    </div>

                    <div className="flex flex-col gap-1 text-sm">
                      <div className="flex items-center gap-2">
                        <Ruler className="h-3 w-3 text-muted-foreground" />
                        <span className="font-mono text-xs">
                          {bbox?.width && bbox?.height
                            ? `${Math.round(bbox.width)}×${Math.round(bbox.height)}`
                            : '—'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Target className="h-3 w-3 text-muted-foreground" />
                        <span className="font-mono text-xs">
                          Position: {bbox?.x && bbox?.y
                            ? `${Math.round(bbox.x)}, ${Math.round(bbox.y)}`
                            : '—'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1 text-right">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="text-xs text-muted-foreground">
                            Saliency: {((candidate.mean_saliency || 0) * 100).toFixed(0)}%
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Visual attention score in this region</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="text-xs text-muted-foreground">
                            Thirds: {((1 - (candidate.thirds_distance || 0)) * 100).toFixed(0)}%
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Alignment with rule of thirds grid</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>

                  {isSelected && (
                    <CheckCircle2 className="h-5 w-5 text-primary animate-smooth" />
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Apply Button */}
      <Button
        className="w-full"
        variant={selectedPlacement !== null ? 'default' : 'outline'}
        disabled={selectedPlacement === null}
        onClick={() => {
          if (selectedPlacement !== null && candidates[selectedPlacement]) {
            // Trigger visual feedback
            window.dispatchEvent(
              new CustomEvent('placement:applied', {
                detail: {
                  slideId: slide.id,
                  placement: candidates[selectedPlacement],
                },
              })
            )
          }
        }}
      >
        <Sparkles className="h-4 w-4 mr-2" />
        {selectedPlacement !== null
          ? 'Apply Selected Placement'
          : 'Select a Placement Option'}
      </Button>
    </Card>
  )
}