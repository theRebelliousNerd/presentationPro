'use client';
import { useState, useRef, useEffect, Dispatch, SetStateAction } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, User, Bot, Loader2 } from 'lucide-react';
import { getClarification } from '@/lib/actions';
import { Presentation, ChatMessage } from '@/lib/types';
import { cn } from '@/lib/utils';

type ClarificationChatProps = {
  presentation: Presentation;
  setPresentation: Dispatch<SetStateAction<Presentation>>;
  onClarificationComplete: (finalGoals: string) => void;
};

export default function ClarificationChat({ presentation, setPresentation, onClarificationComplete }: ClarificationChatProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const { chatHistory, initialInput } = presentation;

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({ top: scrollAreaRef.current.scrollHeight, behavior: 'smooth' });
    }
  };
  
  useEffect(scrollToBottom, [chatHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const newUserMessage: ChatMessage = { role: 'user', content: input };
    const newHistory = [...chatHistory, newUserMessage];
    setPresentation(prev => ({...prev, chatHistory: newHistory}));
    setInput('');
    setIsLoading(true);

    try {
      const response = await getClarification(newHistory, initialInput);
      const aiResponseContent = response.refinedGoals.replace('---FINISHED---', '').trim();
      const newAiMessage: ChatMessage = { role: 'model', content: aiResponseContent };
      setPresentation(prev => ({...prev, chatHistory: [...newHistory, newAiMessage]}));
      
      if (response.finished) {
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
    <Card className="w-full max-w-3xl h-[80vh] flex flex-col shadow-2xl">
      <CardHeader>
        <CardTitle className="font-headline text-3xl">Let's Refine Your Idea</CardTitle>
        <CardDescription>
          I'm your presentation strategist. Answer my questions to help me understand your goals.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-grow overflow-hidden">
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
      </CardContent>
      <CardFooter>
        <form onSubmit={handleSubmit} className="w-full flex items-center gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            autoComplete="off"
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardFooter>
    </Card>
  );
}
