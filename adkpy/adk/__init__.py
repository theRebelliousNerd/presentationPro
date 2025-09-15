"""
ADK Compatibility Module

This module provides a compatibility layer for the Google Agent Development Kit (ADK).
It implements the core ADK patterns and interfaces needed by the presentation agents.
"""

from .agents import Agent, LlmAgent, BaseAgent
from .tools import Tool, ToolResult
from .dev_ui import get_dev_ui_server
from .types import Content, Message, Part, FunctionCall, FunctionResponse

__all__ = [
    'Agent',
    'LlmAgent',
    'BaseAgent',
    'Tool',
    'ToolResult',
    'get_dev_ui_server',
    'Content',
    'Message',
    'Part',
    'FunctionCall',
    'FunctionResponse'
]