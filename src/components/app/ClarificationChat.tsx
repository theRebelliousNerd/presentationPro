'use client';
import { useState, useRef, useEffect, Dispatch, SetStateAction } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, User, Bot, Loader2, Lightbulb } from 'lucide-react';
import { getClarification, ingestAssets } from '@/lib/actions';
import { Presentation, ChatMessage, UploadedFileRef } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';
import FileDropzone from './FileDropzone';
import { Skeleton } from '@/components/ui/skeleton';
import { nanoid } from 'nanoid';
import { addUsage, estimateTokens } from '@/lib/token-meter';
import FormsPreviewDialog from '@/components/app/FormsPreviewDialog'

type ClarificationChatProps = {
  presentation: Presentation;
  setPresentation: Dispatch<SetStateAction<Presentation>>;
  onClarificationComplete: (finalGoals: string) => void;
  uploadFile: (file: File) => Promise<UploadedFileRef>;
  compact?: boolean;
};

const CONTEXT_SUGGESTIONS = [
  'Consider providing a company logo or brand colors.',
  'Do you have any specific data or studies to include?',
  'Are there key images or diagrams that should be in the presentation?',
  'What is the key takeaway for the audience?',
  'Is there a specific call to action?',
  'Mention any important competitors or market context.',
];

export default function ClarificationChat({ presentation, setPresentation, onClarificationComplete, uploadFile, compact = false }: ClarificationChatProps) {
  const [input, setInput] = useState('');
  const [newRawFiles, setNewRawFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(10);
  const [suggestion, setSuggestion] = useState('');

  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { chatHistory, initialInput } = presentation;

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({ top: scrollAreaRef.current.scrollHeight, behavior: 'smooth' });
    }
  };
  
  useEffect(scrollToBottom, [chatHistory]);

  useEffect(() => {
    const getInitialMessage = async () => {
      if (chatHistory.length === 0) {
        setIsLoading(true);
        try {
          const response = await getClarification([], initialInput, [], (presentation as any).id);
          const aiResponseContent = response.refinedGoals.trim();
          const newAiMessage: ChatMessage = { id: nanoid(), role: 'model', content: aiResponseContent, createdAt: Date.now() };
          setPresentation(prev => ({ ...prev, chatHistory: [newAiMessage] }));
          // If backend returned a structured patch, merge into initialInput
          const patch = (response as any).initialInputPatch as any;
          if (patch && typeof patch === 'object') {
            setPresentation(prev => ({ ...prev, initialInput: { ...prev.initialInput, ...patch } }));
          }
          // Telemetry
          const usage = (response as any).usage;
          if (usage) {
            if (usage.promptTokens) addUsage({ model: usage.model || 'gemini-2.5-flash', kind: 'prompt', tokens: usage.promptTokens, at: Date.now() } as any);
            if (usage.completionTokens) addUsage({ model: usage.model || 'gemini-2.5-flash', kind: 'completion', tokens: usage.completionTokens, at: Date.now() } as any);
          }
        } catch (error) {
          console.error("Failed to get initial message:", error);
          const errorMessage: ChatMessage = { id: nanoid(), role: 'model', content: 'Sorry, I encountered an error starting the chat. Please try refreshing.', createdAt: Date.now() };
          setPresentation(prev => ({ ...prev, chatHistory: [errorMessage] }));
        } finally {
          setIsLoading(false);
        }
      }
    };
    if (presentation.id) { // Only run if presentation is loaded
      getInitialMessage();
    }
  }, [presentation.id, setPresentation, initialInput]);

  useEffect(() => {
    const newProgress = Math.min(10 + chatHistory.length * 15, 85);
    setProgress(newProgress);
    
    if (chatHistory.length < CONTEXT_SUGGESTIONS.length) {
      setSuggestion(CONTEXT_SUGGESTIONS[chatHistory.length]);
    } else {
      setSuggestion(CONTEXT_SUGGESTIONS[CONTEXT_SUGGESTIONS.length - 1]);
    }

  }, [chatHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && newRawFiles.length === 0) || isLoading) return;
    
    setIsLoading(true);

    let messageContent = input;
    const uploadedFileInfos: UploadedFileRef[] = [];

    if (newRawFiles.length > 0) {
      const fileNames = newRawFiles.map(f => f.name).join(', ');
      messageContent += `\n\n(Attached files: ${fileNames})`;

      for (const file of newRawFiles) {
        try {
          const uploadedFile = await uploadFile(file);
          uploadedFileInfos.push(uploadedFile);
          // Ingest into orchestrator graph RAG (if enabled)
          try {
            if (presentation.id) {
              await ingestAssets(presentation.id, [uploadedFile]);
            }
          } catch {}
        } catch (error) {
          console.error(`Failed to upload file ${file.name}:`, error);
          setIsLoading(false);
          return;
        }
      }
    }

    const newUserMessage: ChatMessage = { id: nanoid(), role: 'user', content: messageContent.trim(), createdAt: Date.now() };
    const newHistory = [...chatHistory, newUserMessage];
    setPresentation(prev => ({...prev, chatHistory: newHistory}));
    setInput('');
    setNewRawFiles([]);
    
    try {
      // Estimate prompt tokens (user message only; system/context not included here)
      if (messageContent.trim()) {
        addUsage({ model: 'gemini-2.5-flash', kind: 'prompt', tokens: estimateTokens(messageContent) , at: Date.now() } as any);
      }
      const response = await getClarification(newHistory, initialInput, uploadedFileInfos, (presentation as any).id);
      const aiResponseContent = response.refinedGoals.trim();
      const newAiMessage: ChatMessage = { id: nanoid(), role: 'model', content: aiResponseContent, createdAt: Date.now() };

      setPresentation(prev => ({
        ...prev, 
        chatHistory: [...newHistory, newAiMessage],
        initialInput: {
          ...prev.initialInput,
          files: [...prev.initialInput.files, ...uploadedFileInfos]
        }
      }));
      // Merge any structured preference patch
      const patch = (response as any).initialInputPatch as any;
      if (patch && typeof patch === 'object') {
        setPresentation(prev => ({ ...prev, initialInput: { ...prev.initialInput, ...patch } }));
      }

      // Optional: apply any file intents suggested by the agent
      try {
        const intents = (response as any).fileIntents as { name: string; intent: 'content'|'style'|'graphics'|'ignore'; notes?: string }[] | undefined;
        if (Array.isArray(intents) && intents.length) {
          setPresentation(prev => {
            const allKnown = [...prev.initialInput.files, ...prev.initialInput.styleFiles, ...(prev.initialInput.graphicsFiles || []), ...uploadedFileInfos];
            const byName = new Map<string, typeof allKnown[number]>(allKnown.map(f => [f.name, f]));
            const files: typeof prev.initialInput.files = [];
            const styleFiles: typeof prev.initialInput.styleFiles = [];
            const graphicsFiles: typeof prev.initialInput.graphicsFiles = [];
            // Start with existing, then re-assign by intents when provided
            const pushUnique = (arr: any[], f: any) => { if (!arr.find(x => x.name === f.name)) arr.push(f) };
            // Default: carry over existing
            prev.initialInput.files.forEach(f => pushUnique(files, f));
            prev.initialInput.styleFiles.forEach(f => pushUnique(styleFiles, f));
            (prev.initialInput.graphicsFiles || []).forEach(f => pushUnique(graphicsFiles, f));
            // Apply intents
            for (const it of intents) {
              const f = it && byName.get(it.name);
              if (!f) continue;
              // remove from all buckets
              const rm = (arr: any[]) => arr.filter(x => x.name !== f.name);
              const cat = it.intent;
              // rebuild after removals
              const nextFiles = rm(files);
              const nextStyle = rm(styleFiles);
              const nextGraphics = rm(graphicsFiles || []);
              if (cat === 'content') pushUnique(nextFiles, f);
              else if (cat === 'style') pushUnique(nextStyle, f);
              else if (cat === 'graphics') pushUnique(nextGraphics, f);
              // assign
              (files as any) = nextFiles;
              (styleFiles as any) = nextStyle;
              (graphicsFiles as any) = nextGraphics;
            }
            return { ...prev, initialInput: { ...prev.initialInput, files, styleFiles, graphicsFiles } };
          });
        }
      } catch {}
      
      if (response.finished) {
        setProgress(100);
        onClarificationComplete(aiResponseContent);
      }
      // Estimate completion tokens
      const usage = (response as any).usage;
      if (usage && usage.completionTokens) {
        addUsage({ model: usage.model || 'gemini-2.5-flash', kind: 'completion', tokens: usage.completionTokens, at: Date.now() } as any);
      } else if (aiResponseContent) {
        addUsage({ model: 'gemini-2.5-flash', kind: 'completion', tokens: estimateTokens(aiResponseContent), at: Date.now() } as any);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = { id: nanoid(), role: 'model', content: 'Sorry, I encountered an error. Please try again.', createdAt: Date.now() };
      setPresentation(prev => ({...prev, chatHistory: [...newHistory, errorMessage]}));
    } finally {
      setIsLoading(false);
    }
  };

  const isChatReady = Boolean(presentation.id) && chatHistory.length > 0;

  return (
    <Card className={cn("flex flex-col shadow-2xl md-surface md-elevation-2", compact ? "w-80 h-[calc(100vh-140px)] sticky top-24" : "w-full max-w-3xl h-[85vh]") }>
      <CardHeader className={compact ? "py-3" : undefined}>
        <div className="flex items-center justify-between">
          <CardTitle className={cn("font-headline", compact ? "text-lg" : "text-3xl")}>Refine Goals</CardTitle>
          <FormsPreviewDialog presentation={presentation as any} setPresentation={setPresentation as any}>
            <Button size="sm" variant="outline">Review Fields</Button>
          </FormsPreviewDialog>
        </div>
        {!compact && (
          <CardDescription>
            I'm your presentation strategist. Answer my questions to help me understand your goals. You can also add more files.
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-grow overflow-hidden flex flex-col gap-4">
        <ScrollArea className="h-full pr-4" ref={scrollAreaRef}>
          <div className="space-y-6">
            {!isChatReady && (
                <div className="flex items-start gap-3 justify-start">
                    <Bot className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
                    <Skeleton className="w-3/4 h-16" />
                </div>
            )}
            {isChatReady && chatHistory.map((message, index) => (
              <div key={message.id ?? String(index)} className={cn("flex items-start gap-3", message.role === 'user' ? 'justify-end' : 'justify-start')}>
                {message.role === 'model' && <Bot className="h-6 w-6 text-primary flex-shrink-0 mt-1" />}
                <div className={cn("p-4 rounded-xl max-w-[80%] whitespace-pre-wrap", message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted')}>
                  {message.content}
                </div>
                {message.role === 'user' && <User className="h-6 w-6 text-foreground flex-shrink-0 mt-1" />}
              </div>
            ))}
            {isLoading && chatHistory.length > 0 && (
              <div className="flex items-start gap-3 justify-start">
                <Bot className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
                <div className="p-4 rounded-xl bg-muted">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="flex-shrink-0 pt-2 space-y-4">
            {/* File drop support in both compact and full modes */}
            <div className={compact ? 'border border-dashed rounded p-2 text-xs text-muted-foreground' : ''}>
              <FileDropzone 
                onFilesChange={setNewRawFiles}
                acceptedFormats=".pdf, .docx, .md, .txt, .png, .jpg, .jpeg, .webp, .gif, .svg, .csv"
              />
              {compact ? (
                <div className="mt-1 text-[11px] text-muted-foreground">Drop files here to add context</div>
              ) : null}
            </div>
            <div className="space-y-2">
                <div className="flex justify-between text-sm font-medium text-muted-foreground">
                    <span>Context Meter</span>
                    <span>{progress}%</span>
                </div>
                <Progress value={progress} className="w-full" />
                {!compact && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground pt-1">
                    <Lightbulb className="h-4 w-4 text-yellow-400" />
                    <span><b>Suggestion:</b> {suggestion}</span>
                </div>
                )}
            </div>
        </div>
      </CardContent>
      <CardFooter>
        <form onSubmit={handleSubmit} className="w-full flex items-center gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={compact ? "Ask or add context..." : "Type your message or add files above..."}
            disabled={isLoading}
            autoComplete="off"
          />
          <Button type="submit" disabled={isLoading || (!input.trim() && newRawFiles.length === 0)}>
            {isLoading && newRawFiles.length === 0 ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </form>
      </CardFooter>
    </Card>
  );
}
