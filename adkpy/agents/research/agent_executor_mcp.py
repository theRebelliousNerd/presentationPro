"""
Research Agent Executor with MCP Tool Integration

This executor enhances the research agent with MCP tool access for web search,
RAG retrieval, and other data gathering capabilities.
"""

import json
import logging
from typing import TYPE_CHECKING, Optional, Dict, Any, List
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCard,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.genai import types

# Import MCP client from shared
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.mcp_client import get_mcp_client, MCPToolResult

if TYPE_CHECKING:
    from google.adk.sessions.session import Session

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Constants
DEFAULT_USER_ID = 'self'


class ResearchAgentExecutorMCP(AgentExecutor):
    """Research Agent Executor with MCP tool integration"""

    def __init__(self, runner: Runner, card: AgentCard):
        self.runner = runner
        self._card = card
        self._active_sessions: set[str] = set()
        self.mcp_client = get_mcp_client()

    async def _enhance_with_tools(self, query: str, presentation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance research with MCP tools.

        Args:
            query: Research query
            presentation_id: Optional presentation context

        Returns:
            Enhanced research data
        """
        enhanced_data = {
            "web_results": [],
            "rag_results": [],
            "additional_context": []
        }

        try:
            # Web search for current information
            logger.debug(f"Searching web for: {query}")
            web_result = await self.mcp_client.search_web(query, num_results=5)
            if web_result.success and web_result.data:
                enhanced_data["web_results"] = web_result.data
                logger.info(f"Found {len(web_result.data)} web results")

            # RAG retrieval if presentation context available
            if presentation_id:
                logger.debug(f"Retrieving RAG data for presentation: {presentation_id}")
                rag_result = await self.mcp_client.retrieve_rag(
                    query=query,
                    presentation_id=presentation_id,
                    limit=5
                )
                if rag_result.success and rag_result.data:
                    enhanced_data["rag_results"] = rag_result.data
                    logger.info(f"Found {len(rag_result.data)} RAG results")

            # Record telemetry
            await self.mcp_client.record_telemetry(
                "research_tool_usage",
                {
                    "query": query,
                    "web_results_count": len(enhanced_data["web_results"]),
                    "rag_results_count": len(enhanced_data["rag_results"])
                }
            )

        except Exception as e:
            logger.error(f"Error enhancing research with tools: {e}")

        return enhanced_data

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
    ) -> None:
        """Process research request with tool enhancement"""

        session_obj = await self._upsert_session(session_id)
        session_id = session_obj.id
        self._active_sessions.add(session_id)

        try:
            # Extract query from message
            message_text = ""
            for part in new_message.parts:
                if hasattr(part, 'text') and part.text:
                    message_text = part.text
                    break

            # Try to parse as JSON for structured input
            query = message_text
            presentation_id = None
            try:
                input_data = json.loads(message_text)
                query = input_data.get("query", message_text)
                presentation_id = input_data.get("presentation_id")
            except (json.JSONDecodeError, TypeError):
                # Use raw text as query
                pass

            # Enhance with MCP tools before sending to LLM
            tool_data = await self._enhance_with_tools(query, presentation_id)

            # Prepare enhanced message for LLM
            enhanced_message = types.UserContent(
                parts=[
                    types.Part(text=json.dumps({
                        "query": query,
                        "tool_results": tool_data,
                        "instruction": "Use the provided tool results to generate comprehensive research findings."
                    }))
                ]
            )

            # Process with ADK runner
            async for event in self.runner.run_async(
                session_id=session_id,
                user_id=DEFAULT_USER_ID,
                new_message=enhanced_message,
            ):
                if event.is_final_response():
                    parts = [
                        convert_genai_part_to_a2a(part)
                        for part in event.content.parts
                        if (part.text or part.file_data or part.inline_data)
                    ]
                    logger.debug('Yielding final response: %s', parts)
                    await task_updater.add_artifact(parts)
                    await task_updater.update_status(
                        TaskState.completed, final=True
                    )
                    break
                if not event.get_function_calls():
                    logger.debug('Yielding update response')
                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            [
                                convert_genai_part_to_a2a(part)
                                for part in event.content.parts
                                if part.text
                            ],
                        ),
                    )
                else:
                    logger.debug('Skipping event')
        finally:
            self._active_sessions.discard(session_id)

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        """Execute research task with tool enhancement"""
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.update_status(TaskState.submitted)
        await updater.update_status(TaskState.working)
        await self._process_request(
            types.UserContent(
                parts=[
                    convert_a2a_part_to_genai(part)
                    for part in context.message.parts
                ],
            ),
            context.context_id,
            updater,
        )
        logger.debug('[ResearchAgentExecutorMCP] execute exiting')

    async def cleanup(self):
        """Cleanup resources"""
        # MCP client is a singleton, don't close it here
        pass

    @property
    def card(self) -> AgentCard:
        return self._card

    @property
    def active_sessions(self) -> set[str]:
        return self._active_sessions

    async def _upsert_session(self, session_id: str) -> "Session":
        """Get or create session"""
        session_obj = await self.runner.session_store().get_session(session_id=session_id)
        if session_obj is None:
            session_obj = await self.runner.session_store().create_session(session_id=session_id)
        return session_obj


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """Convert GenAI part to A2A part"""
    if part.text:
        return TextPart(text=part.text)
    # Add other conversions as needed
    return TextPart(text="")


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """Convert A2A part to GenAI part"""
    if isinstance(part, TextPart):
        return types.Part(text=part.text)
    # Add other conversions as needed
    return types.Part(text=str(part))