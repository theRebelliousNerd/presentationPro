'use server';
/**
 * @fileOverview An AI agent that refines presentation goals through a guided chat.
 *
 * - refinePresentationGoals - A function that handles the presentation goals refinement process.
 * - RefinePresentationGoalsInput - The input type for the refinePresentationGoals function.
 * - RefinePresentationGoalsOutput - The return type for the refinePresentationGoals function.
 */

// import {ai} from '@/ai.deprecated_genkit/genkit'; // Archived - do not use
import {z} from 'genkit';

const RefinePresentationGoalsInputSchema = z.object({
  inputText: z.string().describe('Unstructured text, notes, or a full script.'),
  uploadedFiles: z
    .array(
      z.string().describe(
        "Uploaded file references as public URLs (https://...) pointing to content in storage."
      )
    )
    .optional(),
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

Once you have a comprehensive understanding of the presentation's requirements, summarize the final plan and set finished=true in your structured response.

Here is some context on what makes a great presentation, use it to inform your questions and strategy:
START OF CONTEXT
[CONTEXT TRUNCATED FOR BREVITY]
END OF CONTEXT

User input: {{inputText}}
{{#if uploadedFiles}}
User uploaded files: {{uploadedFiles}}
{{/if}}

Ask a thoughtful clarifying question to better understand their presentation goals. Focus on one key aspect at a time.`,
});

const refinePresentationGoalsFlow = ai.defineFlow(
  {
    name: 'refinePresentationGoalsFlow',
    inputSchema: RefinePresentationGoalsInputSchema,
    outputSchema: RefinePresentationGoalsOutputSchema,
  },
  async input => {
    const response = await refinePresentationGoalsPrompt(input);
    return response;
  }
);