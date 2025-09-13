'use server';
/**
 * @fileOverview An AI agent that refines presentation goals through a guided chat.
 *
 * - refinePresentationGoals - A function that handles the presentation goals refinement process.
 * - RefinePresentationGoalsInput - The input type for the refinePresentationGoals function.
 * - RefinePresentationGoalsOutput - The return type for the refinePresentationGoals function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const RefinePresentationGoalsInputSchema = z.object({
  inputText: z.string().describe('Unstructured text, notes, or a full script.'),
  uploadedFiles: z.array(
    z.string().describe(
      "Uploaded files as data URIs that must include a MIME type and use Base64 encoding. Expected format: 'data:<mimetype>;base64,<encoded_data>'."
    )
  ).optional(),
});
export type RefinePresentationGoalsInput = z.infer<typeof RefinePresentationGoalsInputSchema>;

const RefinePresentationGoalsOutputSchema = z.object({
  refinedGoals: z.string().describe('The refined presentation goals after the chat.'),
  finished: z.boolean().describe('Whether the clarification phase is finished.'),
});
export type RefinePresentationGoalsOutput = z.infer<typeof RefinePresentationGoalsOutputSchema>;

export async function refinePresentationGoals(input: RefinePresentationGoalsInput): Promise<RefinePresentationGoalsOutput> {
  return refinePresentationGoalsFlow(input);
}

const refinePresentationGoalsPrompt = ai.definePrompt({
  name: 'refinePresentationGoalsPrompt',
  input: {schema: RefinePresentationGoalsInputSchema},
  output: {schema: RefinePresentationGoalsOutputSchema},
  prompt: `You are a presentation strategist. Your goal is to refine the user's presentation goals through a guided chat.

You will ask targeted, sequential clarifying questions about the user's content, audience, and goals to build a comprehensive understanding of the presentation's requirements.

Incorporate Google Search results to enrich context or validate information, presenting search results as "grounding chunks" with linked sources for user verification.

Allow the user to send both text messages and upload images within the chat interface to provide additional context or assets.

Once you have a comprehensive understanding of the presentation's requirements, summarize the final plan and output a ---FINISHED--- token.

Here is the initial input from the user:

Text: {{{inputText}}}
{{#if uploadedFiles}}
Uploaded Files:
{{#each uploadedFiles}}
- {{this}}
{{/each}}
{{/if}}
`,
});

const refinePresentationGoalsFlow = ai.defineFlow(
  {
    name: 'refinePresentationGoalsFlow',
    inputSchema: RefinePresentationGoalsInputSchema,
    outputSchema: RefinePresentationGoalsOutputSchema,
  },
  async input => {
    const {output} = await refinePresentationGoalsPrompt(input);
    // Detect the FINISHED token in the output
    const finished = output?.refinedGoals?.includes('---FINISHED---') || false;

    return {
      refinedGoals: output!.refinedGoals,
      finished,
    };
  }
);
