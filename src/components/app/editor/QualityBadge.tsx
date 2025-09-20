'use client'

import React, { useMemo } from 'react'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  AlertTriangle,
  Eye,
  Contrast,
  Zap,
  Palette,
  Target,
  Sparkles,
  TrendingUp,
  Shield,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export type QualityMetrics = {
  overall?: number // 0-100 overall quality score
  contrast?: {
    score: number
    ratio: number
    passes: boolean
    level?: 'AA' | 'AAA' | 'AA-large'
  }
  blur?: {
    score: number
    level: number
    passes: boolean
  }
  saliency?: {
    score: number
    hotspots: number
    distribution: 'concentrated' | 'balanced' | 'scattered'
  }
  brand?: {
    score: number
    violations: string[]
    passes: boolean
  }
  placement?: {
    score: number
    confidence: number
    suggestions: number
  }
}

type QualityBadgeProps = {
  metrics?: QualityMetrics
  variant?: 'compact' | 'detailed' | 'inline'
  showImprovements?: boolean
  className?: string
}

export default function QualityBadge({
  metrics,
  variant = 'compact',
  showImprovements = true,
  className = '',
}: QualityBadgeProps) {
  // Calculate overall status
  const overallStatus = useMemo(() => {
    if (!metrics?.overall) return 'unknown'
    if (metrics.overall >= 90) return 'excellent'
    if (metrics.overall >= 75) return 'good'
    if (metrics.overall >= 60) return 'fair'
    return 'poor'
  }, [metrics?.overall])

  // Get status color and icon
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'excellent':
        return {
          color: 'success' as const,
          icon: <CheckCircle2 className="h-4 w-4" />,
          label: 'Excellent',
          bgColor: 'bg-green-500/10',
          borderColor: 'border-green-500/20',
          textColor: 'text-green-600 dark:text-green-400',
        }
      case 'good':
        return {
          color: 'default' as const,
          icon: <CheckCircle2 className="h-4 w-4" />,
          label: 'Good',
          bgColor: 'bg-primary/10',
          borderColor: 'border-primary/20',
          textColor: 'text-primary',
        }
      case 'fair':
        return {
          color: 'warning' as const,
          icon: <AlertCircle className="h-4 w-4" />,
          label: 'Fair',
          bgColor: 'bg-yellow-500/10',
          borderColor: 'border-yellow-500/20',
          textColor: 'text-yellow-600 dark:text-yellow-400',
        }
      case 'poor':
        return {
          color: 'destructive' as const,
          icon: <AlertTriangle className="h-4 w-4" />,
          label: 'Needs Work',
          bgColor: 'bg-red-500/10',
          borderColor: 'border-red-500/20',
          textColor: 'text-red-600 dark:text-red-400',
        }
      default:
        return {
          color: 'secondary' as const,
          icon: <Shield className="h-4 w-4" />,
          label: 'Analyzing',
          bgColor: 'bg-muted',
          borderColor: 'border-muted',
          textColor: 'text-muted-foreground',
        }
    }
  }

  const statusConfig = getStatusConfig(overallStatus)

  // Generate improvement suggestions
  const improvements = useMemo(() => {
    const suggestions: { icon: React.ReactNode; text: string; priority: 'high' | 'medium' | 'low' }[] = []

    if (metrics?.contrast && !metrics.contrast.passes) {
      suggestions.push({
        icon: <Contrast className="h-4 w-4" />,
        text: `Increase contrast ratio to ${metrics.contrast.level === 'AAA' ? '7:1' : '4.5:1'}`,
        priority: 'high',
      })
    }

    if (metrics?.blur && !metrics.blur.passes) {
      suggestions.push({
        icon: <Zap className="h-4 w-4" />,
        text: 'Reduce image blur or use sharper assets',
        priority: 'high',
      })
    }

    if (metrics?.saliency && metrics.saliency.distribution === 'scattered') {
      suggestions.push({
        icon: <Eye className="h-4 w-4" />,
        text: 'Consolidate visual focus points',
        priority: 'medium',
      })
    }

    if (metrics?.brand && metrics.brand.violations.length > 0) {
      suggestions.push({
        icon: <Palette className="h-4 w-4" />,
        text: `Fix ${metrics.brand.violations.length} brand guideline violations`,
        priority: 'medium',
      })
    }

    if (metrics?.placement && metrics.placement.confidence < 0.7) {
      suggestions.push({
        icon: <Target className="h-4 w-4" />,
        text: 'Consider alternative element placements',
        priority: 'low',
      })
    }

    return suggestions
  }, [metrics])

  // Inline variant
  if (variant === 'inline') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant={statusConfig.color}
              className={cn('flex items-center gap-1.5 cursor-help', className)}
            >
              {statusConfig.icon}
              <span className="font-mono text-xs">
                {metrics?.overall ? `${metrics.overall}%` : '—'}
              </span>
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <p className="font-medium">Visual Quality Score</p>
              <p className="text-xs text-muted-foreground">{statusConfig.label}</p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  // Compact variant
  if (variant === 'compact') {
    return (
      <div
        className={cn(
          'flex items-center gap-3 p-3 rounded-lg border-2',
          statusConfig.bgColor,
          statusConfig.borderColor,
          className
        )}
      >
        <div className={cn('p-2 rounded-full', statusConfig.bgColor)}>
          {statusConfig.icon}
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={cn('font-medium', statusConfig.textColor)}>
              Quality Score
            </span>
            <Badge variant={statusConfig.color}>{statusConfig.label}</Badge>
          </div>

          <div className="flex items-center gap-2 mt-1">
            <Progress
              value={metrics?.overall || 0}
              className="h-2 flex-1"
            />
            <span className="text-sm font-mono text-muted-foreground">
              {metrics?.overall ? `${metrics.overall}%` : '—'}
            </span>
          </div>
        </div>

        {improvements.length > 0 && showImprovements && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 px-2 py-1 rounded-md bg-background/50">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <span className="text-xs font-medium">{improvements.length}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>{improvements.length} improvement suggestions available</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    )
  }

  // Detailed variant
  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader
        className={cn(
          'pb-3 border-b',
          statusConfig.bgColor,
          statusConfig.borderColor
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('p-2 rounded-full', statusConfig.bgColor)}>
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">Visual Quality Analysis</CardTitle>
              <CardDescription>
                Comprehensive quality metrics for this slide
              </CardDescription>
            </div>
          </div>

          <div className="text-right">
            <div className={cn('text-2xl font-bold font-mono', statusConfig.textColor)}>
              {metrics?.overall ? `${metrics.overall}%` : '—'}
            </div>
            <Badge variant={statusConfig.color} className="mt-1">
              {statusConfig.label}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Individual Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {metrics?.contrast && (
            <MetricCard
              icon={<Contrast className="h-4 w-4" />}
              label="Contrast"
              value={`${metrics.contrast.ratio.toFixed(1)}:1`}
              status={metrics.contrast.passes ? 'pass' : 'fail'}
              tooltip={`WCAG ${metrics.contrast.level || 'AA'} compliance`}
            />
          )}

          {metrics?.blur && (
            <MetricCard
              icon={<Zap className="h-4 w-4" />}
              label="Sharpness"
              value={`${((1 - metrics.blur.level) * 100).toFixed(0)}%`}
              status={metrics.blur.passes ? 'pass' : 'fail'}
              tooltip="Image clarity and focus quality"
            />
          )}

          {metrics?.saliency && (
            <MetricCard
              icon={<Eye className="h-4 w-4" />}
              label="Focus"
              value={metrics.saliency.distribution}
              status={metrics.saliency.score >= 0.6 ? 'pass' : 'warn'}
              tooltip={`${metrics.saliency.hotspots} visual hotspots detected`}
            />
          )}

          {metrics?.brand && (
            <MetricCard
              icon={<Palette className="h-4 w-4" />}
              label="Brand"
              value={
                metrics.brand.violations.length === 0
                  ? 'Compliant'
                  : `${metrics.brand.violations.length} issues`
              }
              status={metrics.brand.passes ? 'pass' : 'fail'}
              tooltip="Brand guideline compliance"
            />
          )}

          {metrics?.placement && (
            <MetricCard
              icon={<Target className="h-4 w-4" />}
              label="Layout"
              value={`${(metrics.placement.confidence * 100).toFixed(0)}%`}
              status={metrics.placement.confidence >= 0.7 ? 'pass' : 'warn'}
              tooltip={`${metrics.placement.suggestions} placement options`}
            />
          )}
        </div>

        {/* Improvement Suggestions */}
        {improvements.length > 0 && showImprovements && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <TrendingUp className="h-4 w-4" />
              Improvement Suggestions
            </div>

            <div className="space-y-1">
              {improvements.map((suggestion, index) => (
                <div
                  key={index}
                  className={cn(
                    'flex items-start gap-2 p-2 rounded-md text-sm',
                    suggestion.priority === 'high'
                      ? 'bg-red-500/10 border border-red-500/20'
                      : suggestion.priority === 'medium'
                      ? 'bg-yellow-500/10 border border-yellow-500/20'
                      : 'bg-muted/50 border border-muted'
                  )}
                >
                  <div className="mt-0.5">{suggestion.icon}</div>
                  <span className="flex-1">{suggestion.text}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Helper component for individual metrics
function MetricCard({
  icon,
  label,
  value,
  status,
  tooltip,
}: {
  icon: React.ReactNode
  label: string
  value: string
  status: 'pass' | 'fail' | 'warn'
  tooltip: string
}) {
  const statusIcon = {
    pass: <CheckCircle2 className="h-3 w-3 text-green-500" />,
    fail: <XCircle className="h-3 w-3 text-red-500" />,
    warn: <AlertCircle className="h-3 w-3 text-yellow-500" />,
  }[status]

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              'p-3 rounded-lg border cursor-help transition-colors',
              status === 'pass'
                ? 'bg-green-500/5 border-green-500/20 hover:bg-green-500/10'
                : status === 'fail'
                ? 'bg-red-500/5 border-red-500/20 hover:bg-red-500/10'
                : 'bg-yellow-500/5 border-yellow-500/20 hover:bg-yellow-500/10'
            )}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                {icon}
                <span className="text-xs font-medium">{label}</span>
              </div>
              {statusIcon}
            </div>
            <div className="font-mono text-sm font-medium">{value}</div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// Export types for external use
export type { QualityMetrics }