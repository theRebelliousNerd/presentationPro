# Gemini Presentation Studio

The Gemini Presentation Studio is a cutting-edge application designed to help you create stunning, AI-powered presentations with ease. This tool leverages the power of Gemini to transform your ideas, notes, and data into compelling visual stories.

At its core, the studio guides you through a seamless, multi-step process. You begin by providing your initial thoughts and context, which can include raw text, supporting documents, and even specific parameters like presentation length, audience type, tone, mood, and color scheme.

Next, you engage in a dynamic chat with an AI strategist. This conversational interface allows the AI to ask clarifying questions, ensuring it fully understands your goals. As you provide more information and upload additional files, a "Context Meter" gives you a sense of how well-developed the AI's understanding is, offering suggestions for further context.

Once the AI has a solid grasp of your objectives, it proposes a slide-by-slide outline for your approval. This gives you a clear roadmap of your presentation before any content is generated. With your go-ahead, the studio then generates the full presentation, complete with titles, bullet points, detailed speaker notes that create a narrative flow, and even descriptive prompts for AI-generated images for each slide.

The final stage is the editor, where you have full control to refine your presentation. You can edit text, regenerate images, rephrase speaker notes with different tones, and rearrange, add, or delete slides. The editor is a flexible and intuitive space to put the finishing touches on your AI-assisted creation.

This README provides an overview of the project's structure and key components, serving as a guide for developers looking to understand and extend its capabilities. Welcome to the future of presentation design!

## Docker

Run the app in Docker Desktop without installing Node locally.

Prerequisites:
- Docker Desktop installed and running
- `.env` file with `GOOGLE_GENAI_API_KEY=...`

Development (hot reload on port 3000):

```
docker compose up --build web
```

Optional: run the Genkit explorer/dev server alongside Next.js:

```
docker compose up --build web genkit
```

Production image build and run:

```
docker build -t presentation-studio:prod --target prod .
docker run --rm -p 3000:3000 --env-file .env presentation-studio:prod
```

Notes:
- Port 3000 is used in both dev and prod.
- The app reads `GOOGLE_GENAI_API_KEY` from environment for AI flows.
- In dev, the source directory is mounted into the container for live reload.
