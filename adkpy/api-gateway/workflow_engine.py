"""
Workflow Engine for A2A Orchestration

Manages the execution of agent pipelines with support for sequential,
parallel, and conditional workflows. Implements retry logic, circuit breakers,
and error recovery strategies.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import json

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    """Workflow execution states."""
    IDLE = "idle"
    CLARIFYING = "clarifying"
    RESEARCHING = "researching"
    OUTLINING = "outlining"
    GENERATING = "generating"
    CRITIQUING = "critiquing"
    POLISHING = "polishing"
    DESIGNING = "designing"
    SCRIPTING = "scripting"
    COMPLETE = "complete"
    ERROR = "error"


class TaskPriority(int, Enum):
    """Task execution priority."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures exceeded threshold
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for agent calls to prevent cascading failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0

    def call_succeeded(self):
        """Record successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                # Recovered successfully
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker closed after recovery")
        else:
            self.failure_count = 0

    def call_failed(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def can_call(self) -> bool:
        """Check if calls are allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if time_since_failure >= self.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False

        # Half-open state
        return self.half_open_calls < self.half_open_max_calls


class RetryPolicy:
    """Retry policy with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        return delay


class WorkflowEngine:
    """
    Orchestrates multi-agent workflows with error handling and recovery.
    """

    def __init__(self, registry, session_manager):
        """
        Initialize workflow engine.

        Args:
            registry: Agent registry for accessing agents
            session_manager: Session manager for state persistence
        """
        self.registry = registry
        self.session_manager = session_manager
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_policy = RetryPolicy()
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def initialize(self):
        """Initialize workflow engine."""
        # Create circuit breakers for each agent
        for agent_name in self.registry.list_agents():
            self.circuit_breakers[agent_name] = CircuitBreaker()

        logger.info("Workflow engine initialized")

    async def clarify(
        self,
        session_id: str,
        history: List[Dict[str, Any]],
        initial_input: Dict[str, Any],
        new_files: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Execute clarification workflow.

        Args:
            session_id: Session identifier
            history: Conversation history
            initial_input: Initial user input
            new_files: Newly uploaded files

        Returns:
            Clarification result
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.update_state(WorkflowState.CLARIFYING)

        try:
            # Execute clarifier agent
            result = await self._execute_agent(
                agent_name="clarifier",
                skill_id="clarify_goals",
                input_data={
                    "history": history,
                    "initialInput": initial_input,
                    "newFiles": new_files
                },
                session_id=session_id
            )

            # Store result in session
            session.add_result("clarification", result)

            # Update state based on result
            if result.get("finished", False):
                session.update_state(WorkflowState.IDLE)

            return result

        except Exception as e:
            session.update_state(WorkflowState.ERROR)
            session.add_error(f"Clarification failed: {str(e)}")
            raise

    async def generate_outline(
        self,
        session_id: str,
        refined_goals: str,
        assets: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate presentation outline with optional research.

        Args:
            session_id: Session identifier
            refined_goals: Refined presentation goals
            assets: User-provided assets

        Returns:
            Generated outline
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.update_state(WorkflowState.OUTLINING)

        try:
            # Parallel execution: Research + Outline generation
            tasks = []

            # Research task (if research agent available)
            if self.registry.is_healthy("research"):
                research_task = asyncio.create_task(
                    self._execute_agent(
                        agent_name="research",
                        skill_id="research_backgrounds",
                        input_data={
                            "topic": refined_goals,
                            "context": {"assets": assets}
                        },
                        session_id=session_id,
                        allow_failure=True  # Research is optional
                    )
                )
                tasks.append(("research", research_task))

            # Outline generation task
            outline_task = asyncio.create_task(
                self._execute_agent(
                    agent_name="outline",
                    skill_id="generate_outline",
                    input_data={
                        "refinedGoals": refined_goals,
                        "assets": assets
                    },
                    session_id=session_id
                )
            )
            tasks.append(("outline", outline_task))

            # Wait for all tasks
            results = {}
            for name, task in tasks:
                try:
                    result = await task
                    results[name] = result
                    session.add_result(name, result)
                except Exception as e:
                    logger.warning(f"Task {name} failed: {e}")
                    if name == "outline":
                        raise  # Outline is critical

            # Combine results
            outline = results.get("outline", {})
            research = results.get("research", {})

            # Enhance outline with research if available
            if research and "rules" in research:
                outline["research_context"] = research["rules"]

            session.update_state(WorkflowState.IDLE)
            return outline

        except Exception as e:
            session.update_state(WorkflowState.ERROR)
            session.add_error(f"Outline generation failed: {str(e)}")
            raise

    async def generate_slide(
        self,
        session_id: str,
        slide_number: int,
        outline: Dict[str, Any],
        refined_goals: str
    ) -> Dict[str, Any]:
        """
        Generate a complete slide through the agent pipeline.

        Args:
            session_id: Session identifier
            slide_number: Slide number to generate
            outline: Presentation outline
            refined_goals: Refined presentation goals

        Returns:
            Complete slide with all enhancements
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.update_state(WorkflowState.GENERATING)

        try:
            # Sequential pipeline with optional steps

            # Step 1: Generate initial content (required)
            slide_content = await self._execute_agent(
                agent_name="slide_writer",
                skill_id="write_slide",
                input_data={
                    "slideNumber": slide_number,
                    "outline": outline,
                    "refinedGoals": refined_goals
                },
                session_id=session_id
            )

            # Step 2: Critique and improve (optional)
            if self.registry.is_healthy("critic"):
                session.update_state(WorkflowState.CRITIQUING)
                try:
                    critique_result = await self._execute_agent(
                        agent_name="critic",
                        skill_id="critique_slide",
                        input_data={
                            "slide": slide_content,
                            "refinedGoals": refined_goals
                        },
                        session_id=session_id,
                        allow_failure=True
                    )
                    if critique_result and "improvedSlide" in critique_result:
                        slide_content = critique_result["improvedSlide"]
                except Exception as e:
                    logger.warning(f"Critique failed for slide {slide_number}: {e}")

            # Step 3: Polish speaker notes (optional)
            if self.registry.is_healthy("notes_polisher") and "speakerNotes" in slide_content:
                session.update_state(WorkflowState.POLISHING)
                try:
                    polish_result = await self._execute_agent(
                        agent_name="notes_polisher",
                        skill_id="polish_notes",
                        input_data={
                            "notes": slide_content.get("speakerNotes", ""),
                            "slideTitle": slide_content.get("title", "")
                        },
                        session_id=session_id,
                        allow_failure=True
                    )
                    if polish_result and "polishedNotes" in polish_result:
                        slide_content["speakerNotes"] = polish_result["polishedNotes"]
                except Exception as e:
                    logger.warning(f"Notes polishing failed for slide {slide_number}: {e}")

            # Step 4: Generate design (optional)
            if self.registry.is_healthy("design"):
                session.update_state(WorkflowState.DESIGNING)
                try:
                    design_result = await self._execute_agent(
                        agent_name="design",
                        skill_id="design_slide",
                        input_data={
                            "slide": slide_content,
                            "slideNumber": slide_number
                        },
                        session_id=session_id,
                        allow_failure=True
                    )
                    if design_result:
                        slide_content["design"] = design_result
                except Exception as e:
                    logger.warning(f"Design generation failed for slide {slide_number}: {e}")

            # Add slide number
            slide_content["slideNumber"] = slide_number

            # Store in session
            session.add_slide(slide_number, slide_content)
            session.update_state(WorkflowState.IDLE)

            return {"slide": slide_content, "usage": self._aggregate_usage(session_id)}

        except Exception as e:
            session.update_state(WorkflowState.ERROR)
            session.add_error(f"Slide generation failed: {str(e)}")
            raise

    async def research(
        self,
        session_id: str,
        topic: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute research workflow.

        Args:
            session_id: Session identifier
            topic: Research topic
            context: Additional context

        Returns:
            Research results
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.update_state(WorkflowState.RESEARCHING)

        try:
            result = await self._execute_agent(
                agent_name="research",
                skill_id="research_backgrounds",
                input_data={
                    "topic": topic,
                    "context": context
                },
                session_id=session_id
            )

            session.add_result("research", result)
            session.update_state(WorkflowState.IDLE)

            return result

        except Exception as e:
            session.update_state(WorkflowState.ERROR)
            session.add_error(f"Research failed: {str(e)}")
            raise

    async def generate_script(
        self,
        session_id: str,
        presentation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate presentation script.

        Args:
            session_id: Session identifier
            presentation_data: Complete presentation data

        Returns:
            Generated script
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.update_state(WorkflowState.SCRIPTING)

        try:
            result = await self._execute_agent(
                agent_name="script_writer",
                skill_id="generate_script",
                input_data={
                    "presentation": presentation_data
                },
                session_id=session_id
            )

            session.add_result("script", result)
            session.update_state(WorkflowState.COMPLETE)

            return result

        except Exception as e:
            session.update_state(WorkflowState.ERROR)
            session.add_error(f"Script generation failed: {str(e)}")
            raise

    async def _execute_agent(
        self,
        agent_name: str,
        skill_id: str,
        input_data: Dict[str, Any],
        session_id: str,
        allow_failure: bool = False
    ) -> Dict[str, Any]:
        """
        Execute an agent task with retry and circuit breaker logic.

        Args:
            agent_name: Name of the agent
            skill_id: Skill to execute
            input_data: Input data for the task
            session_id: Session identifier
            allow_failure: Whether to allow failures

        Returns:
            Task result

        Raises:
            Exception: If execution fails and allow_failure is False
        """
        # Check circuit breaker
        breaker = self.circuit_breakers.get(agent_name)
        if breaker and not breaker.can_call():
            if allow_failure:
                logger.warning(f"Circuit breaker open for {agent_name}, skipping")
                return {}
            raise Exception(f"Circuit breaker open for {agent_name}")

        # Get agent card
        agent_card = self.registry.get_agent(agent_name)
        if not agent_card:
            if allow_failure:
                logger.warning(f"Agent {agent_name} not found, skipping")
                return {}
            raise ValueError(f"Agent {agent_name} not found")

        # Prepare A2A message
        agent_url = str(agent_card.url)
        endpoint = f"{agent_url}/a2a/{agent_card.name}"

        # Execute with retry
        last_error = None
        for attempt in range(self.retry_policy.max_attempts):
            try:
                # Send A2A request
                response = await self.http_client.post(
                    endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "id": f"{session_id}-{agent_name}-{datetime.utcnow().timestamp()}",
                        "method": "tasks/send",
                        "params": {
                            "skillId": skill_id,
                            "input": input_data
                        }
                    }
                )
                response.raise_for_status()

                result = response.json()

                # Check for JSON-RPC error
                if "error" in result:
                    raise Exception(f"Agent error: {result['error']}")

                # Extract result
                task_result = result.get("result", {})

                # Wait for task completion (polling)
                task_id = task_result.get("taskId")
                if task_id:
                    task_result = await self._wait_for_task(
                        agent_url,
                        agent_card.name,
                        task_id
                    )

                # Success
                if breaker:
                    breaker.call_succeeded()

                return task_result.get("result", task_result)

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Agent {agent_name} failed (attempt {attempt + 1}): {e}"
                )

                if breaker:
                    breaker.call_failed()

                if attempt < self.retry_policy.max_attempts - 1:
                    delay = self.retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    if allow_failure:
                        logger.warning(f"Agent {agent_name} failed after retries")
                        return {}
                    raise last_error

    async def _wait_for_task(
        self,
        agent_url: str,
        agent_name: str,
        task_id: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Wait for an agent task to complete.

        Args:
            agent_url: Agent base URL
            agent_name: Agent name
            task_id: Task identifier
            timeout: Maximum wait time in seconds

        Returns:
            Task result
        """
        endpoint = f"{agent_url}/a2a/{agent_name}"
        start_time = datetime.utcnow()

        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            # Check task status
            response = await self.http_client.post(
                endpoint,
                json={
                    "jsonrpc": "2.0",
                    "id": f"status-{task_id}",
                    "method": "tasks/status",
                    "params": {"taskId": task_id}
                }
            )
            response.raise_for_status()

            result = response.json()
            if "error" in result:
                raise Exception(f"Status check error: {result['error']}")

            task_status = result.get("result", {})
            status = task_status.get("status")

            if status == "completed":
                return task_status
            elif status == "failed":
                error = task_status.get("error", "Unknown error")
                raise Exception(f"Task failed: {error}")
            elif status == "cancelled":
                raise Exception("Task was cancelled")

            # Wait before next check
            await asyncio.sleep(1)

        raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")

    def _aggregate_usage(self, session_id: str) -> Dict[str, Any]:
        """
        Aggregate usage statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Aggregated usage data
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return {}

        # Aggregate token usage from all results
        total_tokens = 0
        model_usage = {}

        for result in session.results.values():
            if isinstance(result, dict) and "usage" in result:
                usage = result["usage"]
                if "totalTokens" in usage:
                    total_tokens += usage["totalTokens"]
                if "model" in usage:
                    model = usage["model"]
                    if model not in model_usage:
                        model_usage[model] = 0
                    model_usage[model] += usage.get("totalTokens", 0)

        return {
            "totalTokens": total_tokens,
            "modelUsage": model_usage
        }

    async def close(self):
        """Clean up resources."""
        await self.http_client.aclose()
        logger.info("Workflow engine closed")