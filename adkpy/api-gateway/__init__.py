"""
PresentationPro A2A Orchestrator

A complete multi-agent orchestration service using the A2A protocol
for coordinating presentation generation across distributed agents.
"""

from .main import OrchestratorService, app
from .workflow_engine import WorkflowEngine, WorkflowState, CircuitBreaker
from .agent_discovery import AgentDiscovery, AgentRegistry, AgentCard
from .session_manager import SessionManager, PresentationSession, SessionState

__version__ = "2.0.0"

__all__ = [
    "OrchestratorService",
    "app",
    "WorkflowEngine",
    "WorkflowState",
    "CircuitBreaker",
    "AgentDiscovery",
    "AgentRegistry",
    "AgentCard",
    "SessionManager",
    "PresentationSession",
    "SessionState",
]