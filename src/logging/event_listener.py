"""
EventBus integration for action logging

This module provides an event listener that automatically logs
system-level events from the EventBus to the action logging system.
"""

from ..events import Event, EventType
from .action_logger import ActionLogger
from .types import ActionType


class LoggingEventListener:
    """
    EventBus listener that logs system events to action logger

    This listener subscribes to EventBus events and converts them
    to structured action logs. It handles:
    - System errors (AGENT_ERROR, TOOL_ERROR)
    - Agent state changes
    - Tool execution events (already logged by agent, but provides backup)
    """

    def __init__(self, action_logger: ActionLogger):
        """
        Initialize logging event listener

        Args:
            action_logger: ActionLogger instance to write logs to
        """
        self.action_logger = action_logger

    async def handle_event(self, event: Event):
        """
        Handle incoming event from EventBus

        Args:
            event: Event to process
        """
        event_type = event.event_type
        data = event.data

        # Map EventBus events to ActionTypes
        if event_type == EventType.AGENT_ERROR:
            # Log system error when agent encounters fatal error
            self.action_logger.log(
                action_type=ActionType.SYSTEM_ERROR,
                status="error",
                error=data.get("error", "Unknown error"),
                error_type=data.get("error_type", "UnknownError"),
                context="agent_error"
            )

        elif event_type == EventType.TOOL_ERROR:
            # Backup logging for tool errors (primary logging in agent)
            # Only log if it looks like a system-level error
            error_msg = data.get("error", "")
            if "system" in error_msg.lower() or "fatal" in error_msg.lower():
                self.action_logger.log(
                    action_type=ActionType.SYSTEM_ERROR,
                    status="error",
                    error=error_msg,
                    tool_name=data.get("tool_name", "unknown"),
                    context="tool_system_error"
                )

        # Note: AGENT_STATE_CHANGED is already logged directly in enhanced_agent.py
        # to avoid duplicate logs. Other events (TOOL_STARTED, LLM_CALLING, etc.)
        # are also logged directly by the agent, so we don't duplicate them here


def setup_logging_event_listener(event_bus, action_logger: ActionLogger) -> LoggingEventListener:
    """
    Setup logging event listener and subscribe to EventBus

    Args:
        event_bus: EventBus instance
        action_logger: ActionLogger instance

    Returns:
        LoggingEventListener instance
    """
    listener = LoggingEventListener(action_logger)

    # Subscribe to all events (listener will filter what to log)
    event_bus.subscribe_all(listener.handle_event)

    return listener
