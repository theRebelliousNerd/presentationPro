"""
ADK Type Definitions

Core type definitions for ADK message passing and content handling.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class Role(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


@dataclass
class FunctionCall:
    """Represents a function/tool call."""
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "arguments": self.arguments,
            "id": self.id
        }


@dataclass
class FunctionResponse:
    """Represents a function/tool response."""
    name: str
    response: Any
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "response": self.response,
            "id": self.id
        }


@dataclass
class Part:
    """
    Represents a part of a message content.

    Can contain text, function calls, or function responses.
    """
    text: Optional[str] = None
    function_call: Optional[FunctionCall] = None
    function_response: Optional[FunctionResponse] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.text is not None:
            result["text"] = self.text
        if self.function_call is not None:
            result["function_call"] = self.function_call.to_dict()
        if self.function_response is not None:
            result["function_response"] = self.function_response.to_dict()
        return result

    def is_text(self) -> bool:
        """Check if this is a text part."""
        return self.text is not None

    def is_function_call(self) -> bool:
        """Check if this is a function call part."""
        return self.function_call is not None

    def is_function_response(self) -> bool:
        """Check if this is a function response part."""
        return self.function_response is not None


@dataclass
class Content:
    """
    Represents message content with multiple parts.

    This follows the ADK pattern of structured content.
    """
    parts: List[Part] = field(default_factory=list)
    role: Optional[Role] = None

    def add_text(self, text: str) -> None:
        """Add a text part."""
        self.parts.append(Part(text=text))

    def add_function_call(self, name: str, arguments: Dict[str, Any], id: Optional[str] = None) -> None:
        """Add a function call part."""
        self.parts.append(Part(function_call=FunctionCall(name, arguments, id)))

    def add_function_response(self, name: str, response: Any, id: Optional[str] = None) -> None:
        """Add a function response part."""
        self.parts.append(Part(function_response=FunctionResponse(name, response, id)))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parts": [part.to_dict() for part in self.parts],
            "role": self.role.value if self.role else None
        }

    def to_text(self) -> str:
        """Extract text content."""
        texts = [part.text for part in self.parts if part.is_text()]
        return " ".join(texts)


@dataclass
class Message:
    """
    Represents a message in a conversation.

    This is the core message type for agent communication.
    """
    role: Role
    content: Union[str, Content]
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure content is properly formatted."""
        if isinstance(self.content, str):
            # Convert string to Content with text part
            content_obj = Content(role=self.role)
            content_obj.add_text(self.content)
            self.content = content_obj

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "role": self.role.value,
            "content": self.content.to_dict() if isinstance(self.content, Content) else self.content
        }
        if self.name:
            result["name"] = self.name
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def get_text(self) -> str:
        """Extract text content from message."""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, Content):
            return self.content.to_text()
        return ""


@dataclass
class Session:
    """
    Represents an agent session with conversation history.
    """
    id: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: Message) -> None:
        """Add a message to the session."""
        self.messages.append(message)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get message history as dictionaries."""
        return [msg.to_dict() for msg in self.messages]

    def clear(self) -> None:
        """Clear the session."""
        self.messages.clear()
        self.context.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "messages": self.get_history(),
            "metadata": self.metadata,
            "context": self.context
        }