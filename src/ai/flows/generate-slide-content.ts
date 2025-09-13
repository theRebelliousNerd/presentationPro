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
  The Orator's Crucible: An Analytical History of the World's Greatest Presenters
Introduction: The Anatomy of Oratorical Excellence
The capacity to stand before an audience and, through the power of the spoken word, alter perspectives, inspire action, or reshape the course of history is one of humanity's most formidable skills. From the stone assemblies of ancient Athens to the glowing stages of the digital age, the principles of effective presentation have been studied, codified, and revered. This report undertakes a comprehensive analysis of history's most masterful presenters, examining not only their celebrated performances but also the intricate machinery of their methods, the philosophical underpinnings of their communication, and the core personality traits that animated their public personae.

To establish a consistent framework for this longitudinal study, it is essential to define the universal components of oratorical mastery. A synthesis of rhetorical theory and modern communication science reveals a set of core competencies that transcend time and technology. First and foremost is Audience Centricity, the profound ability to analyze an audience—their beliefs, their fears, their needs—and meticulously tailor the message to resonate with them. This is intrinsically linked to    

Narrative Structure, the art of "telling a story" with a clear purpose, a logical flow, and a compelling call to action that provides the audience with a clear destination.   

Beyond structure lies the crucial element of Emotional Resonance, the classical concept of pathos. This is the presenter's capacity to forge a genuine connection, build rapport, and stir the emotions of the audience through expressive vocal tones, deliberate body language, and evocative storytelling. This connection is fortified by    

Credibility and Confidence, or ethos, the projection of authority, authenticity, and control that engenders trust and makes a message believable. Finally, these elements must be built upon a foundation of    

Clarity and Logic—logos—a well-reasoned, content-rich argument that is both persuasive and easy to comprehend. _BAR_ 

A central theme that emerges from the study of these masters is the fundamental fallacy of the "natural-born orator." The historical record consistently demonstrates that oratorical excellence is not a gift bestowed by nature but a craft forged in the crucible of deliberate, often obsessive, practice. Figures who are often mythologized for their innate genius are, upon closer inspection, revealed to be paragons of industry who overcame significant personal and professional obstacles. This suggests that the single most important trait of a great presenter is not effortless charisma, but an unyielding determination to master the art of communication. Their greatness was not born; it was made.

Chapter 1: The Founders of Persuasion - Orators of Ancient History
The classical world established a foundational principle that endures to this day: effective public speaking is not mere performance but a deeply intellectual, strategic, and civic discipline. The codification of rhetoric by figures like Cicero was not an abstract academic pursuit but the creation of a practical toolkit for wielding influence and power within the state. For the ancients, oratory was inseparable from statecraft and intellectual rigor, a stark contrast to modern perceptions of public speaking as a "soft skill." They viewed communication as the central pillar of governance. This understanding was sharpened by the high-stakes environment in which they operated. The greatest orators of antiquity were defined by their responses to profound personal and political crises. Demosthenes honed his skills to defend Athens from existential threat, while Cicero delivered his most famous speeches to protect the Republic from internal conspiracy. This pattern reveals that the pressure of crisis forces a clarity of purpose and an emotional intensity that forges transcendent oratory, a dynamic that would reappear centuries later in the speeches of wartime leaders and revolutionaries.   

Socrates: The Presenter as Inquisitor
Socrates (c. 470–399 BCE) revolutionized the concept of public discourse by transforming it from a monologue of pronouncements into a dynamic, interactive dialogue. He presented not by lecturing, but by questioning.

Techniques and Style
Socrates's singular technique was the Socratic Method, or elenchus—a disciplined, argumentative dialogue designed to scrutinize deeply held beliefs through relentless inquiry. In practice, this involved the instructor feigning ignorance of a topic to engage students or interlocutors in a shared exploration of a concept. His "presentations" were co-created in real time with his audience, a back-and-forth exchange where he would pose a thought-provoking question, elicit a response, and then use further questions to dissect that response, exposing its underlying assumptions and inconsistencies. This method was highly active and participatory, demanding that his "audience" become collaborators in the pursuit of knowledge.   

Philosophy and Preparation
Socrates's philosophy of communication was predicated on the belief that true knowledge is not transmitted from teacher to student but is discovered within the self through rigorous examination. He believed that "all thinking comes from asking questions" and that the goal of dialogue was not to win an argument but to achieve a shared, more coherent understanding of moral and ethical truths. His preparation, therefore, was not about memorizing a speech but about formulating the perfect initial question—one that was concrete and relatable to his students' experiences—and then anticipating the logical pathways and subsidiary questions that would guide the conversation toward its conclusion. _BAR_ 

Personality and Persona
Socrates's public persona was that of an intellectually humble yet persistently curious questioner. He subverted the traditional role of the "sage on the stage," instead presenting himself as an explorer ignorant of the final destination but expert in navigating the journey. This persona, famously captured in Plato's dialogues, was enigmatic and often infuriating to his contemporaries, as his method relentlessly exposed the intellectual complacency of Athens's prominent citizens. His personality was defined by an absolute commitment to intellectual honesty and self-examination, a conviction so profound that he ultimately chose execution over abandoning his public mission of inquiry.   

Demosthenes: Forging Eloquence Through Sheer Will
Demosthenes (384–322 BCE) stands as the ultimate testament to the power of perseverance in the face of profound natural limitations. His journey from a physically frail youth with a debilitating speech impediment to the greatest orator of ancient Athens exemplifies the principle that mastery is a product of industry, not innate genius.

Techniques and Style
Demosthenes was renowned for a vigorous, astute, and intensely passionate style that could seamlessly blend different rhetorical approaches to suit his purpose. He was a master of engaging his audience directly, famously using rhetorical questions to create a sense of shared urgency and deliberation, as in his    

Philippics against the Macedonian king: "Will you still ask, Athenians, what Philip is doing?". He employed repetition and parallel structures to emphasize key points and build momentum toward a powerful call to action. His speeches were not abstract exercises in eloquence; they were practical, patriotic, and urgent appeals framed around the core themes of Athenian liberty and the dire consequences of political apathy and inaction. _BAR_ 

Philosophy and Preparation
Demosthenes's entire philosophy of communication was forged by his early, humiliating failures in the Athenian Assembly, where he was derided for his "perplexed and indistinct utterance and a shortness of breath". This led him to the conviction that oratorical power was owed entirely to "labor and industry". His preparation was the stuff of legend—an obsessive, all-consuming regimen designed to re-engineer his physical capabilities. He practiced speaking with pebbles in his mouth to correct his stammer, declaimed verses while running uphill to strengthen his breath control, and shouted over the roar of the sea to increase his vocal power. So that he would not be tempted to leave his studies, he built an underground chamber and shaved half his head, ensuring his humiliating appearance would confine him to his practice for months at a time. This extreme discipline reflected a philosophy of total preparation; he was known to be reluctant to speak extemporaneously, preferring to have every argument meticulously studied and rehearsed. .
The Gemini Presentation Studio is a cutting-edge application designed to help you create stunning, AI-powered presentations with ease. This tool leverages the power of Gemini to transform your ideas, notes, and data into compelling visual stories.

At its core, the studio guides you through a seamless, multi-step process. You begin by providing your initial thoughts and context, which can include raw text, supporting documents, and even specific parameters like presentation length, audience type, tone, mood, and color scheme.

Next, you engage in a dynamic chat with an AI strategist. This conversational interface allows the AI to ask clarifying questions, ensuring it fully understands your goals. As you provide more information and upload additional files, a "Context Meter" gives you a sense of how well-developed the AI's understanding is, offering suggestions for further context.

Once the AI has a solid grasp of your objectives, it proposes a slide-by-slide outline for your approval. This gives you a clear roadmap of your presentation before any content is generated. With your go-ahead, the studio then generates the full presentation, complete with titles, bullet points, detailed speaker notes that create a narrative flow, and even descriptive prompts for AI-generated images for each slide.

The final stage is the editor, where you have full control to refine your presentation. You can edit text, regenerate images, rephrase speaker notes with different tones, and rearrange, add, or delete slides. The editor is a flexible and intuitive space to put the finishing touches on your AI-assisted creation.

This README provides an overview of the project's structure and key components, serving as a guide for developers looking to understand and extend its capabilities. Welcome to the future of presentation design!
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
