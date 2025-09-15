# --- METADATA ---
name = "ClarifierAgent"
description = "Drives a short, targeted Q&A to refine a user’s presentation goals, constraints, and success criteria."
author = "Google ADK Example"
license = "Apache 2.0"
version = "1.0.0"
homepage = "https://github.com/google/agent-development-kit"
# --- END METADATA ---

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .base import BaseAgent, AgentResult


class Input(BaseModel):
    """
    Defines the input parameters for the ClarifierAgent.
    """
    history: List[Dict[str, Any]] = Field(
        description="The history of the conversation so far, used to understand context."
    )
    initialInput: Dict[str, Any] = Field(
        description="The user's initial request, containing text, audience, tone, etc."
    )
    newFiles: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="An optional list of new files or assets provided during the clarification phase."
    )


class Output(BaseModel):
    """
    Defines the structured output of the ClarifierAgent.
    """
    response: str = Field(
        description="The agent's response, which is either the next clarifying question or the final summary of goals."
    )
    finished: bool = Field(
        default=False,
        description="A boolean flag that is true only when the agent has gathered sufficient information and is providing its final summary."
    )


class Agent(BaseAgent):
    """
    An agent that engages in a dialogue to refine a user's goals before
    passing a structured summary to downstream agents.
    """

    def run(self, data: Input) -> AgentResult:
        """
        Executes the agent's logic to ask clarifying questions or summarize goals.

        Args:
            data: An instance of the Input model containing conversation history and user inputs.

        Returns:
            An AgentResult containing the agent's response (question or summary) and a finished status.
        """
        initial_prompt = (data.initialInput or {}).get("text", "").strip()
        asset_names = ", ".join([(f.get("name") or "") for f in (data.newFiles or []) if f])

        system_prompt = (
            "You are a Clarifier agent. Your goal is to refine a user's vague request into a clear set of goals for a presentation. "
            "First, review the conversation history and initial request. "
            "If the goals are still unclear, ask one single, concise, targeted question to gather missing information (e.g., about audience, length, tone, required topics, or success metrics). "
            "If you have enough information to proceed, provide a comprehensive summary of the refined goals and set 'finished' to true. "
            "You must respond in a valid JSON format with keys 'response' (string) and 'finished' (boolean)."
        )
        
        # We can simplify the history for the prompt to just a transcript.
        history_transcript = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in data.history])

        # Convert messages to Gemini format (list of strings or content parts)
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
            output_data = Output(**obj)
        except (json.JSONDecodeError, TypeError):
            # Fallback if the model fails to produce valid JSON
            output_data = Output(
                response="I'm having trouble understanding. Could you please rephrase your goal?",
                finished=False
            )

        return AgentResult(data=output_data.model_dump(), usage=usage)