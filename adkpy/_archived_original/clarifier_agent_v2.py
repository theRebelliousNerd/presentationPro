"""
ClarifierAgent - ADK Enhanced Version

This agent drives a targeted Q&A session to refine a user's presentation goals,
constraints, and success criteria using the ADK framework.
"""

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from adk import agent, tool
from adk.base_agent import BaseAgent, AgentResult


class ClarifierInput(BaseModel):
    """Input parameters for the ClarifierAgent."""
    history: List[Dict[str, Any]] = Field(
        description="The conversation history so far"
    )
    initialInput: Dict[str, Any] = Field(
        description="The user's initial request with text, audience, tone, etc."
    )
    newFiles: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional list of new files or assets provided"
    )
    contextMeter: Optional[float] = Field(
        default=0.25,
        description="Current understanding level (0.25 to 1.0)"
    )


class ClarifierOutput(BaseModel):
    """Structured output of the ClarifierAgent."""
    response: str = Field(
        description="The agent's response (question or final summary)"
    )
    finished: bool = Field(
        default=False,
        description="True when sufficient information is gathered"
    )
    contextMeter: float = Field(
        default=0.25,
        description="Updated understanding level"
    )
    refinedGoals: Optional[str] = Field(
        default=None,
        description="Final refined goals when finished"
    )


@agent(
    name="clarifier",
    version="2.0.0",
    description="Refines user goals through targeted questions to build comprehensive presentation requirements",
    category="llm",
    tools=["analyze_context", "generate_question", "summarize_goals"],
    examples=[
        {
            "input": {"initialInput": {"text": "I need a presentation about AI"}},
            "output": {"response": "What specific aspect of AI would you like to focus on? (e.g., machine learning, ethics, applications, history)", "finished": False}
        },
        {
            "input": {"history": [{"role": "user", "content": "Machine learning applications in healthcare"}]},
            "output": {"response": "Who is your target audience for this presentation? (e.g., medical professionals, tech experts, general public)", "finished": False}
        }
    ]
)
class ClarifierAgent(BaseAgent):
    """
    An ADK-enhanced agent that engages in dialogue to refine a user's goals
    before passing a structured summary to downstream agents.
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize the ClarifierAgent with ADK enhancements."""
        super().__init__(model)
        self.question_templates = [
            "What is the primary goal or message you want to convey?",
            "Who is your target audience?",
            "How long should the presentation be?",
            "What tone or style would you prefer?",
            "Are there specific topics or sections you want to include?",
            "What level of technical detail is appropriate?",
            "Do you have any visual style preferences?",
            "What is the context or event for this presentation?",
            "Are there any constraints or requirements I should know about?",
            "How will success be measured for this presentation?"
        ]

    @tool("analyze_context", description="Analyze the current conversation context and understanding level")
    def analyze_context(self, history: List[Dict[str, Any]], initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the conversation context to determine understanding level.

        Returns:
            Dict with context analysis including understanding percentage
        """
        # Count meaningful exchanges
        user_messages = [msg for msg in history if msg.get('role') == 'user']
        assistant_messages = [msg for msg in history if msg.get('role') == 'assistant']

        # Analyze initial input richness
        initial_text = initial_input.get('text', '')
        has_audience = 'audience' in initial_text.lower() or initial_input.get('audience')
        has_tone = 'tone' in initial_text.lower() or initial_input.get('tone')
        has_duration = any(word in initial_text.lower() for word in ['minute', 'hour', 'slide', 'long'])

        # Calculate understanding level
        base_understanding = 0.25
        understanding_increment = 0.15

        # Add for initial input richness
        if len(initial_text) > 100:
            base_understanding += 0.1
        if has_audience:
            base_understanding += 0.05
        if has_tone:
            base_understanding += 0.05
        if has_duration:
            base_understanding += 0.05

        # Add for conversation depth
        total_understanding = base_understanding + (len(user_messages) * understanding_increment)

        # Cap at 1.0
        total_understanding = min(1.0, total_understanding)

        return {
            "understanding_level": total_understanding,
            "message_count": len(history),
            "has_audience": has_audience,
            "has_tone": has_tone,
            "has_duration": has_duration,
            "needs_more_info": total_understanding < 0.7
        }

    @tool("generate_question", description="Generate the next clarifying question based on context")
    def generate_question(self, context_analysis: Dict[str, Any], history: List[Dict[str, Any]]) -> str:
        """
        Generate an appropriate clarifying question.

        Returns:
            The next question to ask
        """
        # Check what's already been asked
        asked_questions = []
        for msg in history:
            if msg.get('role') == 'assistant':
                content = msg.get('content', '').lower()
                asked_questions.append(content)

        # Determine next question based on what's missing
        if not context_analysis.get('has_audience') and 'audience' not in ' '.join(asked_questions):
            return "Who is your target audience for this presentation? Please be specific about their background and expertise level."

        if not context_analysis.get('has_duration') and 'long' not in ' '.join(asked_questions):
            return "How long should the presentation be? (e.g., number of slides, duration in minutes)"

        if not context_analysis.get('has_tone') and 'tone' not in ' '.join(asked_questions):
            return "What tone or style would you prefer? (e.g., formal, conversational, inspirational, technical)"

        # Ask about specific requirements if basics are covered
        if context_analysis.get('understanding_level', 0) > 0.5:
            if 'success' not in ' '.join(asked_questions):
                return "What would make this presentation successful in your view? What are the key outcomes you're hoping for?"

            if 'constraint' not in ' '.join(asked_questions):
                return "Are there any specific constraints, requirements, or must-have elements I should incorporate?"

        # Default to asking for more details
        return "Could you provide more details about your presentation goals? What specific aspects are most important to you?"

    @tool("summarize_goals", description="Create a comprehensive summary of refined goals")
    def summarize_goals(self, history: List[Dict[str, Any]], initial_input: Dict[str, Any]) -> str:
        """
        Summarize the refined goals from the conversation.

        Returns:
            Comprehensive summary of presentation requirements
        """
        # Extract key information from conversation
        requirements = {
            "topic": initial_input.get('text', 'Not specified'),
            "audience": None,
            "duration": None,
            "tone": None,
            "key_points": [],
            "constraints": [],
            "success_criteria": []
        }

        # Parse conversation for details
        for msg in history:
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()

                # Extract audience
                if any(word in content for word in ['audience', 'for', 'presenting to']):
                    requirements['audience'] = msg.get('content', '')

                # Extract duration
                if any(word in content for word in ['minute', 'slide', 'hour', 'long']):
                    requirements['duration'] = msg.get('content', '')

                # Extract tone
                if any(word in content for word in ['tone', 'style', 'formal', 'casual']):
                    requirements['tone'] = msg.get('content', '')

                # Extract key points
                if any(word in content for word in ['include', 'cover', 'focus', 'important']):
                    requirements['key_points'].append(msg.get('content', ''))

        # Build summary
        summary_parts = [
            f"**Presentation Topic**: {requirements['topic']}",
        ]

        if requirements['audience']:
            summary_parts.append(f"**Target Audience**: {requirements['audience']}")

        if requirements['duration']:
            summary_parts.append(f"**Duration/Length**: {requirements['duration']}")

        if requirements['tone']:
            summary_parts.append(f"**Tone/Style**: {requirements['tone']}")

        if requirements['key_points']:
            summary_parts.append(f"**Key Points to Cover**:\n" + "\n".join(f"- {p}" for p in requirements['key_points']))

        if requirements['constraints']:
            summary_parts.append(f"**Constraints**: " + ", ".join(requirements['constraints']))

        summary_parts.append("\n**Next Steps**: I'll create a detailed outline based on these requirements.")

        return "\n\n".join(summary_parts)

    def run(self, data: ClarifierInput) -> AgentResult:
        """
        Execute the clarification process with ADK enhancements.

        Args:
            data: Input containing conversation history and initial request

        Returns:
            AgentResult with response and completion status
        """
        # Enable tracing for Dev UI
        if hasattr(data, 'trace_enabled') and data.trace_enabled:
            self.enable_tracing()

        # Validate input
        data = self.validate_input(data, ClarifierInput)

        # Analyze current context
        context_analysis = self.analyze_context(data.history, data.initialInput)
        understanding_level = context_analysis['understanding_level']

        # Use provided context meter if available
        if data.contextMeter:
            understanding_level = max(understanding_level, data.contextMeter)

        # Decide whether to ask another question or summarize
        if understanding_level >= 0.85 or len(data.history) >= 8:
            # We have enough information - summarize
            refined_goals = self.summarize_goals(data.history, data.initialInput)

            output = ClarifierOutput(
                response=refined_goals,
                finished=True,
                contextMeter=1.0,
                refinedGoals=refined_goals
            )

            # Log completion
            logger.info(f"Clarification complete with understanding level: {understanding_level}")

        else:
            # Need more information - ask a question
            next_question = self.generate_question(context_analysis, data.history)

            # Use LLM to make the question more natural and contextual
            prompt_parts = [
                self.get_system_prompt(),
                f"\nCurrent understanding level: {understanding_level:.0%}",
                f"\nConversation so far:\n{self.format_conversation_history(data.history)}",
                f"\nBase question to ask: {next_question}",
                "\nRephrase this question to be natural, friendly, and contextual. Keep it concise and focused."
            ]

            refined_question, usage = self.llm(prompt_parts, temperature=0.7)

            output = ClarifierOutput(
                response=refined_question.strip(),
                finished=False,
                contextMeter=understanding_level
            )

        # Create result with telemetry
        return self.create_result(
            data=output.model_dump(),
            usage=usage if 'usage' in locals() else AgentUsage(model=self.model),
            trace_id=f"clarifier-{time.time()}",
            metadata={
                "understanding_level": understanding_level,
                "message_count": len(data.history),
                "trace": self.get_trace() if self.trace_enabled else []
            }
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for the ClarifierAgent."""
        return (
            "You are a Clarifier agent specializing in refining presentation requirements. "
            "Your goal is to gather comprehensive information about the user's presentation needs "
            "through targeted, friendly questions. You focus on understanding the audience, goals, "
            "constraints, and success criteria. You ask one question at a time and keep questions "
            "concise and easy to answer."
        )


# Make the agent available with both naming conventions
Agent = ClarifierAgent
Input = ClarifierInput
Output = ClarifierOutput

# This allows backward compatibility
import time
from adk.base_agent import AgentUsage
import logging

logger = logging.getLogger(__name__)