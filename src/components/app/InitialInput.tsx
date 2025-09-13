'use client';

import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import FileDropzone from './FileDropzone';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

type InitialInputProps = {
  onStart: (text: string, files: { name: string; dataUrl: string }[], length: string, audience: string) => void;
};

export default function InitialInput({ onStart }: InitialInputProps) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<{ name: string; dataUrl: string }[]>([]);
  const [length, setLength] = useState('medium');
  const [audience, setAudience] = useState('general');

  const isButtonDisabled = !text.trim() && files.length === 0;

  return (
    <Card className="w-full max-w-3xl shadow-2xl">
      <CardHeader>
        <CardTitle className="font-headline text-3xl">Create a New Presentation</CardTitle>
        <CardDescription>
          Start by pasting your script, notes, or any unstructured text. You can also upload supporting documents and images.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="length">Presentation Length</Label>
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
            <Label htmlFor="audience">Audience Type</Label>
            <Select value={audience} onValueChange={setAudience}>
              <SelectTrigger id="audience" className="w-full">
                <SelectValue placeholder="Select audience" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="general">General</SelectItem>
                <SelectItem value="technical">Technical</SelectItem>
                <SelectItem value="executive">Executive</SelectItem>
                <SelectItem value="sales">Sales</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <Textarea
          placeholder="Paste your presentation content here..."
          className="min-h-[200px] text-base"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <FileDropzone 
          onFilesChange={setFiles}
          acceptedFormats=".pdf, .docx, .md, .txt, .png, .jpg, .jpeg"
        />
      </CardContent>
      <CardFooter>
        <Button
          size="lg"
          className="w-full font-headline"
          disabled={isButtonDisabled}
          onClick={() => onStart(text, files, length, audience)}
        >
          Analyze & Start
        </Button>
      </CardFooter>
    </Card>
  );
}
