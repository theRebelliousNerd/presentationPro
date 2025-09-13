'use client';

import { useState, useEffect } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import FileDropzone from './FileDropzone';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Slider } from '@/components/ui/slider';
import { industries } from '@/lib/industries';
import type { UploadedFileRef } from '@/lib/types';
import { Loader2 } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

type InitialInputProps = {
  onStart: (values: {
    text: string;
    files: UploadedFileRef[];
    styleFiles: UploadedFileRef[];
    length: string;
    audience: string;
    industry: string;
    subIndustry: string;
    tone: { formality: number; energy: number };
    graphicStyle: string;
  }) => void;
  uploadFile: (file: File) => Promise<UploadedFileRef>;
};

const TONE_LABELS = ['Very Casual', 'Casual', 'Neutral', 'Formal', 'Very Formal'];
const ENERGY_LABELS = ['Very Low', 'Low', 'Neutral', 'High', 'Very High'];

export default function InitialInput({ onStart, uploadFile }: InitialInputProps) {
  const [text, setText] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [styleFiles, setStyleFiles] = useState<File[]>([]);
  const [length, setLength] = useState('medium');
  const [audience, setAudience] = useState('general');
  const [industry, setIndustry] = useState('');
  const [subIndustry, setSubIndustry] = useState('');
  const [subIndustries, setSubIndustries] = useState<string[]>([]);
  const [tone, setTone] = useState({ formality: 2, energy: 2 });
  const [graphicStyle, setGraphicStyle] = useState('modern');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const selectedIndustry = industries.find(i => i.name === industry);
    if (selectedIndustry && selectedIndustry.subIndustries) {
      setSubIndustries(selectedIndustry.subIndustries);
      setSubIndustry(''); // Reset sub-industry when industry changes
    } else {
      setSubIndustries([]);
      setSubIndustry('');
    }
  }, [industry]);
  
  const isButtonDisabled = !text.trim() && files.length === 0;

  const handleSubmit = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    let contentFilesData: UploadedFileRef[] = [];
    let styleFilesData: UploadedFileRef[] = [];
    try {
      if (files.length > 0) {
        contentFilesData = await Promise.all(files.map(uploadFile));
      }
      if (styleFiles.length > 0) {
        styleFilesData = await Promise.all(styleFiles.map(uploadFile));
      }
    } catch (err) {
      console.error('File upload failed, proceeding without files', err);
      toast({
        title: 'Some files failed to upload',
        description: 'Continuing without those files. You can add them later in chat.',
        variant: 'destructive',
      });
    } finally {
      onStart({ text, files: contentFilesData, styleFiles: styleFilesData, length, audience, industry, subIndustry, tone, graphicStyle });
      setIsSubmitting(false);
    }
  }

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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-4 bg-muted/20 rounded-lg border border-border/30">
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
                <Label htmlFor="industry" className="text-xs text-muted-foreground">Industry</Label>
                <Select value={industry} onValueChange={setIndustry}>
                  <SelectTrigger id="industry" className="w-full">
                    <SelectValue placeholder="Select industry" />
                  </SelectTrigger>
                  <SelectContent>
                    {industries.map((ind) => (
                      <SelectItem key={ind.name} value={ind.name}>{ind.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {subIndustries.length > 0 && (
                <div>
                  <Label htmlFor="sub-industry" className="text-xs text-muted-foreground">Sub-Industry</Label>
                  <Select value={subIndustry} onValueChange={setSubIndustry}>
                    <SelectTrigger id="sub-industry" className="w-full">
                      <SelectValue placeholder="Select sub-industry" />
                    </SelectTrigger>
                    <SelectContent>
                      {subIndustries.map((subInd) => (
                        <SelectItem key={subInd} value={subInd}>{subInd}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div>
                <Label htmlFor="graphic-style" className="text-xs text-muted-foreground">Graphic Style</Label>
                <Select value={graphicStyle} onValueChange={setGraphicStyle}>
                  <SelectTrigger id="graphic-style" className="w-full">
                    <SelectValue placeholder="Select style" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="modern">Modern & Clean</SelectItem>
                    <SelectItem value="minimalist">Minimalist</SelectItem>
                    <SelectItem value="corporate">Corporate & Professional</SelectItem>
                    <SelectItem value="playful">Playful & Creative</SelectItem>
                    <SelectItem value="elegant">Elegant & Sophisticated</SelectItem>
                    <SelectItem value="retro">Retro</SelectItem>
                    <SelectItem value="art-deco">Art Deco</SelectItem>
                    <SelectItem value="turn-of-the-century">Turn of the Century</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-3">
                <Label className="text-xs text-muted-foreground">Formality: <span className="font-bold text-primary">{TONE_LABELS[tone.formality]}</span></Label>
                <Slider
                  defaultValue={[2]}
                  min={0}
                  max={4}
                  step={1}
                  onValueChange={(value) => setTone(prev => ({...prev, formality: value[0]}))}
                />
              </div>
              <div className="space-y-3">
                <Label className="text-xs text-muted-foreground">Energy: <span className="font-bold text-primary">{ENERGY_LABELS[tone.energy]}</span></Label>
                <Slider
                  defaultValue={[2]}
                  min={0}
                  max={4}
                  step={1}
                  onValueChange={(value) => setTone(prev => ({...prev, energy: value[0]}))}
                />
              </div>
            </div>
        </div>
        <Separator />
         <div className="space-y-2">
            <Label className="text-base font-headline font-semibold text-foreground">Presentation Content</Label>
            <CardDescription>The core material for your presentation. Paste text below and/or upload supporting documents, data, charts, etc.</CardDescription>
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
            <CardDescription>Upload files to guide the visual style (e.g., brand guidelines, logos, color palettes, background images).</CardDescription>
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
          disabled={isButtonDisabled || isSubmitting}
          onClick={handleSubmit}
        >
          {isSubmitting ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin"/>Preparing...</>) : 'Start Creating'}
        </Button>
      </CardFooter>
    </Card>
  );
}
