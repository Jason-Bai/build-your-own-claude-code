"""
Hook Manager

This module implements the global hook management system for event-driven architecture.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Optional, Tuple
from .types import HookEvent, HookContext, HookHandler

logger = logging.getLogger(__name__)


class HookManager:
    """Global hook manager for event-driven system

    Manages registration and triggering of hooks throughout the application lifecycle.
    Supports priority-based handler execution and error isolation.
    """

    def __init__(self, enable_error_logging: bool = True):
        """Initialize HookManager

        Args:
            enable_error_logging: Whether to log hook errors (default: True)
        """
        self._handlers: Dict[HookEvent, List[Tuple[HookHandler, int]]] = {}
        self._error_handlers: List[Callable] = []
        self._enable_error_logging = enable_error_logging

        # Initialize handler lists for all events
        for event in HookEvent:
            self._handlers[event] = []

    def register(
        self,
        event: HookEvent,
        handler: HookHandler,
        priority: int = 0,
    ) -> Callable[[], None]:
        """Register a hook handler for an event

        Handlers with higher priority are executed first.

        Args:
            event: The hook event to register for
            handler: The async handler function
            priority: Priority level (higher values execute first, default: 0)

        Returns:
            A callable that unregisters the handler when called
        """
        if event not in self._handlers:
            self._handlers[event] = []

        # Insert handler maintaining priority order (highest first)
        handlers_list = self._handlers[event]
        insert_idx = 0
        for idx, (_, existing_priority) in enumerate(handlers_list):
            if priority > existing_priority:
                insert_idx = idx
                break
            insert_idx = idx + 1

        handlers_list.insert(insert_idx, (handler, priority))

        # Return unregister function
        def unregister():
            try:
                handlers_list.remove((handler, priority))
            except ValueError:
                logger.warning(f"Handler not found for event {event.value}")

        return unregister

    def unregister(
        self,
        event: HookEvent,
        handler: HookHandler,
    ) -> bool:
        """Unregister a hook handler

        Args:
            event: The hook event to unregister from
            handler: The handler to remove

        Returns:
            True if handler was found and removed, False otherwise
        """
        if event not in self._handlers:
            return False

        handlers_list = self._handlers[event]
        for item in handlers_list:
            if item[0] == handler:
                handlers_list.remove(item)
                return True

        return False

    def register_error_handler(self, handler: Callable) -> None:
        """Register a global error handler for hook execution errors

        Args:
            handler: An async handler that receives (event, error, context)
        """
        self._error_handlers.append(handler)

    async def trigger(
        self,
        event: HookEvent,
        context: HookContext,
    ) -> None:
        """Trigger a hook event

        Executes all registered handlers for the event in priority order.
        Handler errors are isolated and don't interrupt the chain.

        Args:
            event: The hook event to trigger
            context: The execution context for the hook
        """
        if event not in self._handlers:
            return

        handlers = self._handlers[event]

        for handler, _ in handlers:
            try:
                await handler(context)
            except asyncio.CancelledError:
                # Allow cancellation to propagate
                raise
            except Exception as e:
                await self._handle_hook_error(event, e, context)

    async def _handle_hook_error(
        self,
        event: HookEvent,
        error: Exception,
        context: HookContext,
    ) -> None:
        """Handle errors from hook handlers

        Args:
            event: The event that was being triggered
            error: The error that occurred
            context: The execution context
        """
        if self._enable_error_logging:
            logger.error(
                f"Error in hook handler for event {event.value}: {error}",
                exc_info=error,
            )

        # Call registered error handlers
        for error_handler in self._error_handlers:
            try:
                if asyncio.iscoroutinefunction(error_handler):
                    await error_handler(event, error, context)
                else:
                    error_handler(event, error, context)
            except Exception as e:
                logger.error(f"Error in hook error handler: {e}", exc_info=e)

    def get_handlers_count(self, event: HookEvent) -> int:
        """Get the number of registered handlers for an event

        Args:
            event: The hook event

        Returns:
            The number of handlers registered
        """
        return len(self._handlers.get(event, []))

    def clear_handlers(self, event: Optional[HookEvent] = None) -> None:
        """Clear hook handlers

        Args:
            event: Specific event to clear, or None to clear all
        """
        if event is None:
            for event_type in HookEvent:
                self._handlers[event_type] = []
        else:
            if event in self._handlers:
                self._handlers[event] = []

    def clear_error_handlers(self) -> None:
        """Clear all error handlers"""
        self._error_handlers = []

    def get_stats(self) -> Dict[str, any]:
        """Get statistics about registered handlers

        Returns:
            Dictionary with handler counts per event
        """
        stats = {}
        for event in HookEvent:
            count = len(self._handlers.get(event, []))
            if count > 0:
                stats[event.value] = count

        return stats
