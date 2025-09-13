'use client';

import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import FileDropzone from './FileDropzone';

type InitialInputProps = {
  onStart: (text: string, files: { name: string; dataUrl: string }[]) => void;
};

export default function InitialInput({ onStart }: InitialInputProps) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<{ name: string; dataUrl: string }[]>([]);

  const isButtonDisabled = !text.trim() && files.length === 0;

  return (
    <Card className="w-full max-w-2xl shadow-2xl">
      <CardHeader>
        <CardTitle className="font-headline text-3xl">Create a New Presentation</CardTitle>
        <CardDescription>
          Start by pasting your script, notes, or any unstructured text. You can also upload supporting documents and images.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
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
          onClick={() => onStart(text, files)}
        >
          Analyze & Start
        </Button>
      </CardFooter>
    </Card>
  );
}
