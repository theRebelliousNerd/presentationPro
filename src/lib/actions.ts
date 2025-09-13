'use server';

import { refinePresentationGoals } from '@/ai/flows/refine-presentation-goals';
import { generatePresentationOutline } from '@/ai/flows/generate-presentation-outline';
import { generateSlideContent as generateSlideContentFlow } from '@/ai/flows/generate-slide-content';
import { generateAndEditImage as generateAndEditImageFlow } from '@/ai/flows/generate-and-edit-images';
import { rephraseSpeakerNotes as rephraseSpeakerNotesFlow } from '@/ai/flows/rephrase-speaker-notes';

import type { ChatMessage, Presentation } from './types';
import type { GenerateSlideContentInput } from '@/ai/flows/generate-slide-content';

const TONE_LABELS = ['Very Casual', 'Casual', 'Neutral', 'Formal', 'Very Formal'];
const ENERGY_LABELS = ['Very Low', 'Low', 'Neutral', 'High', 'Very High'];

export async function getClarification(
  history: ChatMessage[],
  initialInput: Presentation['initialInput'],
  newFiles: { name: string; dataUrl: string }[] = []
) {
  const formality = TONE_LABELS[initialInput.tone.formality];
  const energy = ENERGY_LABELS[initialInput.tone.energy];

  const initialPrompt = `Initial User Input:
Text: ${initialInput.text}
Length: ${initialInput.length}
Audience: ${initialInput.audience}
Industry: ${initialInput.industry}
Sub-Industry: ${initialInput.subIndustry}
Tone (Formality): ${formality}
Tone (Energy): ${energy}
Graphic Style: ${initialInput.graphicStyle}
Content Files: ${initialInput.files.map(f => f.name).join(', ')}
Style Guide Files: ${initialInput.styleFiles.map(f => f.name).join(', ')}`;

  const inputText = [
    initialPrompt,
    ...history.map(m => `${m.role}: ${m.content}`)
  ].join('\n\n');
  
  const allFiles = [...initialInput.files, ...initialInput.styleFiles, ...newFiles];
  const uploadedFiles = allFiles.map(f => f.dataUrl);

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
