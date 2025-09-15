# Deprecated Genkit Backend Archive

**⚠️ DEPRECATED CODE - DO NOT USE ⚠️**

This directory contains the archived Genkit-based AI backend that was replaced by the ADK/A2A architecture in December 2024.

## Why This Code Was Archived

The original Genkit backend (`src/ai/`) was deprecated and replaced for the following reasons:

### 1. Architecture Limitations
- **Single-process design**: All AI logic ran within the Next.js application, creating tight coupling
- **Limited scalability**: Difficult to scale AI processing independently from the web frontend
- **No agent orchestration**: Simple flows without sophisticated multi-agent coordination

### 2. Migration to ADK/A2A
The new architecture provides significant advantages:
- **Multi-agent orchestration**: Specialized agents (Clarifier, Outline, SlideWriter, Critic, etc.)
- **Agent-to-Agent protocol**: Sophisticated coordination between AI agents
- **Microservices architecture**: Separate FastAPI backend (`adkpy/`) for AI processing
- **Graph RAG integration**: ArangoDB for advanced document retrieval and knowledge management
- **Better error handling**: Robust error recovery and agent supervision

### 3. Performance and Reliability
- **Better resource management**: Isolated AI processing from web serving
- **Improved caching**: Better token usage tracking and optimization
- **Enhanced debugging**: Separate logs and monitoring for AI operations

## What Was Replaced

### Files Archived
- `dev.ts` - Genkit development server entry point
- `genkit.ts` - Genkit configuration and initialization
- `flows/generate-and-edit-images.ts` - Image generation flow
- `flows/generate-presentation-outline.ts` - Outline generation flow
- `flows/generate-slide-content.ts` - Slide content generation flow
- `flows/refine-presentation-goals.ts` - Goal refinement chat flow
- `flows/rephrase-speaker-notes.ts` - Speaker notes rephrasing flow

### New ADK/A2A Implementation
The functionality is now implemented in:
- `adkpy/` - Python FastAPI backend with ADK agents
- `src/lib/orchestrator.ts` - ADK backend client
- `src/lib/actions.ts` - Server actions routing to ADK
- Docker services for scalable deployment

## Migration Timeline

- **Before December 2024**: Genkit-based single-process architecture
- **December 2024**: Migration to ADK/A2A multi-agent architecture
- **Current**: Genkit code archived, ADK/A2A in production

## Environment Variables (Historical)

The old system used these environment variables (now obsolete):
```bash
ORCH_MODE=local  # Used Genkit flows instead of ADK
```

Current system uses:
```bash
ORCH_MODE=adk    # Uses ADK/A2A architecture
ADK_BASE_URL=http://adkpy:8088  # ADK backend URL
```

## Dependencies Removed

The following packages were removed during migration:
- `genkit` - Core Genkit framework
- `genkit-cli` - Genkit CLI tools
- `@genkit-ai/googleai` - Google AI plugin for Genkit
- `@genkit-ai/next` - Next.js integration for Genkit

## Do Not Use This Code

This archived code is provided for:
- **Historical reference** - Understanding the evolution of the architecture
- **Learning purposes** - Studying the differences between architectures
- **Recovery scenarios** - Emergency reference if needed (should not be necessary)

**Important**: Do not attempt to restore or use this code. It is incompatible with the current system and lacks the sophisticated features of the ADK/A2A implementation.

## Current Architecture

For current development, refer to:
- `CLAUDE.md` - Current project documentation
- `adkpy/` - ADK backend implementation
- `ADK_INTEGRATION_COMPLETE.md` - Migration documentation

The current ADK/A2A architecture provides superior performance, scalability, and features compared to this deprecated Genkit implementation.