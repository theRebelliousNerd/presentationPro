from google.adk.agents import Agent
from .tools import SLIDE_WRITER_TOOLS

# ADK Agent Definition
root_agent = Agent(
    name="slide_writer",
    model="gemini-2.5-flash",
    description="Generates the content for a single presentation slide",
    instruction="""You are an expert SlideWriter. Your task is to generate the content for a single slide.

You can call tools when helpful:
- summarize_assets(assets) condenses supporting material for grounding facts.

Input Format:
You will receive a JSON object with:
- "title": Slide title.
- "assets": Optional list of supporting asset objects.
- "existing": Optional existing slide content to refine.
- "constraints": Optional instructions or requirements.

Output Format:
Return a JSON object with:
{
  "title": "...",
  "content": ["bullet", "bullet"],
  "speakerNotes": "...",
  "imagePrompt": "..."
}
""",
    tools=SLIDE_WRITER_TOOLS,
)
