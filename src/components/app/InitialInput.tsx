'use client';

import { useState, useEffect } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import FileDropzone from './FileDropzone';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Slider } from '@/components/ui/slider';
import { industries } from '@/lib/industries';
import type { UploadedFileRef, Presentation } from '@/lib/types';
import { Loader2 } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Checkbox } from '@/components/ui/checkbox';

type InitialInputProps = {
  presentation: Presentation;
  onStart: (values: Presentation["initialInput"]) => void;
  uploadFile: (file: File) => Promise<UploadedFileRef>;
};

const TONE_LABELS = ['Very Casual', 'Casual', 'Neutral', 'Formal', 'Very Formal'];
const ENERGY_LABELS = ['Very Low', 'Low', 'Neutral', 'High', 'Very High'];

export default function InitialInput({ presentation, onStart, uploadFile }: InitialInputProps) {
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
  const [template, setTemplate] = useState<string>('');
  // Map special sentinel values from Select to internal state
  const handleTemplateChange = (v: string) => setTemplate(v === 'none' ? '' : v);
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
        contentFilesData = await Promise.all(files.map(f => uploadFile(f as File) as any).map(async (p, i) => {
          try { return await p } catch { return { name: files[i].name, url: '' } as any }
        }))
      }
      if (styleFiles.length > 0) {
        styleFilesData = await Promise.all(styleFiles.map(f => uploadFile(f as File) as any).map(async (p, i) => {
          try { return await p } catch { return { name: styleFiles[i].name, url: '' } as any }
        }))
      }
    } catch (err) {
      console.error('File upload failed, proceeding without files', err);
      toast({
        title: 'Some files failed to upload',
        description: 'Continuing without those files. You can add them later in chat.',
        variant: 'destructive',
      });
    } finally {
      onStart({ text, files: contentFilesData, styleFiles: styleFilesData, length, audience, industry, subIndustry, tone, graphicStyle,
        objective, keyMessages: splitLines(keyMessages), mustInclude: splitLines(mustInclude), mustAvoid: splitLines(mustAvoid), callToAction,
        audienceExpertise, timeConstraintMin: Number(timeConstraintMin || '') || undefined, successCriteria: splitLines(successCriteria), citationsRequired, slideDensity,
        language, locale, readingLevel,
        brandColors: splitComma(brandColors), brandFonts: splitComma(brandFonts), logoUrl,
        presentationMode, screenRatio, referenceStyle,
        allowedSources: splitComma(allowedSources), bannedSources: splitComma(bannedSources),
        accessibility: { highContrast, captions, altTextRequired }, animationLevel, interactivity: { polls: interactivityPolls, quizzes: interactivityQuizzes }, disclaimers,
        template,
      });
      setIsSubmitting(false);
    }
  }

  // Advanced clarity local state
  const [objective, setObjective] = useState('');
  const [keyMessages, setKeyMessages] = useState('');
  const [mustInclude, setMustInclude] = useState('');
  const [mustAvoid, setMustAvoid] = useState('');
  const [callToAction, setCallToAction] = useState('');
  const [audienceExpertise, setAudienceExpertise] = useState<'beginner'|'intermediate'|'expert'>('intermediate');
  const [timeConstraintMin, setTimeConstraintMin] = useState<string>('');
  const [successCriteria, setSuccessCriteria] = useState('');
  const [citationsRequired, setCitationsRequired] = useState(false);
  const [slideDensity, setSlideDensity] = useState<'light'|'normal'|'dense'>('normal');
  // Additional preferences
  const [language, setLanguage] = useState('en')
  const [locale, setLocale] = useState('en-US')
  const [readingLevel, setReadingLevel] = useState<'basic'|'intermediate'|'advanced'>('intermediate')
  const [brandColors, setBrandColors] = useState('')
  const [brandFonts, setBrandFonts] = useState('')
  const [logoUrl, setLogoUrl] = useState('')
  const [presentationMode, setPresentationMode] = useState<'in-person'|'virtual'|'hybrid'>('in-person')
  const [screenRatio, setScreenRatio] = useState<'16:9'|'4:3'|'1:1'>('16:9')
  const [referenceStyle, setReferenceStyle] = useState<'apa'|'mla'|'chicago'|'none'>('none')
  const [allowedSources, setAllowedSources] = useState('')
  const [bannedSources, setBannedSources] = useState('')
  const [highContrast, setHighContrast] = useState(false)
  const [captions, setCaptions] = useState(false)
  const [altTextRequired, setAltTextRequired] = useState(false)
  const [animationLevel, setAnimationLevel] = useState<'none'|'minimal'|'moderate'|'high'>('minimal')
  const [interactivityPolls, setInteractivityPolls] = useState(false)
  const [interactivityQuizzes, setInteractivityQuizzes] = useState(false)
  const [disclaimers, setDisclaimers] = useState('')

  // When chat infers structure, it updates presentation.initialInput.
  // Mirror those values here so the form auto-fills live.
  useEffect(() => {
    if (!presentation?.initialInput) return;
    const i: any = presentation.initialInput;
    // Core
    setText(i.text || '');
    setLength(i.length || 'medium');
    setAudience(i.audience || 'general');
    setIndustry(i.industry || '');
    setSubIndustry(i.subIndustry || '');
    setTone({
      formality: typeof i.tone?.formality === 'number' ? i.tone.formality : 2,
      energy: typeof i.tone?.energy === 'number' ? i.tone.energy : 2,
    });
    setGraphicStyle(i.graphicStyle || 'modern');
    setTemplate(i.template || '');
    // Advanced
    setObjective(i.objective || '');
    setKeyMessages(Array.isArray(i.keyMessages) ? i.keyMessages.join('\n') : (i.keyMessages || ''));
    setMustInclude(Array.isArray(i.mustInclude) ? i.mustInclude.join('\n') : (i.mustInclude || ''));
    setMustAvoid(Array.isArray(i.mustAvoid) ? i.mustAvoid.join('\n') : (i.mustAvoid || ''));
    setCallToAction(i.callToAction || '');
    setAudienceExpertise((i.audienceExpertise || 'intermediate') as any);
    setTimeConstraintMin(i.timeConstraintMin ? String(i.timeConstraintMin) : '');
    setSuccessCriteria(Array.isArray(i.successCriteria) ? i.successCriteria.join('\n') : (i.successCriteria || ''));
    setCitationsRequired(!!i.citationsRequired);
    setSlideDensity((i.slideDensity || 'normal') as any);
    setLanguage(i.language || 'en');
    setLocale(i.locale || 'en-US');
    setReadingLevel((i.readingLevel || 'intermediate') as any);
    setBrandColors(Array.isArray(i.brandColors) ? i.brandColors.join(', ') : (i.brandColors || ''));
    setBrandFonts(Array.isArray(i.brandFonts) ? i.brandFonts.join(', ') : (i.brandFonts || ''));
    setLogoUrl(i.logoUrl || '');
    setPresentationMode((i.presentationMode || 'in-person') as any);
    setScreenRatio((i.screenRatio || '16:9') as any);
    setReferenceStyle((i.referenceStyle || 'none') as any);
    setAllowedSources(Array.isArray(i.allowedSources) ? i.allowedSources.join(', ') : (i.allowedSources || ''));
    setBannedSources(Array.isArray(i.bannedSources) ? i.bannedSources.join(', ') : (i.bannedSources || ''));
    setHighContrast(!!i.accessibility?.highContrast);
    setCaptions(!!i.accessibility?.captions);
    setAltTextRequired(!!i.accessibility?.altTextRequired);
    setAnimationLevel((i.animationLevel || 'minimal') as any);
    setInteractivityPolls(!!i.interactivity?.polls);
    setInteractivityQuizzes(!!i.interactivity?.quizzes);
    setDisclaimers(i.disclaimers || '');
  }, [presentation?.initialInput]);

  function splitLines(s: string): string[] { return s.split('\n').map(v => v.trim()).filter(Boolean) }
  function splitComma(s: string): string[] { return s.split(',').map(v => v.trim()).filter(Boolean) }

  return (
    <Card className="w-full max-w-5xl shadow-2xl border-2 border-border/50 md-surface md-elevation-2 rounded-2xl">
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
        <Accordion type="single" collapsible>
          <AccordionItem value="advanced">
            <AccordionTrigger className="text-base font-headline font-semibold text-foreground">Advanced Clarity</AccordionTrigger>
            <AccordionContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 p-4 bg-muted/10 rounded-lg border border-border/30">
                <div>
                  <Label className="text-xs text-muted-foreground">Objective / Purpose</Label>
                  <Input placeholder="e.g., Secure stakeholder buy-in for Q4 roadmap" value={objective} onChange={(e)=>setObjective(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Call to Action</Label>
                  <Input placeholder="e.g., Book pilot by Oct 15" value={callToAction} onChange={(e)=>setCallToAction(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Audience Expertise</Label>
                  <select className="w-full border rounded p-2 bg-background" value={audienceExpertise} onChange={(e)=>setAudienceExpertise(e.target.value as any)}>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="expert">Expert</option>
                  </select>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Time Constraint (minutes)</Label>
                  <Input type="number" min={1} placeholder="e.g., 20" value={timeConstraintMin} onChange={(e)=>setTimeConstraintMin(e.target.value)} />
                </div>
                <div className="sm:col-span-2">
                  <Label className="text-xs text-muted-foreground">Key Messages (one per line)</Label>
                  <Textarea className="min-h-[100px]" placeholder="Message 1\nMessage 2" value={keyMessages} onChange={(e)=>setKeyMessages(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Must Include</Label>
                  <Textarea className="min-h-[100px]" placeholder="Topics to include..." value={mustInclude} onChange={(e)=>setMustInclude(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Must Avoid</Label>
                  <Textarea className="min-h-[100px]" placeholder="Topics to avoid..." value={mustAvoid} onChange={(e)=>setMustAvoid(e.target.value)} />
                </div>
                <div className="sm:col-span-2">
                  <Label className="text-xs text-muted-foreground">Success Criteria (one per line)</Label>
                  <Textarea className="min-h-[100px]" placeholder="e.g., Audience can describe X\ne.g., Stakeholders commit to Y" value={successCriteria} onChange={(e)=>setSuccessCriteria(e.target.value)} />
                </div>
                <div className="flex items-center gap-2">
                  <Checkbox id="citations" checked={citationsRequired} onCheckedChange={(v)=>setCitationsRequired(!!v)} />
                  <Label htmlFor="citations" className="text-xs text-muted-foreground">Citations required</Label>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Slide Density</Label>
                  <select className="w-full border rounded p-2 bg-background" value={slideDensity} onChange={(e)=>setSlideDensity(e.target.value as any)}>
                    <option value="light">Light</option>
                    <option value="normal">Normal</option>
                    <option value="dense">Dense</option>
                  </select>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
        {/* Additional Preferences */}
        <Accordion type="single" collapsible>
          <AccordionItem value="prefs">
            <AccordionTrigger className="text-base font-headline font-semibold text-foreground">Presentation Preferences</AccordionTrigger>
            <AccordionContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 p-4 bg-muted/10 rounded-lg border border-border/30">
                <div>
                  <Label className="text-xs text-muted-foreground">Language</Label>
                  <Input placeholder="en" value={language} onChange={(e)=>setLanguage(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Locale</Label>
                  <Input placeholder="en-US" value={locale} onChange={(e)=>setLocale(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Reading Level</Label>
                  <select className="w-full border rounded p-2 bg-background" value={readingLevel} onChange={(e)=>setReadingLevel(e.target.value as any)}>
                    <option value="basic">Basic</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Brand Colors (comma separated)</Label>
                  <Input placeholder="#123456, #abcdef" value={brandColors} onChange={(e)=>setBrandColors(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Brand Fonts (comma separated)</Label>
                  <Input placeholder="Inter, Roboto" value={brandFonts} onChange={(e)=>setBrandFonts(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Logo URL</Label>
                  <Input placeholder="https://..." value={logoUrl} onChange={(e)=>setLogoUrl(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Presentation Mode</Label>
                  <select className="w-full border rounded p-2 bg-background" value={presentationMode} onChange={(e)=>setPresentationMode(e.target.value as any)}>
                    <option value="in-person">In-person</option>
                    <option value="virtual">Virtual</option>
                    <option value="hybrid">Hybrid</option>
                  </select>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Screen Ratio</Label>
                  <select className="w-full border rounded p-2 bg-background" value={screenRatio} onChange={(e)=>setScreenRatio(e.target.value as any)}>
                    <option value="16:9">16:9</option>
                    <option value="4:3">4:3</option>
                    <option value="1:1">1:1</option>
                  </select>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Reference Style</Label>
                  <select className="w-full border rounded p-2 bg-background" value={referenceStyle} onChange={(e)=>setReferenceStyle(e.target.value as any)}>
                    <option value="none">None</option>
                    <option value="apa">APA</option>
                    <option value="mla">MLA</option>
                    <option value="chicago">Chicago</option>
                  </select>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Allowed Sources (domains, comma separated)</Label>
                  <Input placeholder=".gov, .edu" value={allowedSources} onChange={(e)=>setAllowedSources(e.target.value)} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Banned Sources (domains, comma separated)</Label>
                  <Input value={bannedSources} onChange={(e)=>setBannedSources(e.target.value)} />
                </div>
                <div className="col-span-2 grid grid-cols-3 gap-2">
                  <div className="flex items-center gap-2"><Checkbox id="hi" checked={highContrast} onCheckedChange={v=>setHighContrast(!!v)} /><Label htmlFor="hi" className="text-xs text-muted-foreground">High contrast</Label></div>
                  <div className="flex items-center gap-2"><Checkbox id="cap" checked={captions} onCheckedChange={v=>setCaptions(!!v)} /><Label htmlFor="cap" className="text-xs text-muted-foreground">Captions</Label></div>
                  <div className="flex items-center gap-2"><Checkbox id="alt" checked={altTextRequired} onCheckedChange={v=>setAltTextRequired(!!v)} /><Label htmlFor="alt" className="text-xs text-muted-foreground">Alt text required</Label></div>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Animation Level</Label>
                  <select className="w-full border rounded p-2 bg-background" value={animationLevel} onChange={(e)=>setAnimationLevel(e.target.value as any)}>
                    <option value="none">None</option>
                    <option value="minimal">Minimal</option>
                    <option value="moderate">Moderate</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div className="col-span-2 grid grid-cols-2 gap-2">
                  <div className="flex items-center gap-2"><Checkbox id="polls" checked={interactivityPolls} onCheckedChange={v=>setInteractivityPolls(!!v)} /><Label htmlFor="polls" className="text-xs text-muted-foreground">Polls</Label></div>
                  <div className="flex items-center gap-2"><Checkbox id="quizzes" checked={interactivityQuizzes} onCheckedChange={v=>setInteractivityQuizzes(!!v)} /><Label htmlFor="quizzes" className="text-xs text-muted-foreground">Quizzes</Label></div>
                </div>
                <div className="sm:col-span-2">
                  <Label className="text-xs text-muted-foreground">Disclaimers</Label>
                  <Textarea className="min-h-[80px]" value={disclaimers} onChange={(e)=>setDisclaimers(e.target.value)} />
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
        <div className="space-y-2">
          <Label className="text-base font-headline font-semibold text-foreground">Template Preset (Optional)</Label>
          <CardDescription>Choose a preset that guides outline, slide density, and visual style.</CardDescription>
          <Select value={template} onValueChange={handleTemplateChange}>
            <SelectTrigger className="w-[280px]"><SelectValue placeholder="Select a template" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem value="enterprise">Enterprise Pitch (C‑suite)</SelectItem>
              <SelectItem value="startup">Startup Demo (Investors)</SelectItem>
              <SelectItem value="academic">Academic Talk</SelectItem>
            </SelectContent>
          </Select>
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
