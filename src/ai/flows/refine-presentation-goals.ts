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

Once you have a comprehensive understanding of the presentation's requirements, summarize the final plan and output a ---FINISHED--- token.

Here is some context on what makes a great presentation, use it to inform your questions and strategy:
START OF CONTEXT
A summary of "The Orator's Crucible: An Analytical History of the World's Greatest Presenters":
- Core Competencies: Audience Centricity, Narrative Structure, Emotional Resonance (pathos), Credibility/Confidence (ethos), Clarity/Logic (logos).
- Key Insight: Greatness is not born, it's made through deliberate practice.
- Techniques from the Masters:
  - Socrates: The Presenter as Inquisitor; co-creates understanding through dialogue and questioning.
  - Demosthenes: Forged eloquence through sheer will; known for vigorous, passionate style and powerful calls to action.
  - Cicero: The Architect of Rhetoric; master of logos, pathos, and ethos. Goal: to teach, to delight, and to move.
  - Martin Luther: The Plain-Spoken Revolutionary; used simple, direct, conversational style.
  - Queen Elizabeth I: Oratory as an Instrument of Rule; used strategic, paradoxical rhetoric and inclusive language.
  - Leonardo da Vinci: Presented the unseen world through visual thinking (saper vedere).
  - Abraham Lincoln: The Eloquence of Honesty; used profound simplicity, logical clarity, and a humble persona.
  - Frederick Douglass: The Voice of Lived Experience; combined classical rhetoric with the moral authority of his own story.
  - Susan B. Anthony: The Logic of Liberation; relied on incisive logical arguments (logos) and constitutional syllogism.
  - Steve Jobs: The Ultimate Product Evangelist; used minimalist visuals, the rule of three, and hero/villain storytelling.
  - Bill Gates: The Evolution of a Pragmatic Presenter; evolved from data-heavy to simplified, problem-solution narratives.
  - Brené Brown: The Power of Vulnerable Presentation; uses authentic, personal, and humorous storytelling.
  - Barack Obama: The Oratory of Unity; uses unifying narrative, allusion, and parallelism.
  - Malala Yousafzai: The Clarity of Courageous Conviction; uses her powerful personal story and simple, direct language.
END OF CONTEXT

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
