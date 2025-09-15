"""
Agent Wrapper Classes for ADK/A2A Integration

These wrapper classes bridge the gap between the FastAPI orchestrator and
the microservice-based agents. They handle model configuration propagation
and provide a simple interface for the orchestrator to use.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json
import logging
from app.llm import call_text_model

logger = logging.getLogger(__name__)


# ============= Data Models =============

class AgentUsage(BaseModel):
    """Track agent usage metrics."""
    model: str
    promptTokens: int = 0
    completionTokens: int = 0
    durationMs: int = 0


class AgentResult(BaseModel):
    """Standard result format for all agents."""
    data: Dict[str, Any]
    usage: AgentUsage


# ============= Base Agent Wrapper =============

class BaseAgentWrapper:
    """
    Base wrapper class for all agents.
    Handles model configuration and LLM calls.
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize with optional model override."""
        self.default_model = "googleai/gemini-2.5-flash"
        self.model = model or self.default_model

    def set_model(self, model: Optional[str]):
        """Update the model configuration."""
        if model:
            self.model = model
            logger.info(f"Agent model set to: {model}")

    def llm(self, prompt_parts: List[str]) -> tuple[str, AgentUsage]:
        """
        Call the language model with the configured model.

        Args:
            prompt_parts: List of prompt strings

        Returns:
            Tuple of (response_text, usage_data)
        """
        text, usage_raw, duration_ms = call_text_model(self.model, prompt_parts)

        usage = AgentUsage(
            model=usage_raw.get("model", self.model),
            promptTokens=int(usage_raw.get("promptTokens", 0) or 0),
            completionTokens=int(usage_raw.get("completionTokens", 0) or 0),
            durationMs=int(duration_ms or usage_raw.get("durationMs", 0) or 0),
        )

        return text, usage


# ============= Clarifier Agent Wrapper =============

class ClarifierInput(BaseModel):
    """Input schema for ClarifierAgent."""
    history: List[Dict[str, Any]] = Field(description="Conversation history")
    initialInput: Dict[str, Any] = Field(description="Initial user request")
    newFiles: Optional[List[Dict[str, Any]]] = None
    textModel: Optional[str] = Field(None, description="Model to use for this request")


class ClarifierAgent(BaseAgentWrapper):
    """Wrapper for the Clarifier microservice agent."""

    def run(self, data: ClarifierInput) -> AgentResult:
        """Execute the clarifier logic with model configuration."""
        # Set model if provided in request
        if data.textModel:
            self.set_model(data.textModel)

        initial_prompt = (data.initialInput or {}).get("text", "").strip()
        asset_names = ", ".join([(f.get("name") or "") for f in (data.newFiles or []) if f])

        system_prompt = (
            "You are a Clarifier agent for presentation creation.\n\n"
            "Your task is to refine a user's vague request into clear presentation goals.\n\n"
            "Process:\n"
            "1. Review the conversation history and initial request\n"
            "2. If goals are unclear, ask ONE targeted question about:\n"
            "   - Target audience and their background\n"
            "   - Presentation length and format\n"
            "   - Key topics and messages to convey\n"
            "   - Tone and style preferences\n"
            "   - Success criteria and goals\n"
            "3. When you have sufficient information (usually after 3-5 questions), provide a clear summary\n\n"
            "Output Format:\n"
            "Return a JSON object with exactly these fields:\n"
            "{\n"
            '  "response": "Your clarifying question OR final summary of presentation requirements",\n'
            '  "finished": false  // Set to true ONLY when you have enough information to proceed\n'
            "}\n\n"
            "Important:\n"
            "- Ask only ONE question at a time\n"
            "- Be conversational and helpful\n"
            "- Focus on understanding the user's needs\n"
            "- Set finished=true only when you have clear, actionable requirements\n"
            "- Always return valid JSON"
        )

        history_transcript = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in data.history])

        prompt_parts = [
            system_prompt,
            f"\nInitial user request: '{initial_prompt}'",
            f"\nProvided assets: {asset_names}" if asset_names else "\nNo new assets provided.",
            f"\nHere is the conversation history:\n{history_transcript}",
            "\nBased on all this, decide if you need to ask another question or if you can summarize. Then, provide the appropriate JSON output."
        ]

        text, usage = self.llm(prompt_parts)

        try:
            cleaned_text = text.strip().removeprefix("```json").removesuffix("```")
            obj = json.loads(cleaned_text)
            output_data = {"response": obj.get("response", ""), "finished": obj.get("finished", False)}
        except (json.JSONDecodeError, TypeError):
            output_data = {
                "response": "I'm having trouble understanding. Could you please rephrase your goal?",
                "finished": False
            }

        return AgentResult(data=output_data, usage=usage)


# ============= Outline Agent Wrapper =============

class OutlineInput(BaseModel):
    """Input schema for OutlineAgent."""
    clarifiedContent: str = Field(description="Clarified presentation goals")
    textModel: Optional[str] = Field(None, description="Model to use for this request")


class OutlineAgent(BaseAgentWrapper):
    """Wrapper for the Outline microservice agent."""

    def run(self, data: OutlineInput) -> AgentResult:
        """Generate presentation outline with model configuration."""
        if data.textModel:
            self.set_model(data.textModel)

        system_prompt = (
            "You are an Outline agent that creates structured presentation outlines.\n\n"
            "Your task is to generate a list of slide titles based on the clarified goals.\n\n"
            "Requirements:\n"
            "- Create 5-15 slide titles depending on content depth\n"
            "- Include a title slide and conclusion slide\n"
            "- Ensure logical flow and progression\n"
            "- Keep titles concise but descriptive\n\n"
            "Output Format:\n"
            "Return a JSON object with an 'outline' array containing slide titles:\n"
            "{\n"
            '  "outline": ["Title Slide", "Introduction", "Main Point 1", ...]\n'
            "}"
        )

        prompt_parts = [
            system_prompt,
            f"\nClarified presentation goals:\n{data.clarifiedContent}",
            "\nGenerate an appropriate outline with slide titles."
        ]

        text, usage = self.llm(prompt_parts)

        try:
            cleaned_text = text.strip().removeprefix("```json").removesuffix("```")
            obj = json.loads(cleaned_text)
            output_data = {"outline": obj.get("outline", [])}
        except (json.JSONDecodeError, TypeError):
            output_data = {"outline": ["Title Slide", "Introduction", "Main Content", "Conclusion"]}

        return AgentResult(data=output_data, usage=usage)


# ============= SlideWriter Agent Wrapper =============

class SlideWriterInput(BaseModel):
    """Input schema for SlideWriterAgent."""
    clarifiedContent: Optional[str] = None
    outline: List[str]
    audience: Optional[str] = None
    tone: Optional[str] = None
    length: Optional[str] = None
    assets: Optional[List[Dict[str, Any]]] = None
    constraints: Optional[Any] = None
    existing: Optional[List[Dict[str, Any]]] = None
    writerModel: Optional[str] = Field(None, description="Model for writer agent")
    criticModel: Optional[str] = Field(None, description="Model for critic agent")
    textModel: Optional[str] = Field(None, description="Fallback model configuration")


class SlideWriterAgent(BaseAgentWrapper):
    """Wrapper for the SlideWriter microservice agent."""

    def run(self, data: SlideWriterInput) -> AgentResult:
        """Generate slide content with model configuration."""
        # Use writerModel if provided, otherwise fall back to textModel
        model = data.writerModel or data.textModel
        if model:
            self.set_model(model)

        # Generate slides for all titles in the outline
        slides = []
        total_usage = {"input_tokens": 0, "output_tokens": 0}

        for slide_title in data.outline:
            system_prompt = (
                "You are a SlideWriter agent that creates compelling presentation content.\n\n"
                "Your task is to generate content for a presentation slide.\n\n"
                "Requirements:\n"
                "- Create 3-5 bullet points for the slide content\n"
                "- Write detailed speaker notes (2-3 paragraphs)\n"
                "- Suggest an image prompt for visual enhancement\n"
                "- Match the specified tone and audience level\n\n"
                "Output Format:\n"
                "Return a JSON object with this structure:\n"
                "{\n"
                '  "title": "Slide Title",\n'
                '  "content": ["Bullet 1", "Bullet 2", ...],\n'
                '  "speakerNotes": "Detailed notes...",\n'
                '  "imagePrompt": "Visual description..."\n'
                "}"
            )

            context_parts = []
            if data.clarifiedContent:
                context_parts.append(f"Presentation goals: {data.clarifiedContent}")
            if data.audience:
                context_parts.append(f"Target audience: {data.audience}")
            if data.tone:
                context_parts.append(f"Tone: {data.tone}")
            if data.length:
                context_parts.append(f"Length preference: {data.length}")

            prompt_parts = [
                system_prompt,
                f"\nSlide title: {slide_title}",
                "\n" + "\n".join(context_parts) if context_parts else "",
                "\nGenerate appropriate content for this slide."
            ]

            text, usage = self.llm(prompt_parts)

            try:
                cleaned_text = text.strip().removeprefix("```json").removesuffix("```")
                obj = json.loads(cleaned_text)
                slide_data = {
                    "title": obj.get("title", slide_title),
                    "content": obj.get("content", ["Point 1", "Point 2", "Point 3"]),
                    "speakerNotes": obj.get("speakerNotes", ""),
                    "imagePrompt": obj.get("imagePrompt", "")
                }
            except (json.JSONDecodeError, TypeError):
                slide_data = {
                    "title": slide_title,
                    "content": ["Key point 1", "Key point 2", "Key point 3"],
                    "speakerNotes": "Speaker notes for this slide.",
                    "imagePrompt": "Professional presentation slide background"
                }

            slides.append(slide_data)
            total_usage["input_tokens"] += usage.get("input_tokens", 0)
            total_usage["output_tokens"] += usage.get("output_tokens", 0)

        return AgentResult(data=slides, usage=total_usage)


# ============= Critic Agent Wrapper =============

class CriticInput(BaseModel):
    """Input schema for CriticAgent."""
    slide: Dict[str, Any]
    audience: Optional[str] = None
    tone: Optional[str] = None
    textModel: Optional[str] = Field(None, description="Model to use for this request")


class CriticAgent(BaseAgentWrapper):
    """Wrapper for the Critic microservice agent."""

    def run(self, data: CriticInput) -> AgentResult:
        """Critique and improve slide content."""
        if data.textModel:
            self.set_model(data.textModel)

        # For now, return the slide as-is (in production, would provide critique)
        return AgentResult(
            data=data.slide,
            usage=AgentUsage(model=self.model)
        )


# ============= NotesPolisher Agent Wrapper =============

class NotesPolisherInput(BaseModel):
    """Input schema for NotesPolisherAgent."""
    speakerNotes: str
    tone: str = "professional"
    textModel: Optional[str] = Field(None, description="Model to use for this request")


class NotesPolisherAgent(BaseAgentWrapper):
    """Wrapper for the NotesPolisher microservice agent."""

    def run(self, data: NotesPolisherInput) -> AgentResult:
        """Polish speaker notes with model configuration."""
        if data.textModel:
            self.set_model(data.textModel)

        system_prompt = (
            f"You are a NotesPolisher agent that refines speaker notes.\n\n"
            f"Your task is to rephrase the speaker notes in a {data.tone} tone.\n\n"
            "Requirements:\n"
            "- Maintain the key information and message\n"
            "- Improve clarity and flow\n"
            "- Adjust language for the specified tone\n"
            "- Keep approximately the same length\n\n"
            "Output Format:\n"
            "Return a JSON object with:\n"
            "{\n"
            '  "rephrasedSpeakerNotes": "Polished notes..."\n'
            "}"
        )

        prompt_parts = [
            system_prompt,
            f"\nOriginal speaker notes:\n{data.speakerNotes}",
            f"\nRephrase these notes in a {data.tone} tone."
        ]

        text, usage = self.llm(prompt_parts)

        try:
            cleaned_text = text.strip().removeprefix("```json").removesuffix("```")
            obj = json.loads(cleaned_text)
            output_data = {"rephrasedSpeakerNotes": obj.get("rephrasedSpeakerNotes", data.speakerNotes)}
        except (json.JSONDecodeError, TypeError):
            output_data = {"rephrasedSpeakerNotes": data.speakerNotes}

        return AgentResult(data=output_data, usage=usage)


# ============= Design Agent Wrapper =============

class DesignInput(BaseModel):
    """Input schema for DesignAgent."""
    slide: Dict[str, Any]
    theme: Optional[str] = None
    pattern: Optional[str] = None
    preferCode: Optional[bool] = False
    textModel: Optional[str] = Field(None, description="Model to use for this request")


class DesignAgent(BaseAgentWrapper):
    """Wrapper for the Design microservice agent."""

    def run(self, data: DesignInput) -> AgentResult:
        """Generate design suggestions with model configuration."""
        if data.textModel:
            self.set_model(data.textModel)

        slide_title = data.slide.get("title", "Untitled")
        slide_content = data.slide.get("content", [])

        if data.preferCode:
            # Generate CSS/SVG code for the slide
            output_data = {
                "type": "code",
                "code": {
                    "css": f"/* CSS for {slide_title} */\n.slide {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}",
                    "svg": f'<svg viewBox="0 0 100 100"><text x="50" y="50">{slide_title}</text></svg>'
                }
            }
        else:
            # Generate image prompt
            theme_desc = f" with {data.theme} theme" if data.theme else ""
            pattern_desc = f" using {data.pattern} pattern" if data.pattern else ""

            prompt = f"Professional presentation slide{theme_desc}{pattern_desc} for '{slide_title}'"
            output_data = {
                "type": "prompt",
                "prompt": prompt
            }

        return AgentResult(
            data=output_data,
            usage=AgentUsage(model=self.model)
        )


# ============= ScriptWriter Agent Wrapper =============

class ScriptWriterInput(BaseModel):
    """Input schema for ScriptWriterAgent."""
    slides: List[Dict[str, Any]]
    assets: Optional[List[Dict[str, Any]]] = None
    textModel: Optional[str] = Field(None, description="Model to use for this request")


class ScriptWriterAgent(BaseAgentWrapper):
    """Wrapper for the ScriptWriter microservice agent."""

    def run(self, data: ScriptWriterInput) -> AgentResult:
        """Generate presentation script with model configuration."""
        if data.textModel:
            self.set_model(data.textModel)

        system_prompt = (
            "You are a ScriptWriter agent that creates presentation scripts.\n\n"
            "Your task is to write a cohesive script for the entire presentation.\n\n"
            "Requirements:\n"
            "- Create smooth transitions between slides\n"
            "- Maintain consistent tone throughout\n"
            "- Include timing cues and emphasis points\n"
            "- Make it conversational and engaging\n\n"
            "Output Format:\n"
            "Return a JSON object with:\n"
            "{\n"
            '  "script": "Complete presentation script..."\n'
            "}"
        )

        slides_summary = "\n".join([
            f"Slide {i+1}: {s.get('title', 'Untitled')}"
            for i, s in enumerate(data.slides)
        ])

        prompt_parts = [
            system_prompt,
            f"\nPresentation slides:\n{slides_summary}",
            "\nGenerate a complete presentation script."
        ]

        text, usage = self.llm(prompt_parts)

        try:
            cleaned_text = text.strip().removeprefix("```json").removesuffix("```")
            obj = json.loads(cleaned_text)
            output_data = {"script": obj.get("script", "Presentation script goes here.")}
        except (json.JSONDecodeError, TypeError):
            output_data = {"script": "Welcome to this presentation. Let's begin..."}

        return AgentResult(data=output_data, usage=usage)


# ============= Research Agent Wrapper =============

class ResearchInput(BaseModel):
    """Input schema for ResearchAgent."""
    query: Optional[str] = None
    topK: Optional[int] = 5
    allowDomains: Optional[List[str]] = None
    textModel: Optional[str] = Field(None, description="Model to use for this request")


class ResearchAgent(BaseAgentWrapper):
    """Wrapper for the Research microservice agent."""

    def run(self, data: ResearchInput) -> AgentResult:
        """Perform research with model configuration."""
        if data.textModel:
            self.set_model(data.textModel)

        # For now, return placeholder rules
        # In production, would use web search and other tools
        output_data = {
            "rules": [
                "Use consistent color scheme throughout",
                "Limit text to 6 lines per slide",
                "Include relevant visuals on each slide"
            ]
        }

        return AgentResult(
            data=output_data,
            usage=AgentUsage(model=self.model)
        )