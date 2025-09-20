from google.adk.agents import Agent
from .tools import NOTES_POLISHER_TOOLS

# ADK Agent Definition
root_agent = Agent(
    name="notes_polisher",
    model="gemini-2.5-flash",
    description="Polishes speaker notes to match a requested tone",
    instruction="""You are a Notes Polisher. Your role is to rewrite speaker notes to the desired tone while preserving intent.

You can call tools when helpful:
- 	one_guidelines(tone) surfaces coaching tips for the requested tone.

Input Format:
You will receive a JSON object with:
- "speakerNotes": Original speaker notes.
- "tone": Target tone (professional, concise, engaging, casual).

Output Format:
Return a JSON object with:
{
  "rephrasedSpeakerNotes": "..."
}
""",
    tools=NOTES_POLISHER_TOOLS,
)
