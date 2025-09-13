'use server';

import { refinePresentationGoals } from '@/ai/flows/refine-presentation-goals';
import { generatePresentationOutline } from '@/ai/flows/generate-presentation-outline';
import { generateSlideContent as generateSlideContentFlow } from '@/ai/flows/generate-slide-content';
import { generateAndEditImage as generateAndEditImageFlow } from '@/ai/flows/generate-and-edit-images';
import { rephraseSpeakerNotes as rephraseSpeakerNotesFlow } from '@/ai/flows/rephrase-speaker-notes';

import type { ChatMessage, Presentation } from './types';
import type { GenerateSlideContentInput } from '@/ai/flows/generate-slide-content';

export async function getClarification(
  history: ChatMessage[],
  initialInput: Presentation['initialInput']
) {
  const initialPrompt = `Initial User Input:\nText: ${initialInput.text}\nAudience: ${initialInput.audience}\nLength: ${initialInput.length}\nFiles: ${initialInput.files.map(f => f.name).join(', ')}`;

  const inputText = [
    initialPrompt,
    ...history.map(m => `${m.role}: ${m.content}`)
  ].join('\n\n');
  
  const uploadedFiles = initialInput.files.map(f => f.dataUrl);

  return await refinePresentationGoals({ inputText, uploadedFiles });
}

export async function getPresentationOutline(clarifiedGoals: string) {
  return await generatePresentationOutline({ clarifiedContent: clarifiedGoals });
}

export async function generateSlideContent(input: GenerateSlideContentInput) {
    return await generateSlideContentFlow(input);
}

export async function generateImage(prompt: string) {
    return await generateAndEditImageFlow({ prompt });
}

export async function editImage(prompt: string, baseImage: string) {
    return await generateAndEditImageFlow({ prompt, baseImage });
}

export async function rephraseNotes(speakerNotes: string, tone: 'professional' | 'concise') {
    return await rephraseSpeakerNotesFlow({ speakerNotes, tone });
}
