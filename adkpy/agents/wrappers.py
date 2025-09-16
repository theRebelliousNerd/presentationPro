"""
Agent Wrapper Classes for ADK/A2A Integration

These wrapper classes bridge the gap between the FastAPI orchestrator and
the microservice-based agents. They handle model configuration propagation
and provide a simple interface for the orchestrator to use.
"""

from typing import Dict, Any, Optional, List
import json
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
    """Standard result format for all agents.

    'data' can be any JSON-serializable payload (dict, list, str, etc.).
    """
    data: Any
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
    presentationId: Optional[str] = Field(None, description="Presentation ID for context retrieval")
    assetContext: Optional[List[str]] = Field(None, description="Retrieved context snippets from assets")


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
            "Your task is to refine a user's request into clear presentation goals and pre-fill ALL form fields: parameters, advanced clarity, and presentation content.\n\n"
            "Process:\n"
            "1. Review the conversation history and the initial request.\n"
            "2. Consider uploaded assets and retrieved snippets; infer how each file should be used.\n"
            "3. Ask ONE targeted question per turn if needed, prioritizing:\n"
            "   - How to use specific files (content vs style/brand vs graphics)\n"
            "   - Target audience and background\n"
            "   - Presentation length and mode\n"
            "   - Industry/sub-industry and tone/style\n"
            "   - Key messages, constraints, and success criteria\n"
            "4. When sufficient info is available, provide a concise summary and a structured patch to the preference fields.\n\n"
            "Instructions:\n"
            "- If the user already provided content, keep it in 'text' and optionally refine it (do not discard).\n"
            "- If content is unstructured, summarize into bullet points under 'text'.\n"
            "- Tone sliders are integers 0..4 for formality and energy.\n"
            "- 'length' is one of short|medium|long.\n"
            "- Prefer brand colors/fonts from assets or design system if none given.\n\n"
            "Output Format (JSON only):\n"
            "{\n"
            '  "response": "Your clarifying question OR final summary of presentation requirements",\n'
            '  "finished": false,\n'
            '  "fileIntents": [ { "name": "brand-guidelines.pdf", "intent": "style", "notes": "Use colors & logo" } ],\n'
            '  "initialInputPatch": {\n'
            '     "text": "(preserved or refined content)",\n'
            '     "length": "short|medium|long",\n'
            '     "audience": "...",\n'
            '     "industry": "...",\n'
            '     "subIndustry": "...",\n'
            '     "tone": { "formality": 0, "energy": 0 },\n'
            '     "graphicStyle": "modern|minimalist|corporate|playful|elegant|retro|art-deco|turn-of-the-century",\n'
            '     "template": "enterprise|startup|academic|...",\n'
            '     "objective": "...",\n'
            '     "keyMessages": ["..."],\n'
            '     "mustInclude": ["..."],\n'
            '     "mustAvoid": ["..."],\n'
            '     "callToAction": "...",\n'
            '     "audienceExpertise": "beginner|intermediate|expert",\n'
            '     "timeConstraintMin": 20,\n'
            '     "successCriteria": ["..."],\n'
            '     "citationsRequired": false,\n'
            '     "slideDensity": "light|normal|dense",\n'
            '     "language": "en",\n'
            '     "locale": "en-US",\n'
            '     "readingLevel": "basic|intermediate|advanced",\n'
            '     "brandColors": ["#192940","#556273","#73BF50"],\n'
            '     "brandFonts": ["Montserrat","Roboto"],\n'
            '     "logoUrl": "...",\n'
            '     "presentationMode": "in-person|virtual|hybrid",\n'
            '     "screenRatio": "16:9|4:3|1:1",\n'
            '     "referenceStyle": "none|apa|mla|chicago",\n'
            '     "allowedSources": [".gov",".edu"],\n'
            '     "bannedSources": ["..."],\n'
            '     "animationLevel": "none|minimal|moderate|high"\n'
            '  }\n'
            "}"
        )

        history_transcript = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in data.history])

        # Include brief mention of attached assets
        files_desc = ", ".join([f.get("name") for f in (data.newFiles or []) if f.get("name")])
        prompt_parts = [
            system_prompt,
            f"\nInitial user request: '{initial_prompt}'",
            f"\nAttached files: {files_desc}" if files_desc else "\nNo files attached.",
            f"\nHere is the conversation history:\n{history_transcript}",
            ("\nRelevant context from uploaded assets (snippets):\n" + "\n---\n".join((data.assetContext or [])[:5])) if data.assetContext else "",
            "\nBased on all this, decide if you need to ask another question or if you can summarize. Then, provide the appropriate JSON output."
        ]

        text, usage = self.llm(prompt_parts)

        try:
            cleaned_text = text.strip().removeprefix("```json").removesuffix("```")
            obj = json.loads(cleaned_text)
            output_data = {
                "response": obj.get("response", ""),
                "finished": obj.get("finished", False),
            }
            patch = obj.get("initialInputPatch")
            if isinstance(patch, dict):
                output_data["initialInputPatch"] = patch
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
    audience: Optional[str] = Field(None, description="Target audience descriptor")
    tone: Optional[Any] = Field(None, description="Tone preferences or sliders")
    length: Optional[str] = Field(None, description="Desired outline length")
    template: Optional[str] = Field(None, description="Template preference")


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
            f"\nClarified presentation goals:\n{data.clarifiedContent}"
        ]
        if data.audience:
            prompt_parts.append(f"\nTarget audience: {data.audience}")
        if data.length:
            prompt_parts.append(f"\nDesired deck length: {data.length}")
        if data.template:
            prompt_parts.append(f"\nTemplate preference: {data.template}")
        if data.tone is not None:
            tone_value = data.tone
            if isinstance(tone_value, dict):
                formality = tone_value.get('formality')
                energy = tone_value.get('energy')
                if formality is not None and energy is not None:
                    tone_label = f"formality {formality}, energy {energy}"
                else:
                    tone_label = json.dumps(tone_value)
            else:
                tone_label = str(tone_value)
            prompt_parts.append(f"\nTone guidance: {tone_label}")
        prompt_parts.append("\nGenerate an appropriate outline with slide titles.")

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
        slides: List[Dict[str, Any]] = []
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_duration_ms = 0

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
            try:
                total_prompt_tokens += int(getattr(usage, "promptTokens", 0) or 0)
                total_completion_tokens += int(getattr(usage, "completionTokens", 0) or 0)
                total_duration_ms += int(getattr(usage, "durationMs", 0) or 0)
            except Exception:
                pass

        agg_usage = AgentUsage(
            model=self.model,
            promptTokens=total_prompt_tokens,
            completionTokens=total_completion_tokens,
            durationMs=total_duration_ms,
        )

        return AgentResult(data=slides, usage=agg_usage)


# ============= Critic Agent Wrapper =============

class CriticInput(BaseModel):
    """Input schema for CriticAgent."""
    slide: Dict[str, Any]
    audience: Optional[str] = None
    tone: Optional[str] = None
    textModel: Optional[str] = Field(None, description="Model to use for this request")
    presentationId: Optional[str] = Field(None, description="Presentation ID (for persistence)")
    slideIndex: Optional[int] = Field(None, description="Slide index (for persistence)")


class CriticAgent(BaseAgentWrapper):
    """Wrapper for the Critic microservice agent."""

    def run(self, data: CriticInput) -> AgentResult:
        """Critique and improve slide content."""
        if data.textModel:
            self.set_model(data.textModel)

        slide = data.slide or {}
        title = slide.get("title", "Untitled")
        content = slide.get("content", [])
        notes = slide.get("speakerNotes", "")

        system = (
            "You are a Critic agent for slide quality. Improve content while preserving intent.\n"
            "- 3–5 concise bullets\n- Avoid redundancy\n- Strong verbs\n- Consistent parallelism\n"
            "- Ensure notes are clear and actionable\n- Improve title clarity if needed\n\n"
            "Output JSON: {\n  \"slide\": {\"title\":..., \"content\": [...], \"speakerNotes\": ...},\n  \"review\": {\"issues\": [...], \"suggestions\": [...]}\n}"
        )

        prompt_parts = [
            system,
            f"Audience: {data.audience or 'general'}; Tone: {data.tone or 'neutral'}",
            f"Title: {title}",
            f"Bullets: {json.dumps(content)}",
            f"Notes: {notes}",
            "Return JSON only."
        ]

        text, usage = self.llm(prompt_parts)
        try:
            cleaned = text.strip().removeprefix("```json").removesuffix("```")
            obj = json.loads(cleaned)
            out_slide = obj.get("slide") or {
                "title": title,
                "content": content,
                "speakerNotes": notes,
            }
            review = obj.get("review") or {"issues": [], "suggestions": []}
            return AgentResult(data={"slide": out_slide, "review": review}, usage=usage)
        except Exception:
            return AgentResult(data={"slide": slide, "review": {"issues": [], "suggestions": []}}, usage=usage)


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
    preferLayout: Optional[bool] = False
    variants: Optional[int] = 0
    textModel: Optional[str] = Field(None, description="Model to use for this request")
    iconPack: Optional[str] = Field(None, description="Icon pack preference (lucide|tabler|heroicons)")
    screenshotDataUrl: Optional[str] = None


class DesignAgent(BaseAgentWrapper):
    """Wrapper for the Design microservice agent."""

    def run(self, data: DesignInput) -> AgentResult:
        """Generate design suggestions with model configuration."""
        if data.textModel:
            self.set_model(data.textModel)

        slide_title = data.slide.get("title", "Untitled")
        slide_content = data.slide.get("content", [])

        # Helper palettes per theme
        theme = (data.theme or 'brand').lower()
        palettes = {
            'brand': { 'bg': '#192940', 'primary': '#73BF50', 'muted': '#556273', 'text': '#FFFFFF' },
            'muted': { 'bg': '#3C4650', 'primary': '#D2D2D2', 'muted': '#6E7780', 'text': '#F0F0F0' },
            'dark':  { 'bg': '#121418', 'primary': '#5A6E82', 'muted': '#22282E', 'text': '#E0E0E0' },
        }
        colors = palettes.get(theme, palettes['brand'])
        spacing = 8
        radii = 12

        def make_background(pattern: str, intensity: float = 0.3):
            # Simple gradient + optional pattern overlay
            css_bg = "linear-gradient(135deg, rgba(102,126,234,0.35) 0%, rgba(118,75,162,0.35) 100%)"
            svg_overlay = None
            pat = (pattern or "").lower()
            if pat in ("topography", "hexagons", "grid", "dots", "wave", "shapes", "diagonal"):
                if pat == "topography":
                    svg_overlay = (
                        '<svg xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" viewBox="0 0 160 120">'
                        '<path d="M0,60 C40,40 120,80 160,60" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>'
                        '<path d="M0,90 C30,70 130,110 160,90" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>'
                        '<path d="M0,30 C50,20 110,40 160,30" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>'
                        '</svg>'
                    )
                elif pat == "hexagons":
                    svg_overlay = (
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 34.64">'
                        '<polygon points="20,0 40,10 40,24.64 20,34.64 0,24.64 0,10" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="1" />'
                        '</svg>'
                    )
                elif pat == "grid":
                    svg_overlay = (
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">'
                        '<path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1" />'
                        '</svg>'
                    )
                elif pat == "dots":
                    svg_overlay = (
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                        + ''.join([f'<circle cx="{(i*80)%1280}" cy="{(i*50)%720}" r="3" fill="rgba(255,255,255,0.06)" />' for i in range(0,60)])
                        + '</svg>'
                    )
                elif pat == "wave":
                    svg_overlay = (
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                        '<path d="M0,420 C320,320 560,520 1280,380 L1280,720 L0,720 Z" fill="rgba(255,255,255,0.08)" />'
                        '<path d="M0,520 C320,420 560,620 1280,480 L1280,720 L0,720 Z" fill="rgba(255,255,255,0.05)" />'
                        '</svg>'
                    )
                elif pat == "diagonal":
                    svg_overlay = (
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
                        '<rect width="10" height="20" fill="rgba(255,255,255,0.06)" />'
                        '</svg>'
                    )
                elif pat == "shapes":
                    svg_overlay = (
                        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
                        '<circle cx="192" cy="144" r="120" fill="rgba(255,255,255,0.12)" />'
                        '<rect x="900" y="420" width="260" height="260" rx="16" fill="rgba(255,255,255,0.06)" />'
                        '</svg>'
                    )
            return css_bg, svg_overlay, max(0.0, min(1.0, intensity))

        def make_layout():
            html = (
                "<section class=\"slide\">"
                "  <div class=\"pad\">"
                "    <h1 id=\"slot-title\"></h1>"
                "    <ul id=\"slot-bullets\"></ul>"
                "  </div>"
                "</section>"
            )
            css = (
                ".slide{position:absolute;inset:0;display:flex;align-items:center;}"
                ".slide .pad{width:80%;margin-left:10%;}"
                ".slide h1{color:var(--color-text-title, var(--color-text,#fff));font-family:var(--font-headline,Montserrat,sans-serif);font-weight:600;margin-bottom:calc(var(--space,8px)*2);}"
                ".slide ul{color:var(--color-text-body, var(--color-text,#fff));font-family:var(--font-body,Roboto,sans-serif);padding-left:24px;display:grid;row-gap:calc(var(--space,8px)*1.5);}"
            )
            slots = { 'title': '#slot-title', 'bullets': '#slot-bullets' }
            return html, css, slots

        if data.preferCode or data.preferLayout:
            # Generate CSS/SVG code for the slide. css = value suitable for `backgroundImage` style.
            css_bg, svg_overlay, intensity = make_background((data.pattern or "gradient"), 0.3)

            # Optional icon overlay
            try:
                from tools.assets_catalog_tool import get_icon_svg
                pack = (data.iconPack or "lucide").lower()
                # Heuristic: choose icon based on title/content
                t = (slide_title or "").lower() + " " + " ".join([str(x).lower() for x in slide_content])
                icon_candidates = [
                    ("light-bulb", ["idea", "insight", "tip", "strategy", "vision"]),
                    ("check", ["done", "complete", "benefit", "advantage", "success"]),
                    ("chart-bar", ["metric", "chart", "growth", "kpi", "results"]),
                    ("info", ["note", "info", "details", "learn"]),
                ]
                chosen = None
                for name, kws in icon_candidates:
                    if any(k in t for k in kws):
                        chosen = name
                        break
                chosen = chosen or "light-bulb"
                icon_svg = get_icon_svg(pack, chosen)
                if icon_svg:
                    # Strip outer <svg> wrapper roughly
                    inner = icon_svg
                    try:
                        s = icon_svg.find('>')
                        e = icon_svg.rfind('</svg>')
                        if s != -1 and e != -1:
                            inner = icon_svg[s+1:e]
                    except Exception:
                        pass
                    # Compose icon into overlay (top-right corner)
                    icon_group = f'<svg x="1120" y="40" width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
                    if svg_overlay and svg_overlay.startswith('<svg'):
                        # insert icon before closing
                        svg_overlay = svg_overlay[:-6] + icon_group + '</svg>'
                    else:
                        svg_overlay = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">{icon_group}</svg>'
            except Exception:
                pass
            # Compose designSpec and optional variants
            html, css, slots = make_layout() if data.preferLayout else (None, None, None)  # type: ignore
            design_spec = {
                "tokens": {
                    "colors": colors,
                    "typeScale": "normal",
                    "spacing": spacing,
                    "radii": radii,
                },
                "background": {
                    "css": css_bg,
                    "svg": svg_overlay,
                    "intensity": intensity,
                    "safeAreas": [{"x": 64, "y": 96, "w": 960, "h": 420}],
                },
            }
            if html and css and slots:
                design_spec["layout"] = { "type": "title_bullets_left", "html": html, "css": css, "slots": slots }

            variants = []
            try:
                n = max(0, min(int(data.variants or 0), 4))
                for i in range(n):
                    css_v, svg_v, inten_v = make_background((data.pattern or "gradient"), 0.2 + 0.1 * i)
                    variants.append({
                        "designSpec": {
                            **design_spec,
                            "background": { **design_spec["background"], "css": css_v, "svg": svg_v, "intensity": inten_v },
                        },
                        "variantId": f"v{i+1}",
                        "score": 0.7 + 0.05 * i,
                        "rationale": "Variant with adjusted intensity",
                    })
            except Exception:
                pass

            output_data = {
                "type": "code",
                "code": {"css": css_bg, "svg": svg_overlay},
                "designSpec": design_spec,
                "variants": variants,
            }
            # Optional VisionCV placement hints
            try:
                import os, httpx
                if os.environ.get('DESIGN_USE_VISIONCV', 'false').lower() == 'true' and (data.screenshotDataUrl or data.slide.get('screenshotDataUrl')):
                    base = os.environ.get('ADK_BASE_URL', 'http://localhost:8088')
                    url = (base or '').rstrip('/') + '/v1/visioncv/placement'
                    body = { 'screenshotDataUrl': data.screenshotDataUrl or data.slide.get('screenshotDataUrl') }
                    with httpx.Client(timeout=8.0) as client:
                        r = client.post(url, json=body)
                    if r.status_code == 200:
                        placement = r.json()
                        candidates = placement.get('candidates', []) or []
                        if candidates:
                            output_data.setdefault('designSpec', {})
                            output_data['designSpec']['placementCandidates'] = candidates
                            width = placement.get('width')
                            height = placement.get('height')
                            if isinstance(width, (int, float)) and isinstance(height, (int, float)):
                                output_data['designSpec']['placementFrame'] = { 'width': float(width), 'height': float(height) }
            except Exception:
                pass
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
            "Your task is to write a cohesive script for the entire presentation that references slide content and relevant supporting assets.\n\n"
            "Requirements:\n"
            "- Create smooth transitions between slides\n"
            "- Maintain consistent tone throughout\n"
            "- Call out when to reference provided assets (cite the asset name)\n"
            "- Include timing cues and emphasis points\n"
            "- Make it conversational and engaging\n\n"
            "Output Format:\n"
            "Return a JSON object with:\n"
            "{\n"
            '  "script": "Complete presentation script..."\n'
            "}\n"
        )

        slide_blocks = []
        for idx, slide in enumerate(data.slides or []):
            title = slide.get('title') or 'Untitled'
            bullets = slide.get('content') or []
            notes = slide.get('speakerNotes') or ''
            section_lines = [f"Slide {idx + 1}: {title}"]
            filtered_bullets = [b.strip() for b in bullets if isinstance(b, str) and b.strip()]
            if filtered_bullets:
                section_lines.append('Key points:')
                section_lines.extend([f"- {b}" for b in filtered_bullets])
            if isinstance(notes, str) and notes.strip():
                section_lines.append('Existing speaker notes:')
                section_lines.append(notes.strip())
            slide_blocks.append("
".join(section_lines))

        asset_lines = []
        for asset in data.assets or []:
            name = asset.get('name') or asset.get('url') or 'Asset'
            snippet = ''
            text_field = asset.get('text') or asset.get('summary')
            if isinstance(text_field, str) and text_field.strip():
                snippet = text_field.strip().replace('\r', ' ').replace('\n', ' ')[:400]
            kind = asset.get('kind') or asset.get('intent')
            descriptor = f" ({kind})" if kind else ''
            if snippet:
                asset_lines.append(f"{name}{descriptor}: {snippet}")
            else:
                asset_lines.append(f"{name}{descriptor}")

        prompt_parts = [system_prompt]
        if slide_blocks:
            prompt_parts.append("
Presentation slides with details:
" + "

".join(slide_blocks))
        if asset_lines:
            prompt_parts.append("
Reference assets available for the script:
" + "
".join(asset_lines))
        prompt_parts.append("
Generate a complete presentation script that references slides in order, transitions smoothly, and mentions assets when relevant.")

        text, usage = self.llm(prompt_parts)

        try:
            cleaned_text = text.strip().removeprefix("```json").removesuffix("```")
            obj = json.loads(cleaned_text)
            script_text = obj.get("script") or obj.get("data") or "Presentation script goes here."
            output_data = {"script": script_text}
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
    imageDataUrl: Optional[str] = None
    chartImageDataUrl: Optional[str] = None
    chartType: Optional[str] = None
    presentationId: Optional[str] = None


class ResearchAgent(BaseAgentWrapper):
    """Wrapper for the Research microservice agent."""

    def run(self, data: ResearchInput) -> AgentResult:
        """Perform research with ADK built-in tools when available, else fallback to WebSearchTool."""
        if data.textModel:
            self.set_model(data.textModel)

        query = (data.query or '').strip() or 'presentation design best practices'
        top_k = max(1, int(data.topK or 5))
        allow = data.allowDomains or []

        # Try ADK built-in Google Search tool first (Gemini 2 only), then fallback
        items: list[dict] = []
        used = 'fallback'
        try:
            # Lazy import; only available if google-adk is installed
            from agents.tools.google_search import GoogleSearchTool  # type: ignore
            gs = GoogleSearchTool()
            results = gs.search(query=query, max_results=top_k)
            for r in results or []:
                try:
                    url = getattr(r, 'url', None) or (r.get('url') if isinstance(r, dict) else None)
                    title = getattr(r, 'title', None) or (r.get('title') if isinstance(r, dict) else '')
                    snippet = getattr(r, 'snippet', None) or (r.get('snippet') if isinstance(r, dict) else '')
                    if url:
                        if allow:
                            from urllib.parse import urlparse
                            host = (urlparse(url).hostname or '').lower()
                            if not any(host.endswith(d.lower()) for d in allow):
                                continue
                        items.append({'title': title, 'url': url, 'snippet': snippet})
                except Exception:
                    continue
            used = 'adk_google_search'
        except Exception:
            # Fallback to internal WebSearchTool (Bing or DuckDuckGo)
            try:
                from tools.web_search_tool import WebSearchTool
                tool = WebSearchTool(allow_domains=allow)
                results = tool.search(query, top_k=top_k)
                items = [ {'title': r.title, 'url': r.url, 'snippet': r.snippet} for r in results ]
                used = 'web_search_tool'
            except Exception:
                items = []
                used = 'none'

        # Optional VisionCV assisted extraction
        extras: dict = {}
        try:
            import os, httpx
            base = os.environ.get('ADK_BASE_URL', 'http://localhost:8088')
            if os.environ.get('RESEARCH_USE_VISIONCV', 'false').lower() == 'true':
                with httpx.Client(timeout=8.0) as client:
                    if data.imageDataUrl:
                        try:
                            ocr = client.post((base.rstrip('/') + '/v1/visioncv/ocr'), json={ 'imageDataUrl': data.imageDataUrl }).json()
                            extras['ocr'] = { 'text': ocr.get('text',''), 'words': (ocr.get('words',[])[:50] if isinstance(ocr.get('words',[]), list) else []) }
                        except Exception:
                            pass
                    if data.chartImageDataUrl:
                        try:
                            if (data.chartType or '').lower() == 'bar':
                                res = client.post((base.rstrip('/') + '/v1/visioncv/bar_chart'), json={ 'imageDataUrl': data.chartImageDataUrl }).json()
                                extras['chart'] = res
                            elif (data.chartType or '').lower() == 'line':
                                res = client.post((base.rstrip('/') + '/v1/visioncv/line_graph'), json={ 'imageDataUrl': data.chartImageDataUrl }).json()
                                extras['chart'] = res
                        except Exception:
                            pass
        except Exception:
            pass

        # Synthesize concise design/strategy rules from results using the LLM
        prompt_parts = [
            "You are a presentation research assistant. Read the web results and create 5 concise, actionable rules.",
            "Each rule should be a short imperative phrase.",
            "Results:",
            "\n".join([f"- {it.get('title','')}: {it.get('snippet','')} ({it.get('url','')})" for it in items[:top_k]]) or "- No results",
            "Return JSON: { \"rules\": [\"...\", \"...\", \"...\"] }"
        ]
        text, usage = self.llm(prompt_parts)
        rules: list[str]
        try:
            import json as _json
            cleaned = text.strip().removeprefix('```json').removesuffix('```')
            obj = _json.loads(cleaned)
            rules = obj.get('rules') or []
        except Exception:
            rules = [
                'Use consistent color scheme',
                'Limit on-slide text; prefer visuals',
                'Keep headings clear and specific',
                'Maintain visual hierarchy and spacing',
                'Cite sources when appropriate',
            ]

        return AgentResult(
            data={ 'rules': rules, 'source': used, **({ 'extractions': extras } if extras else {}) },
            usage=usage
        )
