"""
Hook Context Builder

Helper class for simplified construction of HookContext instances.
"""

import time
import uuid
from typing import Any, Dict, Optional
from .types import HookEvent, HookContext


class HookContextBuilder:
    """Simplified helper for building HookContext instances

    This class provides a convenient way to create HookContext objects with
    consistent request_id and agent_id tracking across multiple hook events.
    """

    def __init__(self, request_id: Optional[str] = None, agent_id: Optional[str] = None):
        """Initialize the context builder

        Args:
            request_id: Request ID for tracking (auto-generated if not provided)
            agent_id: Agent ID for tracking (auto-generated if not provided)
        """
        self.request_id = request_id or self._generate_id()
        self.agent_id = agent_id or self._generate_id()
        self.base_timestamp = time.time()

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique ID

        Returns:
            A unique ID string
        """
        return str(uuid.uuid4())[:8]

    def build(
        self,
        event: HookEvent,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **data,
    ) -> HookContext:
        """Build a HookContext instance

        Args:
            event: The hook event type
            user_id: Optional user ID for this context
            metadata: Optional metadata dictionary
            **data: Event-specific data as keyword arguments

        Returns:
            A configured HookContext instance
        """
        return HookContext(
            event=event,
            timestamp=time.time(),
            data=data,
            request_id=self.request_id,
            agent_id=self.agent_id,
            user_id=user_id,
            metadata=metadata or {},
        )

    def build_with_parent(
        self,
        event: HookEvent,
        parent_context: HookContext,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **data,
    ) -> HookContext:
        """Build a HookContext that inherits from a parent context

        Useful for creating child contexts within a single request chain.

        Args:
            event: The hook event type
            parent_context: The parent HookContext to inherit from
            user_id: Optional user ID (inherits from parent if not provided)
            metadata: Optional metadata (merged with parent metadata)
            **data: Event-specific data as keyword arguments

        Returns:
            A configured HookContext instance inheriting from parent
        """
        merged_metadata = {
            **parent_context.metadata,
            **(metadata or {}),
            "parent_event": parent_context.event.value,
        }

        return HookContext(
            event=event,
            timestamp=time.time(),
            data=data,
            request_id=parent_context.request_id,
            agent_id=parent_context.agent_id,
            user_id=user_id or parent_context.user_id,
            metadata=merged_metadata,
        )

    def reset(self, new_request_id: bool = False) -> None:
        """Reset the builder for a new context chain

        Args:
            new_request_id: If True, generate a new request_id; otherwise just update agent_id
        """
        if new_request_id:
            self.request_id = self._generate_id()
        self.agent_id = self._generate_id()
        self.base_timestamp = time.time()

    def create_child_builder(self) -> "HookContextBuilder":
        """Create a child builder that shares the same request_id

        Useful for creating contexts in nested operations that should be
        tracked under the same request.

        Returns:
            A new HookContextBuilder with same request_id but different agent_id
        """
        return HookContextBuilder(
            request_id=self.request_id,
            agent_id=self._generate_id(),
        )
