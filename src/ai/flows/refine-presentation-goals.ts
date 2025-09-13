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

Here is some context on what makes a great presentation, use it to inform your questions and strategy:
START OF CONTEXT
The Orator's Crucible: An Analytical History of the World's Greatest Presenters
Introduction: The Anatomy of Oratorical Excellence
The capacity to stand before an audience and, through the power of the spoken word, alter perspectives, inspire action, or reshape the course of history is one of humanity's most formidable skills. From the stone assemblies of ancient Athens to the glowing stages of the digital age, the principles of effective presentation have been studied, codified, and revered. This report undertakes a comprehensive analysis of history's most masterful presenters, examining not only their celebrated performances but also the intricate machinery of their methods, the philosophical underpinnings of their communication, and the core personality traits that animated their public personae.

To establish a consistent framework for this longitudinal study, it is essential to define the universal components of oratorical mastery. A synthesis of rhetorical theory and modern communication science reveals a set of core competencies that transcend time and technology. First and foremost is Audience Centricity, the profound ability to analyze an audience—their beliefs, their fears, their needs—and meticulously tailor the message to resonate with them. This is intrinsically linked to

Narrative Structure, the art of "telling a story" with a clear purpose, a logical flow, and a compelling call to action that provides the audience with a clear destination.

Beyond structure lies the crucial element of Emotional Resonance, the classical concept of pathos. This is the presenter's capacity to forge a genuine connection, build rapport, and stir the emotions of the audience through expressive vocal tones, deliberate body language, and evocative storytelling. This connection is fortified by

Credibility and Confidence, or ethos, the projection of authority, authenticity, and control that engenders trust and makes a message believable. Finally, these elements must be built upon a foundation of

Clarity and Logic—logos—a well-reasoned, content-rich argument that is both persuasive and easy to comprehend.

A central theme that emerges from the study of these masters is the fundamental fallacy of the "natural-born orator." The historical record consistently demonstrates that oratorical excellence is not a gift bestowed by nature but a craft forged in the crucible of deliberate, often obsessive, practice. Figures who are often mythologized for their innate genius are, upon closer inspection, revealed to be paragons of industry who overcame significant personal and professional obstacles. This suggests that the single most important trait of a great presenter is not effortless charisma, but an unyielding determination to master the art of communication. Their greatness was not born; it was made.

Chapter 1: The Founders of Persuasion - Orators of Ancient History
The classical world established a foundational principle that endures to this day: effective public speaking is not mere performance but a deeply intellectual, strategic, and civic discipline. The codification of rhetoric by figures like Cicero was not an abstract academic pursuit but the creation of a practical toolkit for wielding influence and power within the state. For the ancients, oratory was inseparable from statecraft and intellectual rigor, a stark contrast to modern perceptions of public speaking as a "soft skill." They viewed communication as the central pillar of governance. This understanding was sharpened by the high-stakes environment in which they operated. The greatest orators of antiquity were defined by their responses to profound personal and political crises. Demosthenes honed his skills to defend Athens from existential threat, while Cicero delivered his most famous speeches to protect the Republic from internal conspiracy. This pattern reveals that the pressure of crisis forces a clarity of purpose and an emotional intensity that forges transcendent oratory, a dynamic that would reappear centuries later in the speeches of wartime leaders and revolutionaries.

Socrates: The Presenter as Inquisitor
Socrates (c. 470–399 BCE) revolutionized the concept of public discourse by transforming it from a monologue of pronouncements into a dynamic, interactive dialogue. He presented not by lecturing, but by questioning.

Techniques and Style
Socrates's singular technique was the Socratic Method, or elenchus—a disciplined, argumentative dialogue designed to scrutinize deeply held beliefs through relentless inquiry. In practice, this involved the instructor feigning ignorance of a topic to engage students or interlocutors in a shared exploration of a concept. His "presentations" were co-created in real time with his audience, a back-and-forth exchange where he would pose a thought-provoking question, elicit a response, and then use further questions to dissect that response, exposing its underlying assumptions and inconsistencies. This method was highly active and participatory, demanding that his "audience" become collaborators in the pursuit of knowledge.

Philosophy and Preparation
Socrates's philosophy of communication was predicated on the belief that true knowledge is not transmitted from teacher to student but is discovered within the self through rigorous examination. He believed that "all thinking comes from asking questions" and that the goal of dialogue was not to win an argument but to achieve a shared, more coherent understanding of moral and ethical truths. His preparation, therefore, was not about memorizing a speech but about formulating the perfect initial question—one that was concrete and relatable to his students' experiences—and then anticipating the logical pathways and subsidiary questions that would guide the conversation toward its conclusion.

Personality and Persona
Socrates's public persona was that of an intellectually humble yet persistently curious questioner. He subverted the traditional role of the "sage on the stage," instead presenting himself as an explorer ignorant of the final destination but expert in navigating the journey. This persona, famously captured in Plato's dialogues, was enigmatic and often infuriating to his contemporaries, as his method relentlessly exposed the intellectual complacency of Athens's prominent citizens. His personality was defined by an absolute commitment to intellectual honesty and self-examination, a conviction so profound that he ultimately chose execution over abandoning his public mission of inquiry.

Demosthenes: Forging Eloquence Through Sheer Will
Demosthenes (384–322 BCE) stands as the ultimate testament to the power of perseverance in the face of profound natural limitations. His journey from a physically frail youth with a debilitating speech impediment to the greatest orator of ancient Athens exemplifies the principle that mastery is a product of industry, not innate genius.

Techniques and Style
Demosthenes was renowned for a vigorous, astute, and intensely passionate style that could seamlessly blend different rhetorical approaches to suit his purpose. He was a master of engaging his audience directly, famously using rhetorical questions to create a sense of shared urgency and deliberation, as in his

Philippics against the Macedonian king: "Will you still ask, Athenians, what Philip is doing?". He employed repetition and parallel structures to emphasize key points and build momentum toward a powerful call to action. His speeches were not abstract exercises in eloquence; they were practical, patriotic, and urgent appeals framed around the core themes of Athenian liberty and the dire consequences of political apathy and inaction.

Philosophy and Preparation
Demosthenes's entire philosophy of communication was forged by his early, humiliating failures in the Athenian Assembly, where he was derided for his "perplexed and indistinct utterance and a shortness of breath". This led him to the conviction that oratorical power was owed entirely to "labor and industry". His preparation was the stuff of legend—an obsessive, all-consuming regimen designed to re-engineer his physical capabilities. He practiced speaking with pebbles in his mouth to correct his stammer, declaimed verses while running uphill to strengthen his breath control, and shouted over the roar of the sea to increase his vocal power. So that he would not be tempted to leave his studies, he built an underground chamber and shaved half his head, ensuring his humiliating appearance would confine him to his practice for months at a time. This extreme discipline reflected a philosophy of total preparation; he was known to be reluctant to speak extemporaneously, preferring to have every argument meticulously studied and rehearsed.

Personality and Persona
Demosthenes's personality was defined by an almost superhuman determination and a fierce, unwavering patriotism. His life story is one of overcoming immense personal obstacles through sheer force of will, a narrative that undoubtedly informed his public persona. In the Assembly, he projected an image of passionate and forceful conviction, becoming the leading voice of resistance against Macedonian expansionism. He was the embodiment of his message: a figure who, like Athens itself, could rise from a state of weakness to one of formidable strength through vigilance and effort.

Cicero: The Architect of Rhetoric
Marcus Tullius Cicero (106–43 BCE) was not only Rome's greatest orator but also its most important theorist of the art. He systematically codified the principles of persuasion, creating a comprehensive framework that has influenced Western thought for over two millennia.

Techniques and Style
Cicero's style was marked by its versatility and adaptability. He was a master of all three of Aristotle's modes of persuasion: logos (logic and reason), pathos (emotional appeal), and ethos (credibility and character). His delivery was a model of controlled power; he modulated his voice across a full scale of tones and used gestures that were impressive and erect but never extravagant. He could be rigorously logical in a legal case or powerfully emotional in a political speech, as demonstrated in his

Catiline Orations, where he masterfully played on the Senate's fear of conspiracy to expose and condemn his adversary. His prose was celebrated for its clarity, rhythm, and persuasive force.

Philosophy and Preparation
Cicero's most enduring contribution was his systematization of rhetoric into what became known as the five canons: Inventio (the discovery of arguments), Dispositio (the arrangement of arguments), Elocutio (the style and language), Memoria (memorization), and Pronuntiatio (delivery). This framework reveals his philosophy that a great presentation is a holistic creation, requiring as much intellectual labor in preparation as performative skill in delivery. He argued that the ideal orator must be a person of immense learning, possessing an "encyclopedic knowledge" and combining "the subtlety of the logician, the thoughts of the philosopher, a diction almost poetic... and the bearing almost of the consummate actor". His ultimate goal was to

docere, delectare, et movere—to teach, to delight, and to move the audience emotionally, recognizing that logic alone was insufficient for true persuasion. This philosophy was backed by an incredible work ethic; he was known for his industriousness, conducting thorough research and working late into the night to master his subjects.

Personality and Persona
Cicero's personality was a complex mixture of ambition, intellectual brilliance, and principled conviction. He was a staunch defender of the Roman Republic, a value for which he ultimately paid with his life. He was also remarkably self-aware, admitting in his writings to feeling "very nervous when I begin to speak," viewing each oration as a profound judgment not just of his ability but of his "character and honor". On the public stage, he projected a persona of supreme authority and intellect. Yet he was also a master of what modern scholars call "self-fashioning," capable of strategically adopting different personae—the fierce attacker, the loyal friend, the noble martyr—to navigate the treacherous political landscape of the late Republic.

Chapter 2: The Rebirth of the Word - Voices of the Renaissance
The Renaissance marked a critical expansion in the theater of public address. While the civic and legal forums of antiquity remained influential, the pulpit and the royal court emerged as dominant new stages for persuasive communication. This shift fundamentally altered the source of a speaker's authority. For Martin Luther, authority flowed not from civic election but from the interpretation of divine scripture, with the goal of spiritual salvation rather than political consensus. For Queen Elizabeth I, authority was derived from divine right, making her speeches potent instruments of statecraft designed to project power and command loyalty in a deeply patriarchal world. In this context, effective presentation often required sophisticated "persona management." As a female monarch, Elizabeth had to construct a paradoxical identity, acknowledging her gender's perceived weakness only to assert a king's strength, thereby neutralizing a potential liability and turning it into a rhetorical asset. Similarly, Luther, as a heretic challenging a monolithic church, adopted the persona of a plain-spoken servant of the common person to build trust and sidestep accusations of intellectual arrogance. For these figures, presentation was not just about conveying a message, but about strategically constructing an identity that allowed the message to be heard.

Martin Luther: The Plain-Spoken Revolutionary
Martin Luther (1483–1546), the seminal figure of the Protestant Reformation, was a revolutionary whose primary weapon was the spoken and written word. Though a theologian of immense intellectual depth, his power as a presenter lay in his radical commitment to simplicity.

Techniques and Style
Luther's preaching style was intentionally simple, direct, and conversational. Eyewitnesses reported that he spoke slowly but with "great vigor," producing a deeply moving effect on his congregation. He consciously rejected the ornate, complex structures of classical rhetoric that he had been taught, along with any use of scholarly languages like Greek or Hebrew in the pulpit. He was famously scornful of preachers like Zwingli who did so, believing it was his duty to speak in the plain German of the common people he called "Hansie and Betsy". His sermons were delivered extemporaneously, which naturally lent them a simpler, more accessible structure and allowed him to engage his listeners directly, reading their faces for signs of understanding or confusion and adjusting his message accordingly. His rhetoric was holistic, aiming to persuade both the mind (

intellectus) and the heart (affectus).

Philosophy and Preparation
Luther's philosophy of communication was fundamentally pastoral. He believed his role in the pulpit was to "lay bare the breasts and nourish the people with milk," a metaphor for making complex theological truths, like his doctrine of justification by faith, easily digestible for the average person. He argued that intricate theological debates should be reserved for scholars, not the Sunday sermon. This did not mean he devalued deep learning. On the contrary, he insisted that all preachers must be thoroughly "versed in the languages" of scripture to ensure their discourse had "freshness and force". For Luther, preparation involved profound scholarly immersion, but the act of presentation required a radical translation of that knowledge into the vernacular. He saw language as a sacred vessel, the "sheath where the knife of the Spirit is kept," and believed its highest purpose was clear, powerful proclamation.

Personality and Persona
Luther possessed a personality of immense passion, unwavering conviction, and frequent volatility. This complexity was reflected in his public personae. In the pulpit, he was the caring, pragmatic pastor, focused on comforting the "anxious consciences" of his flock with the "soothing balm of the Gospel". In his written works and disputations, however, he was a fierce and often sarcastic polemicist, whose pages could burn with "vitriol" for his theological opponents. This duality reveals a leader who was both a protective shepherd and a relentless warrior, a man whose deep love for his people was matched by his ferocious opposition to those he believed were leading them astray.

Queen Elizabeth I: Oratory as an Instrument of Rule
Queen Elizabeth I (1533–1603) reigned in an era where her gender was considered a fundamental disqualification for leadership. Her success as a monarch was inextricably linked to her mastery of rhetoric, which she wielded as a primary instrument of statecraft to legitimize her rule, inspire her subjects, and project an image of indomitable power.

Techniques and Style
Elizabeth's rhetorical style was highly strategic, sophisticated, and often built on paradox. Her most famous address, the Speech to the Troops at Tilbury in 1588, is a masterclass in the classical appeals. She established her

ethos (credibility) by appearing before her troops, ready to "live and die amongst you all". She evoked powerful

pathos (emotion) by appealing to their patriotism and casting the conflict as a defense of "my God, of my kingdom, and of my people". Her most brilliant technique was the use of antithesis to redefine her identity as a female ruler. She acknowledged the conventional view of her "weak and feeble woman" body only to immediately counter it by claiming to possess the "heart and stomach of a king, and of a king of England too". This masterstroke did not deny her gender but transcended it, claiming a masculine spirit of leadership that her audience could rally behind. She further built solidarity through the use of inclusive language like "we" and reinforced her personal commitment through repetition ("I myself will take up arms, I myself will be your general").

Philosophy and Communication
Elizabeth viewed communication as essential to her political survival and success. She understood that her power depended on her ability to manage her public image and shape the national narrative. In her dealings with Parliament, particularly on the sensitive issue of her marriage and the succession, she employed what has been termed "opaque rhetoric"—using complex, ambiguous, and Petrarchan-style prose to create purposeful uncertainty, thereby deferring pressure and maintaining her political autonomy. Her philosophy was not one of transparent self-revelation but of strategic self-representation, using language to control her political environment.

Personality and Persona
Elizabeth's speeches reveal a personality of immense courage, political shrewdness, and pragmatic intelligence. She was acutely aware of the patriarchal structures she had to navigate and was a master at manipulating its conventions to her advantage. She carefully constructed a public persona that was multifaceted and paradoxical. She was at once the maternal "loving" queen to her people and the powerful, authoritative monarch with the heart of a king. By embodying the medieval political theory of the "King's Two Bodies"—a mortal, natural body (female) and an immortal, political body (kingly)—she crafted a unique and powerful regal identity that allowed her to command the loyalty and respect of her nation.

Leonardo da Vinci: Presenting the Unseen World
Leonardo da Vinci (1452–1519) was a presenter of a different kind. His stage was not the public square but the private page, and his audience was primarily himself. His thousands of notebook pages represent one of history's most profound and sustained acts of communication—a visual dialogue between observation, intellect, and imagination.

Techniques and Style
Leonardo's primary presentation technique was visual thinking, guided by his principle of saper vedere ("knowing how to see"). He used drawing and diagramming not merely to illustrate finished ideas, but as his principal method of inquiry and explanation. A single page from his notebooks is a non-linear presentation, a fusion of art and science where meticulous anatomical drawings, complex engineering schematics, and personal observations coexist, annotated in his famous right-to-left mirror script. This method allowed for an unpredictable and associative pattern of ideas, capturing the simultaneous workings of a designer and a scientist. His paintings, too, were a form of public presentation, employing revolutionary techniques like

sfumato (the blurring of outlines) and three-quarter portraits to present a more realistic, psychologically complex, and humanistic vision of the world.

Philosophy and Preparation
Leonardo's philosophy of communication was rooted in the belief that sight was the "main avenue to knowledge". For him, art and science were not separate disciplines but two sides of the same coin: the quest to understand and represent the truth of the natural world. He believed that to draw a thing was to understand it. His preparation was a life of relentless, microscopic observation. He carried loose sheets of paper with him constantly, documenting everything he encountered—from the turbulence of water to the structure of a human skull—in an effort to wrest the secrets of creation from nature. His notebooks were not a polished final product but a dynamic, ongoing process of thinking on paper, a continuous presentation of his discoveries to his own inquisitive mind.

Personality and Persona
Leonardo's notebooks reveal a personality defined by an insatiable and boundless curiosity (Curiositá) and an intellect unconstrained by the conventions of his time. He was a systematic thinker who divided phenomena into ever smaller parts to understand the whole, yet he was also comfortable with ambiguity and paradox. The famous mirror script suggests a highly individualistic, perhaps even secretive, personality, more concerned with the personal act of discovery than with public acclaim. He was the archetypal "Renaissance Man," a figure whose genius lay in his ability to make connections across disparate fields, and whose personality was a perfect synthesis of the analytical rigor of a scientist and the profound creativity of an artist.
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
