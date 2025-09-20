'use client';

import { Slide } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function DesignLayers({ slide }: { slide: Slide }) {
  const tokens = slide.design?.tokens && typeof slide.design.tokens === 'object'
    ? Object.entries(slide.design.tokens as Record<string, string>)
    : [];
  const layers = Array.isArray(slide.design?.layers) ? slide.design?.layers : [];
  const prompt = slide.design?.prompt;
  const image = slide.design?.image;

  if (!tokens.length && !layers.length && !prompt && !image) {
    return <p className="text-xs text-muted-foreground">No design metadata available for this slide yet.</p>;
  }

  return (
    <div className="space-y-3 text-xs">
      {tokens.length ? (
        <div className="space-y-2">
          <div className="font-medium text-sm">Token Selections</div>
          <div className="flex flex-wrap gap-1">
            {tokens.map(([key, value]) => (
              <Badge key={key} variant="outline" className="text-[11px] capitalize">
                {key}: {value}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {prompt ? (
        <Card>
          <CardHeader className="py-2">
            <CardTitle className="text-sm">Design Prompt</CardTitle>
          </CardHeader>
          <CardContent className="py-2 text-[11px] whitespace-pre-wrap">
            {prompt}
          </CardContent>
        </Card>
      ) : null}

      {image?.url ? (
        <Card>
          <CardHeader className="py-2">
            <CardTitle className="text-sm">Generated Image</CardTitle>
          </CardHeader>
          <CardContent className="py-2 text-[11px] space-y-1">
            <div className="break-all text-primary underline"><a href={image.url} target="_blank" rel="noreferrer">{image.url}</a></div>
            {image.prompt ? <div className="text-muted-foreground">Prompt: {image.prompt}</div> : null}
          </CardContent>
        </Card>
      ) : null}

      {layers.length ? (
        <div className="space-y-2">
          <div className="font-medium text-sm">Layers ({layers.length})</div>
          <div className="space-y-2">
            {layers.map((layer: any, index: number) => (
              <Card key={index} className="border-muted">
                <CardHeader className="py-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <span className="capitalize">{layer?.kind || 'layer'} #{index + 1}</span>
                    {layer?.token ? <Badge variant="secondary" className="text-[10px]">{layer.token}</Badge> : null}
                  </CardTitle>
                </CardHeader>
                <CardContent className="py-2 space-y-1 text-[11px]">
                  {layer?.columns ? <div>Columns: {layer.columns}</div> : null}
                  {layer?.gutter ? <div>Gutter: {layer.gutter}</div> : null}
                  {Array.isArray(layer?.weights) ? <div>Weights: {layer.weights.join(', ')}</div> : null}
                  {layer?.css ? (
                    <pre className="bg-muted/50 rounded p-2 text-[10px] whitespace-pre-wrap">
                      {layer.css}
                    </pre>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
