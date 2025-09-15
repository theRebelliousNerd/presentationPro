'use server';

/**
 * @fileOverview A flow to generate slide content (title, body, speaker notes, and image prompt) from an outline.
 *
 * - generateSlideContent - A function that generates the slide content.
 * - GenerateSlideContentInput - The input type for the generateSlideContent function.
 * - GenerateSlideContentOutput - The return type for the generateSlideContent function.
 */

// import {ai} from '@/ai.deprecated_genkit/genkit'; // Archived - do not use
import {z} from 'genkit';

const GenerateSlideContentInputSchema = z.object({
  outline: z
    .array(z.string())
    .describe('An array of slide titles representing the presentation outline.'),
  assets: z
    .array(
      z.object({
        name: z.string(),
        url: z.string(),
        kind: z.enum(['image', 'document', 'other']).optional(),
      })
    )
    .optional()
    .describe('Uploaded user assets (documents, images) to use for context or slide media.'),
  existing: z
    .array(
      z.object({
        title: z.string(),
        content: z.array(z.string()).optional(),
        speakerNotes: z.string().optional(),
      })
    )
    .optional()
    .describe('Existing slide content to improve or refine'),
});
export type GenerateSlideContentInput = z.infer<typeof GenerateSlideContentInputSchema>;

const SlideSchema = z.object({
  title: z.string().describe('The title of the slide.'),
  content: z
    .array(z.string())
    .min(1)
    .max(4)
    .describe('An array of 1-4 strings for bullet points on the slide.'),
  speakerNotes: z.string().describe('Speaker notes in short paragraphs and concise bullet points to guide the presenter.'),
  imagePrompt: z
    .string()
    .describe(
      'A detailed, descriptive image prompt suitable for an image generation model.'
    ),
  useAssetImageUrl: z.string().nullable().optional().describe('If provided, use this uploaded asset URL as the slide background image instead of generating one.'),
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

  You are also given a list of uploaded user assets (documents, images). Use these as primary context and cite them logically when appropriate. If an uploaded image is suitable as the main visual for a slide, set useAssetImageUrl to that image URL and provide a modest imagePrompt that complements it; otherwise, leave useAssetImageUrl null and provide a strong imagePrompt for generation.

  Speaker notes should be concise: a few bullets and short guiding paragraphs, focused on cues, not scripts.

  If existing slide content is provided, improve and refine it, keeping the same intent while enhancing clarity and narrative flow. Preserve any critical facts and use assets where appropriate.

  START OF CONTEXT
  [CONTEXT TRUNCATED FOR BREVITY]
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