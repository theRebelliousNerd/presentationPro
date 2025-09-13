'use client';

import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import FileDropzone from './FileDropzone';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';

type InitialInputProps = {
  onStart: (text: string, files: { name: string; dataUrl: string }[], length: string, audience: string, tone: string, mood: string, colorScheme: string) => void;
};

export default function InitialInput({ onStart }: InitialInputProps) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<{ name: string; dataUrl: string }[]>([]);
  const [styleFiles, setStyleFiles] = useState<{ name: string; dataUrl: string }[]>([]);
  const [length, setLength] = useState('medium');
  const [audience, setAudience] = useState('general');
  const [tone, setTone] = useState('educational');
  const [mood, setMood] = useState('neutral');
  const [colorScheme, setColorScheme] = useState('default');

  const isButtonDisabled = !text.trim() && files.length === 0;

  return (
    <Card className="w-full max-w-5xl shadow-2xl border-2 border-border/50">
      <CardHeader>
        <CardTitle className="font-headline text-3xl bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">Create a New Presentation</CardTitle>
        <CardDescription>
          Start by pasting your script, notes, or any unstructured text. You can also upload supporting documents and images.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        <div className="space-y-2">
            <Label className="text-base font-headline font-semibold text-foreground">Presentation Parameters</Label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4 bg-muted/20 rounded-lg border border-border/30">
              <div>
                <Label htmlFor="length" className="text-xs text-muted-foreground">Length</Label>
                <Select value={length} onValueChange={setLength}>
                  <SelectTrigger id="length" className="w-full">
                    <SelectValue placeholder="Select length" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="short">Short (5-10 slides)</SelectItem>
                    <SelectItem value="medium">Medium (10-15 slides)</SelectItem>
                    <SelectItem value="long">Long (15-20+ slides)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="audience" className="text-xs text-muted-foreground">Audience</Label>
                <Select value={audience} onValueChange={setAudience}>
                  <SelectTrigger id="audience" className="w-full">
                    <SelectValue placeholder="Select audience" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="technical">Technical</SelectItem>
                    <SelectItem value="executive">Executive</SelectItem>
                    <SelectItem value="sales">Sales</SelectItem>
                    <SelectItem value="investors">Investors</SelectItem>
                    <SelectItem value="students">Students</SelectItem>
                    <SelectItem value="internal-team">Internal Team</SelectItem>
                  </SelectContent>
                </Select>
              </div>
               <div>
                <Label htmlFor="tone" className="text-xs text-muted-foreground">Tone</Label>
                <Select value={tone} onValueChange={setTone}>
                  <SelectTrigger id="tone" className="w-full">
                    <SelectValue placeholder="Select tone" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="educational">Educational / TED Talk</SelectItem>
                    <SelectItem value="sales">Sales Pitch</SelectItem>
                    <SelectItem value="technical">Technical Deep Dive</SelectItem>
                    <SelectItem value="storytelling">Storytelling</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="mood" className="text-xs text-muted-foreground">Mood</Label>
                <Select value={mood} onValueChange={setMood}>
                  <SelectTrigger id="mood" className="w-full">
                    <SelectValue placeholder="Select mood" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="neutral">Neutral</SelectItem>
                    <SelectItem value="funny">Funny</SelectItem>
                    <SelectItem value="serious">Serious</SelectItem>
                    <SelectItem value="inspirational">Inspirational</SelectItem>
                    <SelectItem value="sad">Sad</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="color-scheme" className="text-xs text-muted-foreground">Color Scheme</Label>
                <Select value={colorScheme} onValueChange={setColorScheme}>
                  <SelectTrigger id="color-scheme" className="w-full">
                    <SelectValue placeholder="Select color scheme" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default</SelectItem>
                    <SelectItem value="corporate-blue">Corporate Blue</SelectItem>
                    <SelectItem value="creative-vibrant">Creative & Vibrant</SelectItem>
                    <SelectItem value="earthy-natural">Earthy & Natural</SelectItem>
                    <SelectItem value="tech-dark">Tech Dark Mode</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
        </div>
        <Separator />
         <div className="space-y-2">
            <Label className="text-base font-headline font-semibold text-foreground">Presentation Content</Label>
            <Textarea
              placeholder="Paste your presentation content here..."
              className="min-h-[200px] text-base p-4"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <FileDropzone 
              onFilesChange={setFiles}
              acceptedFormats=".pdf, .docx, .md, .txt, .png, .jpg, .jpeg, .csv, .xls, .xlsx"
            />
        </div>
        <Separator />
        <div className="space-y-2">
            <Label className="text-base font-headline font-semibold text-foreground">Style Guide (Optional)</Label>
             <FileDropzone 
              onFilesChange={setStyleFiles}
              acceptedFormats=".pdf, .png, .jpg, .jpeg"
            />
        </div>
      </CardContent>
      <CardFooter>
        <Button
          size="lg"
          className="w-full font-headline text-base"
          disabled={isButtonDisabled}
          onClick={() => onStart(text, files, length, audience, tone, mood, colorScheme)}
        >
          Start Creating
        </Button>
      </CardFooter>
    </Card>
  );
}
