import { config } from 'dotenv';
config();

import '@/ai/flows/refine-presentation-goals.ts';
import '@/ai/flows/generate-slide-content.ts';
import '@/ai/flows/generate-and-edit-images.ts';
import '@/ai/flows/rephrase-speaker-notes.ts';
import '@/ai/flows/generate-presentation-outline.ts';