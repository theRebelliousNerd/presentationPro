// src/ai/flows/rephrase-speaker-notes.ts
'use server';

/**
 * @fileOverview Rephrases speaker notes with different tones.
 *
 * - rephraseSpeakerNotes - A function that rephrases the speaker notes.
 * - RephraseSpeakerNotesInput - The input type for the rephraseSpeakerNotes function.
 * - RephraseSpeakerNotesOutput - The return type for the rephraseSpeakerNotes function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const RephraseSpeakerNotesInputSchema = z.object({
  speakerNotes: z.string().describe('The original speaker notes.'),
  tone: z.enum(['professional', 'concise']).describe('The desired tone for the rephrased speaker notes.'),
});
export type RephraseSpeakerNotesInput = z.infer<typeof RephraseSpeakerNotesInputSchema>;

const RephraseSpeakerNotesOutputSchema = z.object({
  rephrasedSpeakerNotes: z.string().describe('The rephrased speaker notes.'),
});
export type RephraseSpeakerNotesOutput = z.infer<typeof RephraseSpeakerNotesOutputSchema>;

export async function rephraseSpeakerNotes(input: RephraseSpeakerNotesInput): Promise<RephraseSpeakerNotesOutput> {
  return rephraseSpeakerNotesFlow(input);
}

const rephraseSpeakerNotesPrompt = ai.definePrompt({
  name: 'rephraseSpeakerNotesPrompt',
  input: {schema: RephraseSpeakerNotesInputSchema},
  output: {schema: RephraseSpeakerNotesOutputSchema},
  prompt: `Rephrase the following speaker notes in a {{{tone}}} tone:\n\n{{{speakerNotes}}}`,
});

const rephraseSpeakerNotesFlow = ai.defineFlow(
  {
    name: 'rephraseSpeakerNotesFlow',
    inputSchema: RephraseSpeakerNotesInputSchema,
    outputSchema: RephraseSpeakerNotesOutputSchema,
  },
  async input => {
    const {output} = await rephraseSpeakerNotesPrompt(input);
    return output!;
  }
);
