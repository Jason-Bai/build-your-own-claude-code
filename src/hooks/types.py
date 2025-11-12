"""
Hook Event Types and Context Definitions

This module defines all hook events and context structures for the global hooks system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
import time


class HookEvent(Enum):
    """Hook event types enumeration"""

    # User Interaction
    ON_USER_INPUT = "user.input"
    ON_COMMAND_PARSE = "command.parse"

    # Agent Lifecycle
    ON_AGENT_START = "agent.start"
    ON_AGENT_END = "agent.end"
    ON_AGENT_ERROR = "agent.error"

    # Thinking Process
    ON_THINKING = "agent.thinking"
    ON_DECISION = "agent.decision"

    # Tool Execution
    ON_TOOL_SELECT = "tool.select"
    ON_TOOL_EXECUTE = "tool.execute"
    ON_TOOL_RESULT = "tool.result"
    ON_TOOL_ERROR = "tool.error"
    ON_PERMISSION_CHECK = "permission.check"

    # Output
    ON_OUTPUT_FORMAT = "output.format"
    ON_OUTPUT_RENDER = "output.render"
    ON_OUTPUT_SEND = "output.send"

    # System
    ON_ERROR = "system.error"
    ON_RECOVERY = "system.recovery"
    ON_SHUTDOWN = "system.shutdown"
    ON_METRICS = "system.metrics"


@dataclass
class HookContext:
    """Hook execution context information

    This class encapsulates all context needed by hook handlers to perform their operations.
    """

    # Core event information
    event: HookEvent
    timestamp: float

    # Event-specific data
    data: Dict[str, Any]

    # Context tracing
    request_id: str
    agent_id: str
    user_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "event": self.event.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HookContext":
        """Create context from dictionary"""
        return cls(
            event=HookEvent(data["event"]),
            timestamp=data["timestamp"],
            data=data["data"],
            request_id=data["request_id"],
            agent_id=data["agent_id"],
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
        )


# Type alias for hook handler functions
from typing import Callable, Awaitable

HookHandler = Callable[[HookContext], Awaitable[None]]
