'use client';

import { Presentation } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

function summarizeStep(result: any): string {
  if (!result || typeof result !== 'object') return 'OK';
  const parts: string[] = [];
  if (Array.isArray(result.slides)) {
    parts.push(`slides:${result.slides.length}`);
  }
  if (result.design || result.layers) {
    parts.push('design');
  }
  if (result.findings || result.research) {
    parts.push('research');
  }
  if (result.missingCitations?.length) {
    parts.push(`missing citations:${result.missingCitations.length}`);
  }
  if (result.should_continue === false) {
    parts.push('stop=false');
  }
  if (result.status) {
    parts.push(`status:${result.status}`);
  }
  if (!parts.length) {
    const keys = Object.keys(result).slice(0, 3);
    if (keys.length) {
      parts.push(keys.join(', '));
    }
  }
  return parts.length ? parts.join(' | ') : 'OK';
}

function formatQualityEntry(entry: any, idx: number) {
  const issues = Array.isArray(entry?.violations) ? entry.violations.length : 0;
  const missing = Array.isArray(entry?.missingCitations) ? entry.missingCitations.length : 0;
  return (
    <li key={idx} className="border rounded-md p-2 space-y-1 bg-muted/40">
      <div className="flex items-center justify-between">
        <Badge variant={missing || issues ? 'destructive' : 'secondary'} className="text-[10px] uppercase tracking-wide">
          {missing || issues ? 'Action required' : 'Clean'}
        </Badge>
        {entry?.telemetry?.durationMs ? (
          <span className="text-[10px] text-muted-foreground">{entry.telemetry.durationMs} ms</span>
        ) : null}
      </div>
      {missing ? <div className="text-xs">Missing citations: {missing}</div> : null}
      {issues ? <div className="text-xs">Violations: {entry.violations.join(', ')}</div> : null}
      {!missing && !issues ? <div className="text-xs text-muted-foreground">No blockers detected.</div> : null}
    </li>
  );
}

export default function WorkflowPanel({ presentation }: { presentation: Presentation }) {
  const trace = presentation.workflowTrace || [];
  const workflowState = presentation.workflowState || {};
  const qualityLog = Array.isArray(workflowState?.metadata?.quality) ? workflowState.metadata.quality : [];
  const qualityState = workflowState?.quality_state || {};
  const slides = Array.isArray(workflowState?.slides) ? workflowState.slides : [];
  const finalResponse = workflowState?.final_response || {};
  const finalStatus = finalResponse?.status || (trace.length ? 'complete' : 'not-run');

  return (
    <div className="h-full w-[360px] md:w-[420px] lg:w-[460px] flex flex-col">
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-3">
          <Card>
            <CardHeader className="py-2">
              <CardTitle className="text-sm">Workflow Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span>Status</span>
                <Badge variant={finalStatus === 'complete' ? 'secondary' : finalStatus === 'needs_clarification' ? 'warning' : 'outline'} className="text-[10px] uppercase tracking-wide">
                  {String(finalStatus)}
                </Badge>
              </div>
              {presentation.workflowSessionId ? (
                <div className="flex justify-between">
                  <span>Session</span>
                  <span className="text-muted-foreground break-all">{presentation.workflowSessionId}</span>
                </div>
              ) : null}
              <div className="flex justify-between">
                <span>Trace steps</span>
                <span className="text-muted-foreground">{trace.length}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="py-2">
              <CardTitle className="text-sm">Trace</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              {trace.length ? (
                <div className="space-y-2">
                  {trace.map((step: any, index: number) => {
                    const summary = summarizeStep(step?.result);
                    const hasError = step?.result?.error || step?.result?.detail;
                    return (
                      <div key={index} className="border rounded-md p-2">
                        <div className="flex items-center justify-between">
                          <div className="font-medium text-[11px]">{step?.id || `step-${index + 1}`}</div>
                          <Badge variant={hasError ? 'destructive' : 'outline'} className="text-[10px] capitalize">{step?.type || 'step'}</Badge>
                        </div>
                        <div className="mt-1 text-muted-foreground">{summary}</div>
                        <details className="mt-1">
                          <summary className="cursor-pointer text-[11px] text-primary">Inspect</summary>
                          <pre className="bg-muted/40 rounded p-2 mt-1 whitespace-pre-wrap text-[10px]">
                            {JSON.stringify(step?.result, null, 2)}
                          </pre>
                        </details>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-muted-foreground">Run a workflow to populate the trace.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="py-2">
              <CardTitle className="text-sm">Quality Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              {Object.keys(qualityState || {}).length ? (
                <div className="space-y-1">
                  {Object.entries(qualityState)
                    .filter(([, value]) => value !== null && value !== undefined && value !== '' && !(Array.isArray(value) && value.length === 0))
                    .map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between">
                        <span className="capitalize">{key.replace(/([A-Z])/g, ' $1').toLowerCase()}</span>
                        <span className="text-muted-foreground">{Array.isArray(value) ? value.length : String(value)}</span>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No quality metrics recorded yet.</p>
              )}
              {qualityLog.length ? (
                <div className="space-y-2">
                  <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Guardrail snapshots</div>
                  <ul className="space-y-2">
                    {qualityLog.slice(-5).map(formatQualityEntry)}
                  </ul>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="py-2">
              <CardTitle className="text-sm">Design Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              {slides.length ? (
                <div className="space-y-2">
                  {slides.map((slide: any, index: number) => (
                    <details key={slide?.id || index} className="border rounded-md p-2">
                      <summary className="cursor-pointer text-[11px] font-medium">
                        {slide?.title || `Slide ${index + 1}`}
                      </summary>
                      <div className="mt-2 space-y-1">
                        {slide?.design?.tokens ? (
                          <div>
                            <div className="text-[10px] uppercase text-muted-foreground">Tokens</div>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {Object.entries(slide.design.tokens as Record<string, string>).map(([key, value]) => (
                                <Badge key={key} variant="outline" className="text-[10px] capitalize">{key}: {value}</Badge>
                              ))}
                            </div>
                          </div>
                        ) : null}
                        {Array.isArray(slide?.design?.layers) ? (
                          <div>
                            <div className="text-[10px] uppercase text-muted-foreground">Layers</div>
                            <ul className="mt-1 space-y-1">
                              {slide.design.layers.map((layer: any, layerIndex: number) => (
                                <li key={layerIndex} className="border rounded p-1">
                                  <div className="flex items-center justify-between">
                                    <span className="capitalize">{layer?.kind || 'layer'} #{layerIndex + 1}</span>
                                    {layer?.token ? <Badge variant="secondary" className="text-[9px]">{layer.token}</Badge> : null}
                                  </div>
                                  {layer?.css ? (
                                    <pre className="bg-muted/40 rounded mt-1 p-1 text-[9px] whitespace-pre-wrap">{layer.css}</pre>
                                  ) : null}
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                        {slide?.design?.prompt ? (
                          <div className="text-muted-foreground">Prompt: {slide.design.prompt}</div>
                        ) : null}
                      </div>
                    </details>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">Design metadata will appear after running a workflow that includes design stages.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
