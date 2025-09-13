'use server';
/**
 * @fileOverview AI functions for generating and editing images for slides.
 *
 * - generateAndEditImage - A function that generates and edits images based on a prompt and optional base image.
 * - GenerateAndEditImageInput - The input type for the generateAndEditImage function.
 * - GenerateAndEditImageOutput - The return type for the generateAndEditImage function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateAndEditImageInputSchema = z.object({
  prompt: z.string().describe('The prompt to use for generating or editing the image.'),
  baseImage: z
    .string()
    .optional()
    .describe(
      "The base image to edit, as a data URI that must include a MIME type and use Base64 encoding. Expected format: 'data:<mimetype>;base64,<encoded_data>'."
    ),
});
export type GenerateAndEditImageInput = z.infer<typeof GenerateAndEditImageInputSchema>;

const GenerateAndEditImageOutputSchema = z.object({
  imageUrl: z.string().describe('The URL of the generated or edited image.'),
});
export type GenerateAndEditImageOutput = z.infer<typeof GenerateAndEditImageOutputSchema>;

export async function generateAndEditImage(input: GenerateAndEditImageInput): Promise<GenerateAndEditImageOutput> {
  return generateAndEditImageFlow(input);
}

const generateAndEditImageFlow = ai.defineFlow(
  {
    name: 'generateAndEditImageFlow',
    inputSchema: GenerateAndEditImageInputSchema,
    outputSchema: GenerateAndEditImageOutputSchema,
  },
  async input => {
    const {prompt, baseImage} = input;

    let media;
    if (baseImage) {
      const response = await ai.generate({
        model: 'googleai/gemini-2.5-flash-image-preview',
        prompt: [
          {media: {url: baseImage}},
          {text: prompt},
        ],
        config: {
          responseModalities: ['TEXT', 'IMAGE'], // MUST provide both TEXT and IMAGE, IMAGE only won't work
        },
      });
      media = response.media;
    } else {
      const response = await ai.generate({
        model: 'googleai/imagen-4.0-generate-001',
        prompt: prompt,
      });
      media = response.media;
    }

    if (!media) {
      throw new Error('No image was generated.');
    }

    return {imageUrl: media.url};
  }
);
