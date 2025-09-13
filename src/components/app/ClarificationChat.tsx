'use client';
import { useState, useRef, useEffect, Dispatch, SetStateAction } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, User, Bot, Loader2, Lightbulb, Paperclip } from 'lucide-react';
import { getClarification } from '@/lib/actions';
import { Presentation, ChatMessage } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';
import FileDropzone from './FileDropzone';

type ClarificationChatProps = {
  presentation: Presentation;
  setPresentation: Dispatch<SetStateAction<Presentation>>;
  onClarificationComplete: (finalGoals: string) => void;
};

const CONTEXT_SUGGESTIONS = [
  'Consider providing a company logo or brand colors.',
  'Do you have any specific data or studies to include?',
  'Are there key images or diagrams that should be in the presentation?',
  'What is the key takeaway for the audience?',
  'Is there a specific call to action?',
  'Mention any important competitors or market context.',
];

export default function ClarificationChat({ presentation, setPresentation, onClarificationComplete }: ClarificationChatProps) {
  const [input, setInput] = useState('');
  const [newFiles, setNewFiles] = useState<{ name: string; dataUrl: string }[]>([]);
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
    // Update progress based on chat length
    const newProgress = Math.min(10 + chatHistory.length * 15, 85);
    setProgress(newProgress);
    
    // Update suggestion
    if (chatHistory.length < CONTEXT_SUGGESTIONS.length) {
      setSuggestion(CONTEXT_SUGGESTIONS[chatHistory.length]);
    } else {
      setSuggestion(CONTEXT_SUGGESTIONS[CONTEXT_SUGGESTIONS.length - 1]);
    }

  }, [chatHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && newFiles.length === 0) || isLoading) return;

    let messageContent = input;
    if (newFiles.length > 0) {
      const fileNames = newFiles.map(f => f.name).join(', ');
      messageContent += `\n\n(Attached files: ${fileNames})`;
    }

    const newUserMessage: ChatMessage = { role: 'user', content: messageContent.trim() };
    const newHistory = [...chatHistory, newUserMessage];
    setPresentation(prev => ({...prev, chatHistory: newHistory}));
    setInput('');
    setNewFiles([]); // Clear files after sending
    setIsLoading(true);

    try {
      // We pass the new files along with the history
      const response = await getClarification(newHistory, initialInput, newFiles);
      const aiResponseContent = response.refinedGoals.replace('---FINISHED---', '').trim();
      const newAiMessage: ChatMessage = { role: 'model', content: aiResponseContent };
      
      // We also add the newly uploaded files to the permanent presentation state
      setPresentation(prev => ({
        ...prev, 
        chatHistory: [...newHistory, newAiMessage],
        initialInput: {
          ...prev.initialInput,
          files: [...prev.initialInput.files, ...newFiles]
        }
      }));
      
      if (response.finished) {
        setProgress(100);
        onClarificationComplete(aiResponseContent);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = { role: 'model', content: 'Sorry, I encountered an error. Please try again.' };
      setPresentation(prev => ({...prev, chatHistory: [...newHistory, errorMessage]}));
    } finally {
      setIsLoading(false);
    }
  };

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
            {chatHistory.map((message, index) => (
              <div key={index} className={cn("flex items-start gap-3", message.role === 'user' ? 'justify-end' : 'justify-start')}>
                {message.role === 'model' && <Bot className="h-6 w-6 text-primary flex-shrink-0 mt-1" />}
                <div className={cn("p-4 rounded-xl max-w-[80%] whitespace-pre-wrap", message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted')}>
                  {message.content}
                </div>
                {message.role === 'user' && <User className="h-6 w-6 text-foreground flex-shrink-0 mt-1" />}
              </div>
            ))}
            {isLoading && (
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
              onFilesChange={setNewFiles}
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
            disabled={isLoading}
            autoComplete="off"
          />
          <Button type="submit" disabled={isLoading || (!input.trim() && newFiles.length === 0)}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardFooter>
    </Card>
  );
}
