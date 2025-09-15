# ADK Agent Patterns for PresentationPro

## Table of Contents
1. [Core Agent Types](#core-agent-types)
2. [Basic LLM Agent Pattern](#basic-llm-agent-pattern)
3. [Workflow Agent Patterns](#workflow-agent-patterns)
4. [Custom Agent Pattern](#custom-agent-pattern)
5. [Multi-Agent Orchestration](#multi-agent-orchestration)
6. [Tool Integration Patterns](#tool-integration-patterns)
7. [State Management](#state-management)
8. [Callbacks and Events](#callbacks-and-events)
9. [Real-World Examples](#real-world-examples)

## Core Agent Types

ADK provides three main categories of agents:

### 1. LLM Agents
- Dynamic reasoning using language models
- Handle unstructured inputs
- Generate creative outputs

### 2. Workflow Agents
- Deterministic flow control
- Sequential, Parallel, or Loop execution
- Orchestrate multiple sub-agents

### 3. Custom Agents
- Extend BaseAgent for unique logic
- Implement custom control flows
- Handle complex business logic

## Basic LLM Agent Pattern

### Simple Agent Definition

```python
from google.adk.agents import Agent

# Basic pattern - Minimal agent
root_agent = Agent(
    name="slide_writer",
    model="gemini-2.0-flash",
    description="Generates slide content for presentations",
    instruction="""
    You are a professional slide writer. Create compelling slide content
    with clear headlines, concise bullet points, and engaging speaker notes.

    Rules:
    1. Headlines should be 5-7 words maximum
    2. Bullet points should be 10-15 words each
    3. Maximum 5 bullet points per slide
    4. Always include speaker notes

    Output format: JSON with structure:
    {
        "headline": "...",
        "bullets": ["...", "..."],
        "speaker_notes": "..."
    }
    """
)
```

### Advanced LLM Agent with Tools

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, WebSearch
from typing import List

class ResearchAgent:
    """Research agent that gathers information for presentations."""

    def __init__(self):
        self.agent = self._build_agent()

    def _build_agent(self) -> LlmAgent:
        return LlmAgent(
            name="research_agent",
            model="gemini-2.0-flash",
            description="Researches topics for presentations",
            instruction=self._get_instruction(),
            tools=self._get_tools(),
            temperature=0.3,  # Lower for factual research
            max_output_tokens=2000
        )

    def _get_instruction(self) -> str:
        return """
        You are a research specialist for presentations.

        Your process:
        1. Search for authoritative sources on the topic
        2. Extract key facts, statistics, and quotes
        3. Verify information from multiple sources
        4. Organize findings by relevance

        Always cite sources with URLs.
        Focus on recent information (last 2 years preferred).
        """

    def _get_tools(self) -> List:
        return [
            google_search,
            WebSearch(
                allowed_domains=["wikipedia.org", "scholar.google.com"],
                max_results=10
            )
        ]

# Export for ADK
research = ResearchAgent()
root_agent = research.agent
```

## Workflow Agent Patterns

### Sequential Agent Pattern

```python
from google.adk.agents import SequentialAgent, LlmAgent

# Define sub-agents
clarifier = LlmAgent(
    name="clarifier",
    model="gemini-2.0-flash",
    description="Clarifies presentation requirements",
    instruction="Ask questions to understand the presentation needs..."
)

outliner = LlmAgent(
    name="outliner",
    model="gemini-2.0-flash",
    description="Creates presentation outline",
    instruction="Create a structured outline based on requirements..."
)

writer = LlmAgent(
    name="writer",
    model="gemini-2.0-flash",
    description="Writes slide content",
    instruction="Write detailed content for each slide..."
)

# Sequential workflow
root_agent = SequentialAgent(
    name="presentation_creator",
    sub_agents=[clarifier, outliner, writer],
    description="Creates presentations step by step",
    pass_output=True  # Pass output from one agent to next
)
```

### Parallel Agent Pattern

```python
from google.adk.agents import ParallelAgent, LlmAgent

# Define parallel sub-agents
content_writer = LlmAgent(
    name="content_writer",
    model="gemini-2.0-flash",
    description="Writes slide content",
    instruction="Create slide content..."
)

image_generator = LlmAgent(
    name="image_generator",
    model="gemini-2.0-flash",
    description="Generates image prompts",
    instruction="Create image generation prompts..."
)

notes_writer = LlmAgent(
    name="notes_writer",
    model="gemini-2.0-flash",
    description="Writes speaker notes",
    instruction="Create detailed speaker notes..."
)

# Parallel execution
root_agent = ParallelAgent(
    name="parallel_content_creator",
    sub_agents=[content_writer, image_generator, notes_writer],
    description="Creates all content simultaneously",
    merge_outputs=True  # Combine outputs
)
```

### Loop Agent Pattern

```python
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.core import Event, EventActions, InvocationContext
from typing import AsyncGenerator

class CheckCondition(BaseAgent):
    """Custom agent to check loop termination."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # Check if all slides are processed
        slides_done = ctx.session.state.get("slides_processed", 0)
        total_slides = ctx.session.state.get("total_slides", 10)

        is_done = slides_done >= total_slides

        yield Event(
            author=self.name,
            actions=EventActions(escalate=is_done)
        )

# Sub-agents for loop
slide_processor = LlmAgent(
    name="slide_processor",
    model="gemini-2.0-flash",
    description="Processes one slide",
    instruction="Process the current slide...",
    output_key="slide_content"
)

slide_reviewer = LlmAgent(
    name="slide_reviewer",
    model="gemini-2.0-flash",
    description="Reviews slide quality",
    instruction="Review the slide and mark as complete or needs revision...",
    output_key="review_status"
)

# Loop agent
root_agent = LoopAgent(
    name="slide_loop_processor",
    sub_agents=[
        slide_processor,
        slide_reviewer,
        CheckCondition(name="check_done")
    ],
    description="Processes slides one by one",
    max_iterations=20,
    after_agent_callback=lambda ctx: modify_output_after_agent(ctx)
)
```

## Custom Agent Pattern

### BaseAgent Extension

```python
from google.adk.agents import BaseAgent
from google.adk.core import (
    Event, EventActions, InvocationContext,
    ToolCall, ToolOutput
)
from typing import AsyncGenerator
import asyncio

class OrchestratorAgent(BaseAgent):
    """Custom orchestrator with complex logic."""

    def __init__(self, name: str, remote_agents: dict):
        super().__init__(name=name)
        self.remote_agents = remote_agents
        self.description = "Orchestrates multiple remote agents"

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Custom orchestration logic."""

        # Get user request
        user_request = ctx.inputs.get("request", "")

        # Analyze request to determine which agents to use
        required_agents = self._analyze_request(user_request)

        # Execute agents in optimal order
        results = {}
        for agent_name in required_agents:
            # Create tool call for remote agent
            tool_call = ToolCall(
                name="send_message",
                arguments={
                    "remote_agent_name": agent_name,
                    "user_request": user_request,
                    "context": results  # Pass previous results
                }
            )

            # Yield tool call event
            yield Event(
                author=self.name,
                tool_calls=[tool_call]
            )

            # Wait for tool output
            # (In real implementation, this would be handled by framework)
            await asyncio.sleep(0.1)

            # Store result
            results[agent_name] = "agent_output_here"

        # Final event with complete results
        yield Event(
            author=self.name,
            content=self._format_results(results),
            actions=EventActions(escalate=True)
        )

    def _analyze_request(self, request: str) -> list:
        """Determine which agents are needed."""
        agents = []

        if "research" in request.lower():
            agents.append("research_agent")
        if "outline" in request.lower():
            agents.append("outline_agent")
        if "slides" in request.lower():
            agents.append("slide_writer_agent")

        # Default flow if no specific request
        if not agents:
            agents = ["clarifier", "outliner", "slide_writer"]

        return agents

    def _format_results(self, results: dict) -> str:
        """Format final output."""
        return f"Completed presentation with {len(results)} agents"

# Usage
root_agent = OrchestratorAgent(
    name="orchestrator",
    remote_agents={
        "research_agent": "http://localhost:10001",
        "outline_agent": "http://localhost:10002",
        "slide_writer_agent": "http://localhost:10003"
    }
)
```

## Multi-Agent Orchestration

### Complex Multi-Agent System

```python
from google.adk.agents import Agent, LoopAgent, LlmAgent
from google.adk.core import CallbackContext
from google.adk import types
import logging

logger = logging.getLogger(__name__)

# Define specialized agents
profile_agent = LlmAgent(
    name="profile_agent",
    model="gemini-2.0-flash",
    description="Analyzes user profile and preferences",
    instruction="""
    Analyze the user's presentation history and preferences.
    Extract style preferences, common topics, and audience types.
    """,
    tools=[get_user_profile, get_past_presentations]
)

summary_agent = LlmAgent(
    name="summary_agent",
    model="gemini-2.0-flash",
    description="Summarizes findings",
    instruction="""
    Create a comprehensive summary of all gathered information.
    Highlight key insights and recommendations.
    """,
    output_key="summary"
)

quality_check_agent = LlmAgent(
    name="quality_check",
    model="gemini-2.0-flash",
    description="Checks if quality standards are met",
    instruction="""
    Review the presentation for:
    1. Completeness (all sections present)
    2. Consistency (style, tone, formatting)
    3. Accuracy (facts, citations)
    4. Engagement (storytelling, visuals)

    Output: 'approved' or 'needs_revision'
    """,
    output_key="quality_status"
)

# Callback to handle loop results
def modify_output_after_agent(callback_context: CallbackContext):
    """Extract final summary from state."""

    agent_name = callback_context.agent_name
    current_state = callback_context.state.to_dict()

    logger.info(f"[Callback] Exiting agent: {agent_name}")

    # Check if quality approved
    status = current_state.get("quality_status", "").strip()
    is_approved = (status == "approved")

    if is_approved:
        # Get final summary
        final_summary = current_state.get("summary")

        if final_summary:
            logger.info("[Callback] Quality approved, returning summary")

            return types.Content(
                role="model",
                parts=[types.Part(text=final_summary.strip())]
            )

    logger.warning("[Callback] Quality not approved or no summary")
    return None

# Main orchestration loop
root_agent = LoopAgent(
    name="presentation_pipeline",
    sub_agents=[
        profile_agent,
        summary_agent,
        quality_check_agent,
        CheckCondition(name="quality_checker")
    ],
    description="Complete presentation creation pipeline",
    max_iterations=3,  # Max 3 revision cycles
    after_agent_callback=modify_output_after_agent
)
```

## Tool Integration Patterns

### Native ADK Tools

```python
from google.adk.tools import (
    google_search,
    code_execution,
    grounding
)

agent_with_tools = Agent(
    name="research_agent",
    model="gemini-2.0-flash",
    description="Research agent with multiple tools",
    instruction="Research the topic thoroughly...",
    tools=[
        google_search,
        code_execution,
        grounding
    ]
)
```

### Custom Tool Definition

```python
from google.adk.tools import Tool
from typing import Dict, Any

def analyze_presentation_metrics(
    presentation_id: str,
    metrics: list = ["engagement", "clarity", "impact"]
) -> Dict[str, Any]:
    """Analyze presentation performance metrics."""

    # Implementation here
    results = {
        "engagement": 0.85,
        "clarity": 0.92,
        "impact": 0.78,
        "recommendations": [
            "Add more visuals",
            "Simplify complex slides"
        ]
    }

    return results

# Register as tool
metrics_tool = Tool(
    function=analyze_presentation_metrics,
    name="analyze_metrics",
    description="Analyzes presentation performance"
)

# Use in agent
agent = Agent(
    name="analytics_agent",
    model="gemini-2.0-flash",
    description="Analyzes presentation effectiveness",
    instruction="Analyze the presentation and provide improvement suggestions...",
    tools=[metrics_tool]
)
```

### MCP Tool Integration

```python
from google.adk.tools.mcp import MCPToolset, SseServerParams

# Connect to MCP server
mcp_tools = MCPToolset(
    connection_params=SseServerParams(
        url="http://localhost:8080/sse",
        headers={"Authorization": "Bearer token"}
    )
)

# Agent with MCP tools
agent = Agent(
    name="mcp_agent",
    model="gemini-2.0-flash",
    description="Agent using MCP tools",
    instruction="Use available tools to complete tasks...",
    tools=[mcp_tools]
)
```

## State Management

### Using Session State

```python
from google.adk.agents import Agent, Runner
from google.adk.services import InMemorySessionService

class StatefulAgent:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.agent = self._build_agent()
        self.runner = self._build_runner()

    def _build_agent(self) -> Agent:
        return Agent(
            name="stateful_agent",
            model="gemini-2.0-flash",
            description="Agent with persistent state",
            instruction="""
            Track conversation history and maintain context.
            Store important information in state for later use.
            """,
            before_agent_callback=self.load_state,
            after_agent_callback=self.save_state
        )

    def _build_runner(self) -> Runner:
        return Runner(
            app_name="presentation_app",
            agent=self.agent,
            session_service=self.session_service
        )

    def load_state(self, context):
        """Load state before agent execution."""
        state = context.session.state

        # Access previous values
        slides_created = state.get("slides_created", 0)
        current_section = state.get("current_section", "introduction")

        logger.info(f"Loaded state: {slides_created} slides, section: {current_section}")

    def save_state(self, context):
        """Save state after agent execution."""
        state = context.session.state

        # Update state
        state["slides_created"] = state.get("slides_created", 0) + 1
        state["last_updated"] = datetime.now().isoformat()

        logger.info("State saved")
```

## Callbacks and Events

### Event Handling

```python
from google.adk.core import Event, EventActions
from google.adk.agents import Agent

class EventDrivenAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        # Emit progress event
        yield Event(
            author=self.name,
            content="Starting presentation generation...",
            event_type="progress",
            metadata={"step": 1, "total": 5}
        )

        # Process...
        await self.process_step_1()

        # Emit completion event
        yield Event(
            author=self.name,
            content="Step 1 complete",
            event_type="step_complete",
            metadata={"step": 1}
        )

        # Tool call event
        yield Event(
            author=self.name,
            tool_calls=[
                ToolCall(
                    name="generate_outline",
                    arguments={"topic": "AI in Healthcare"}
                )
            ]
        )

        # Final event with escalation
        yield Event(
            author=self.name,
            content="Presentation complete",
            actions=EventActions(
                escalate=True,
                store_in_memory=True
            )
        )
```

### Callback Patterns

```python
def before_agent_callback(context: CallbackContext):
    """Called before agent execution."""
    logger.info(f"Starting {context.agent_name}")

    # Modify inputs
    if "topic" in context.inputs:
        context.inputs["topic"] = context.inputs["topic"].upper()

def after_agent_callback(context: CallbackContext):
    """Called after agent execution."""
    logger.info(f"Completed {context.agent_name}")

    # Modify outputs
    output = context.user_content
    if output:
        return types.Content(
            role="model",
            parts=[types.Part(text=f"[PROCESSED] {output}")]
        )

def after_tool_callback(context: CallbackContext):
    """Called after tool execution."""
    tool_name = context.tool_name
    result = context.tool_output

    logger.info(f"Tool {tool_name} returned: {result}")

# Apply callbacks
agent = Agent(
    name="callback_agent",
    model="gemini-2.0-flash",
    description="Agent with callbacks",
    instruction="Process the request...",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    after_tool_callback=after_tool_callback
)
```

## Real-World Examples

### PresentationPro Complete Agent

```python
from google.adk.agents import Agent, LoopAgent, LlmAgent
from google.adk.tools import google_search
from typing import List, Dict, Any
import json

class PresentationProAgent:
    """Complete presentation generation agent."""

    def __init__(self):
        self.agents = self._build_agents()
        self.root_agent = self._build_orchestrator()

    def _build_agents(self) -> Dict[str, Agent]:
        """Build all specialized agents."""

        agents = {}

        # Clarifier Agent
        agents["clarifier"] = LlmAgent(
            name="clarifier",
            model="gemini-2.0-flash",
            description="Refines presentation requirements",
            instruction="""
            You are a presentation consultant. Ask targeted questions to understand:
            1. Target audience (executives, students, technical, general)
            2. Presentation duration (5, 10, 20, 30+ minutes)
            3. Key messages (3-5 main points)
            4. Desired outcome (inform, persuade, teach, inspire)
            5. Visual style preferences

            Ask ONE question at a time. After 3-5 questions, summarize the requirements.
            """,
            temperature=0.7
        )

        # Outline Agent
        agents["outline"] = LlmAgent(
            name="outline",
            model="gemini-2.0-flash",
            description="Creates presentation structure",
            instruction="""
            Create a detailed presentation outline with:

            1. Title Slide
            2. Agenda/Overview
            3. Introduction (hook, context, thesis)
            4. Main Content Sections (3-5 sections)
               - Section title
               - Key points (3-5 per section)
               - Supporting evidence
               - Transitions
            5. Conclusion (summary, call-to-action)
            6. Q&A Slide

            Output as JSON:
            {
                "title": "...",
                "duration_minutes": 20,
                "sections": [
                    {
                        "title": "...",
                        "slides": [...],
                        "duration": 5
                    }
                ]
            }
            """,
            temperature=0.5
        )

        # Slide Writer Agent
        agents["slide_writer"] = LlmAgent(
            name="slide_writer",
            model="gemini-2.0-flash",
            description="Generates slide content",
            instruction="""
            Generate slide content following these rules:

            HEADLINE:
            - 5-7 words maximum
            - Action-oriented
            - Clear value proposition

            CONTENT:
            - 3-5 bullet points
            - 10-15 words per bullet
            - Parallel structure
            - No full sentences

            SPEAKER NOTES:
            - 2-3 paragraphs
            - Conversational tone
            - Include transitions
            - Add engagement techniques

            VISUALS:
            - Suggest relevant images/charts
            - Describe layout

            Output as JSON for each slide.
            """,
            temperature=0.6,
            tools=[google_search]
        )

        # Critic Agent
        agents["critic"] = LlmAgent(
            name="critic",
            model="gemini-2.0-flash",
            description="Reviews and improves slides",
            instruction="""
            Review each slide for:

            1. CLARITY (0-10): Is the message clear?
            2. IMPACT (0-10): Will it engage the audience?
            3. CONSISTENCY (0-10): Does it fit the overall narrative?
            4. VISUAL APPEAL (0-10): Is it visually balanced?

            Provide specific improvements for scores below 8.

            Output format:
            {
                "slide_id": "...",
                "scores": {...},
                "improvements": [...],
                "revised_content": {...}
            }
            """,
            temperature=0.3
        )

        # Research Agent
        agents["research"] = LlmAgent(
            name="research",
            model="gemini-2.0-flash",
            description="Gathers supporting information",
            instruction="""
            Research the presentation topic to find:

            1. Latest statistics and data
            2. Relevant case studies
            3. Expert quotes
            4. Industry trends
            5. Compelling stories

            Focus on credible sources from the last 2 years.
            Always include source URLs.

            Output as structured JSON with categories.
            """,
            temperature=0.2,
            tools=[google_search]
        )

        return agents

    def _build_orchestrator(self) -> LoopAgent:
        """Build main orchestration agent."""

        # Quality check condition
        class QualityCheck(BaseAgent):
            async def _run_async_impl(self, ctx: InvocationContext):
                quality_score = ctx.session.state.get("quality_score", 0)
                is_complete = quality_score >= 8.0

                yield Event(
                    author=self.name,
                    actions=EventActions(escalate=is_complete)
                )

        # Orchestration loop
        return LoopAgent(
            name="presentation_orchestrator",
            sub_agents=[
                self.agents["clarifier"],
                self.agents["research"],
                self.agents["outline"],
                self.agents["slide_writer"],
                self.agents["critic"],
                QualityCheck(name="quality_check")
            ],
            description="Complete presentation generation pipeline",
            max_iterations=3,
            after_agent_callback=self._extract_final_presentation
        )

    def _extract_final_presentation(self, context: CallbackContext):
        """Extract final presentation from state."""

        state = context.state.to_dict()

        presentation = {
            "title": state.get("title"),
            "outline": state.get("outline"),
            "slides": state.get("slides", []),
            "speaker_notes": state.get("speaker_notes", {}),
            "research": state.get("research", {}),
            "quality_score": state.get("quality_score", 0)
        }

        return types.Content(
            role="model",
            parts=[types.Part(text=json.dumps(presentation, indent=2))]
        )

# Initialize and export
presentation_pro = PresentationProAgent()
root_agent = presentation_pro.root_agent
agents = list(presentation_pro.agents.values())
```

## Best Practices

### 1. Agent Naming
- Use descriptive, lowercase names with underscores
- Include agent role in name (e.g., `research_agent`, `outline_generator`)

### 2. Instruction Design
- Be specific and detailed
- Include output format requirements
- Provide examples when possible
- Set clear constraints and rules

### 3. Temperature Settings
- Creative tasks: 0.7-0.9
- Analytical tasks: 0.3-0.5
- Factual/research: 0.1-0.3

### 4. Tool Selection
- Only include necessary tools
- Consider tool execution time
- Implement caching for expensive operations

### 5. Error Handling
- Implement retry logic for critical agents
- Provide fallback options
- Log errors comprehensively

### 6. State Management
- Keep state minimal and relevant
- Clean up old state regularly
- Use state for context, not data storage

### 7. Testing
- Test each agent independently
- Test agent interactions
- Validate output formats
- Monitor token usage