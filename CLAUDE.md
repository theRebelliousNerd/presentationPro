# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Next-Gen Presentation Studio - an AI-powered presentation creation tool using Next.js, TypeScript, and Google Genkit AI. The app guides users through creating presentations via AI assistance, from initial input through clarification, outline approval, content generation, and editing.

## Development Commands

```bash
# Development server (runs on port 3000 - DO NOT CHANGE)
npm run dev

# Genkit AI development server
npm run genkit:dev
npm run genkit:watch  # With auto-reload

# Build and production
npm run build
npm run start

# Code quality
npm run lint
npm run typecheck
```

## Architecture Overview

### Application Flow States
The app progresses through distinct states (`src/lib/types.ts`):
1. `initial` - User provides text, files, presentation parameters
2. `clarifying` - AI chat to refine goals
3. `approving` - User reviews generated outline
4. `generating` - AI creates slide content
5. `editing` - User refines presentation
6. `error` - Error handling state

### Core Structure

**AI Integration (`src/ai/`)**
- `genkit.ts` - Genkit configuration with Google AI (Gemini 2.5 Flash)
- `flows/` - AI workflows for presentation generation:
  - `refine-presentation-goals.ts` - Clarification chat
  - `generate-presentation-outline.ts` - Outline creation
  - `generate-slide-content.ts` - Content generation
  - `generate-and-edit-images.ts` - Image generation
  - `rephrase-speaker-notes.ts` - Notes editing

**State Management**
- `src/hooks/use-presentation-state.ts` - Custom hook managing presentation data and app state
- Data persisted in localStorage as `presentation` object

**Component Structure**
- `src/app/page.tsx` - Main orchestrator component
- `src/components/app/` - Application-specific components for each flow state
- `src/components/ui/` - Reusable UI components (shadcn/ui based)

### Design System

The app follows the Next-Gen Engineering brand guidelines:
- **Colors**: Deep Navy (#192940), Action Green (#73BF50), Slate Blue (#556273)
- **Typography**: Montserrat (headings), Roboto (body)
- **Spacing**: 8px grid system
- **Logo**: Located in `/public/Next-Gen-logos/`

### Key Dependencies
- **Next.js 15.3.3** with App Router
- **Genkit 1.14.1** for AI workflows
- **Google AI** for Gemini integration
- **Tailwind CSS** for styling
- **Radix UI** for accessible components
- **React Hook Form** with Zod validation

### Environment Setup

Required environment variable:
```
GOOGLE_GENAI_API_KEY=your_api_key_here
```

### Important Notes

- Port 3000 is hardcoded for the dev server - DO NOT CHANGE
- The app uses Turbopack in development for faster builds
- Images are generated asynchronously after slides are created
- Presentation data auto-saves to localStorage
- Firebase integration is configured but implementation details vary by deployment
- remember never to change port numbers