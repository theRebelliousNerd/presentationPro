'use server';

/**
 * @fileOverview A flow to generate slide content (title, body, speaker notes, and image prompt) from an outline.
 *
 * - generateSlideContent - A function that generates the slide content.
 * - GenerateSlideContentInput - The input type for the generateSlideContent function.
 * - GenerateSlideContentOutput - The return type for the generateSlideContent function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateSlideContentInputSchema = z.object({
  outline: z
    .array(z.string())
    .describe('An array of slide titles representing the presentation outline.'),
});
export type GenerateSlideContentInput = z.infer<typeof GenerateSlideContentInputSchema>;

const SlideSchema = z.object({
  title: z.string().describe('The title of the slide.'),
  content: z
    .array(z.string())
    .min(1)
    .max(4)
    .describe('An array of 1-4 strings for bullet points on the slide.'),
  speakerNotes: z.string().describe('Detailed speaker notes for the slide that create a narrative flow.'),
  imagePrompt: z
    .string()
    .describe(
      'A detailed, descriptive image prompt suitable for an image generation model.'
    ),
});

const GenerateSlideContentOutputSchema = z.array(SlideSchema).describe('An array of slide objects.');
export type GenerateSlideContentOutput = z.infer<typeof GenerateSlideContentOutputSchema>;

export async function generateSlideContent(
  input: GenerateSlideContentInput
): Promise<GenerateSlideContentOutput> {
  return generateSlideContentFlow(input);
}

const prompt = ai.definePrompt({
  name: 'generateSlideContentPrompt',
  input: {schema: GenerateSlideContentInputSchema},
  output: {schema: GenerateSlideContentOutputSchema},
  prompt: `You are an expert presentation creator and storyteller. Given the outline below, create content for each slide.
  Use the provided context on great orators to inform the narrative flow, slide content, and speaker notes.

  START OF CONTEXT
  The Orator's Crucible: An Analytical History of the World's Greatest Presenters
  - Core Competencies: Audience Centricity, Narrative Structure, Emotional Resonance (pathos), Credibility/Confidence (ethos), Clarity/Logic (logos).
  - Key Insight: Greatness is not born, it's made through practice.
  - Techniques from the Masters:
    - Socrates: Questioning, interactive dialogue.
    - Demosthenes: Passionate, direct calls to action.
    - Cicero: Balance of logic, emotion, credibility (logos, pathos, ethos). Goal: teach, delight, move.
    - Martin Luther: Simplicity, direct and conversational style.
    - Queen Elizabeth I: Strategic, paradoxical rhetoric, inclusive language.
    - Abraham Lincoln: Simplicity, logical clarity, humble persona.
    - Frederick Douglass: Using lived experience and moral authority to expose hypocrisy.
    - Susan B. Anthony: Relentless logical arguments (logos).
    - Steve Jobs: Minimalist visuals, rule of three, hero/villain storytelling.
    - Brené Brown: Vulnerable, authentic, personal storytelling.
    - Barack Obama: Unifying narrative, allusion, parallelism.
    - Martin Luther King, Jr.: Anaphora (repetition), metaphor, moral/spiritual framing.
  END OF CONTEXT

  Outline:
  {{#each outline}}
  - {{{this}}}
  {{/each}}

  For each slide, generate:

  *   A concise title.
  *   An array of 1-4 bullet points summarizing the key information for the slide.
  *   Detailed speaker notes that not only explain the slide's content but also create a compelling narrative that flows smoothly from one slide to the next, telling a cohesive story throughout the presentation. The speaker notes should be crafted with the techniques of the great orators in mind.
  *   A descriptive image prompt that can be used to generate a relevant image for the slide.

  Return the result as a JSON array of slide objects. Each slide object should have the following structure:

  {
    "title": "Slide Title",
    "content": ["Bullet point 1", "Bullet point 2"],
    "speakerNotes": "Detailed notes for the presenter that connect this slide to the previous one and set up the next one.",
    "imagePrompt": "A descriptive image prompt"
  }

  Ensure that the output is valid JSON.
  `,
});

const generateSlideContentFlow = ai.defineFlow(
  {
    name: 'generateSlideContentFlow',
    inputSchema: GenerateSlideContentInputSchema,
    outputSchema: GenerateSlideContentOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
