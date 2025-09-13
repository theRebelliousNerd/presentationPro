'use client';
import { useState, useRef, useEffect, Dispatch, SetStateAction } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, User, Bot, Loader2, Lightbulb } from 'lucide-react';
import { getClarification } from '@/lib/actions';
import { Presentation, ChatMessage, UploadedFileRef } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';
import FileDropzone from './FileDropzone';
import { Skeleton } from '@/components/ui/skeleton';
import { nanoid } from 'nanoid';
import { addUsage, estimateTokens } from '@/lib/token-meter';

type ClarificationChatProps = {
  presentation: Presentation;
  setPresentation: Dispatch<SetStateAction<Presentation>>;
  onClarificationComplete: (finalGoals: string) => void;
  uploadFile: (file: File) => Promise<UploadedFileRef>;
};

const CONTEXT_SUGGESTIONS = [
  'Consider providing a company logo or brand colors.',
  'Do you have any specific data or studies to include?',
  'Are there key images or diagrams that should be in the presentation?',
  'What is the key takeaway for the audience?',
  'Is there a specific call to action?',
  'Mention any important competitors or market context.',
];

export default function ClarificationChat({ presentation, setPresentation, onClarificationComplete, uploadFile }: ClarificationChatProps) {
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
          const response = await getClarification([], initialInput, []);
          const aiResponseContent = response.refinedGoals.trim();
          const newAiMessage: ChatMessage = { id: nanoid(), role: 'model', content: aiResponseContent, createdAt: Date.now() };
          setPresentation(prev => ({ ...prev, chatHistory: [newAiMessage] }));
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
      const response = await getClarification(newHistory, initialInput, uploadedFileInfos);
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
      
      if (response.finished) {
        setProgress(100);
        onClarificationComplete(aiResponseContent);
      }
      // Estimate completion tokens
      if (aiResponseContent) {
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

  const isChatReady = presentation.id && chatHistory.length > 0;

  return (
    <Card className="w-full max-w-3xl h-[85vh] flex flex-col shadow-2xl">
      <CardHeader>
        <CardTitle className="font-headline text-3xl">Let's Refine Your Idea</CardTitle>
        <CardDescription>
          I'm your presentation strategist. Answer my questions to help me understand your goals. You can also add more files.
        </CardDescription>
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
            <FileDropzone 
              onFilesChange={setNewRawFiles}
              acceptedFormats=".pdf, .docx, .md, .txt, .png, .jpg, .jpeg, .csv, .xls, .xlsx"
            />
            <div className="space-y-2">
                <div className="flex justify-between text-sm font-medium text-muted-foreground">
                    <span>Context Meter</span>
                    <span>{progress}% complete</span>
                </div>
                <Progress value={progress} className="w-full" />
                <div className="flex items-center gap-2 text-xs text-muted-foreground pt-1">
                    <Lightbulb className="h-4 w-4 text-yellow-400" />
                    <span><b>Suggestion:</b> {suggestion}</span>
                </div>
            </div>
        </div>
      </CardContent>
      <CardFooter>
        <form onSubmit={handleSubmit} className="w-full flex items-center gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message or add files above..."
            disabled={isLoading || !isChatReady}
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
