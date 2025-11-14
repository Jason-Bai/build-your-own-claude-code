"""
Unit tests for Hook Manager

Tests hook registration, priority ordering, trigger execution,
error handling, and hook lifecycle management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.hooks.manager import HookManager
from src.hooks.types import HookEvent, HookContext


@pytest.mark.unit
class TestHookManagerInitialization:
    """Tests for HookManager initialization"""

    def test_initialization_creates_handler_dict(self):
        """Test HookManager initializes with empty handlers"""
        manager = HookManager()

        assert isinstance(manager._handlers, dict)
        assert len(manager._handlers) > 0

    def test_initialization_with_error_logging_enabled(self):
        """Test HookManager initialization with error logging"""
        manager = HookManager(enable_error_logging=True)

        assert manager._enable_error_logging is True

    def test_initialization_with_error_logging_disabled(self):
        """Test HookManager initialization without error logging"""
        manager = HookManager(enable_error_logging=False)

        assert manager._enable_error_logging is False

    def test_initialization_creates_all_hook_events(self):
        """Test that HookManager initializes all HookEvent types"""
        manager = HookManager()

        for event in HookEvent:
            assert event in manager._handlers
            assert isinstance(manager._handlers[event], list)

    def test_initialization_creates_empty_error_handlers(self):
        """Test that error handlers list is initialized"""
        manager = HookManager()

        assert isinstance(manager._error_handlers, list)
        assert len(manager._error_handlers) == 0


@pytest.mark.unit
class TestHookRegistration:
    """Tests for hook handler registration"""

    @pytest.mark.asyncio
    async def test_register_single_handler(self):
        """Test registering a single handler"""
        manager = HookManager()
        handler = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 1

    @pytest.mark.asyncio
    async def test_register_multiple_handlers(self):
        """Test registering multiple handlers for same event"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_USER_INPUT, handler2)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 2

    @pytest.mark.asyncio
    async def test_register_returns_unregister_callable(self):
        """Test register returns unregister function"""
        manager = HookManager()
        handler = AsyncMock()

        unregister = manager.register(HookEvent.ON_USER_INPUT, handler)

        assert callable(unregister)

    @pytest.mark.asyncio
    async def test_register_with_default_priority(self):
        """Test registration with default priority (0)"""
        manager = HookManager()
        handler = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler)

        # Should have 1 handler
        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 1

    @pytest.mark.asyncio
    async def test_register_with_custom_priority(self):
        """Test registration with custom priority"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1, priority=5)
        manager.register(HookEvent.ON_USER_INPUT, handler2, priority=10)

        # Handler2 should be first due to higher priority
        handlers = manager._handlers[HookEvent.ON_USER_INPUT]
        assert handlers[0][0] == handler2
        assert handlers[1][0] == handler1

    @pytest.mark.asyncio
    async def test_register_different_events(self):
        """Test registering handlers for different events"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_AGENT_START, handler2)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 1
        assert manager.get_handlers_count(HookEvent.ON_AGENT_START) == 1


@pytest.mark.unit
class TestPriorityOrdering:
    """Tests for handler priority ordering"""

    def test_handlers_ordered_by_priority_descending(self):
        """Test handlers are ordered by priority (highest first)"""
        manager = HookManager()
        handler1 = AsyncMock(name="handler1")
        handler2 = AsyncMock(name="handler2")
        handler3 = AsyncMock(name="handler3")

        manager.register(HookEvent.ON_USER_INPUT, handler1, priority=1)
        manager.register(HookEvent.ON_USER_INPUT, handler2, priority=10)
        manager.register(HookEvent.ON_USER_INPUT, handler3, priority=5)

        handlers = [h[0] for h in manager._handlers[HookEvent.ON_USER_INPUT]]
        assert handlers == [handler2, handler3, handler1]

    def test_same_priority_preserves_insertion_order(self):
        """Test handlers with same priority preserve insertion order"""
        manager = HookManager()
        handler1 = AsyncMock(name="handler1")
        handler2 = AsyncMock(name="handler2")

        manager.register(HookEvent.ON_USER_INPUT, handler1, priority=5)
        manager.register(HookEvent.ON_USER_INPUT, handler2, priority=5)

        handlers = [h[0] for h in manager._handlers[HookEvent.ON_USER_INPUT]]
        assert handlers == [handler1, handler2]

    def test_negative_priority_ordering(self):
        """Test negative priorities work correctly"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1, priority=-5)
        manager.register(HookEvent.ON_USER_INPUT, handler2, priority=5)

        handlers = [h[0] for h in manager._handlers[HookEvent.ON_USER_INPUT]]
        assert handlers[0] == handler2  # positive priority first
        assert handlers[1] == handler1


@pytest.mark.unit
class TestHookUnregistration:
    """Tests for unregistering hooks"""

    def test_unregister_by_callable(self):
        """Test unregistering handler by returning function"""
        manager = HookManager()
        handler = AsyncMock()

        unregister = manager.register(HookEvent.ON_USER_INPUT, handler)
        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 1

        unregister()
        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 0

    def test_unregister_method(self):
        """Test unregister method"""
        manager = HookManager()
        handler = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler)
        result = manager.unregister(HookEvent.ON_USER_INPUT, handler)

        assert result is True
        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 0

    def test_unregister_nonexistent_handler(self):
        """Test unregistering nonexistent handler returns False"""
        manager = HookManager()
        handler = AsyncMock()

        result = manager.unregister(HookEvent.ON_USER_INPUT, handler)

        assert result is False

    def test_unregister_from_event_with_multiple_handlers(self):
        """Test unregistering one handler leaves others"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_USER_INPUT, handler2)

        manager.unregister(HookEvent.ON_USER_INPUT, handler1)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 1
        assert manager._handlers[HookEvent.ON_USER_INPUT][0][0] == handler2


@pytest.mark.unit
class TestHookTrigger:
    """Tests for triggering hooks"""

    @pytest.mark.asyncio
    async def test_trigger_calls_registered_handler(self):
        """Test trigger calls registered handlers"""
        manager = HookManager()
        handler = AsyncMock()
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, handler)
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        handler.assert_called_once_with(context)

    @pytest.mark.asyncio
    async def test_trigger_calls_multiple_handlers(self):
        """Test trigger calls all registered handlers"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_USER_INPUT, handler2)
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        handler1.assert_called_once()
        handler2.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_in_priority_order(self):
        """Test handlers are called in priority order"""
        manager = HookManager()
        call_order = []

        async def handler1(ctx):
            call_order.append(1)

        async def handler2(ctx):
            call_order.append(2)

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, handler1, priority=1)
        manager.register(HookEvent.ON_USER_INPUT, handler2, priority=10)
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        assert call_order == [2, 1]

    @pytest.mark.asyncio
    async def test_trigger_nonexistent_event(self):
        """Test triggering event with no handlers"""
        manager = HookManager()
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        # Should not raise error
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

    @pytest.mark.asyncio
    async def test_trigger_continues_on_handler_error(self):
        """Test trigger continues despite handler errors"""
        manager = HookManager()

        async def failing_handler(ctx):
            raise ValueError("Test error")

        handler2 = AsyncMock()
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, failing_handler)
        manager.register(HookEvent.ON_USER_INPUT, handler2)
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        # Second handler should still be called
        handler2.assert_called_once()


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handler registration and execution"""

    def test_register_error_handler(self):
        """Test registering error handler"""
        manager = HookManager()
        error_handler = Mock()

        manager.register_error_handler(error_handler)

        assert len(manager._error_handlers) == 1

    def test_register_multiple_error_handlers(self):
        """Test registering multiple error handlers"""
        manager = HookManager()
        handler1 = Mock()
        handler2 = Mock()

        manager.register_error_handler(handler1)
        manager.register_error_handler(handler2)

        assert len(manager._error_handlers) == 2

    @pytest.mark.asyncio
    async def test_error_handler_called_on_hook_error(self):
        """Test error handler is called when hook fails"""
        manager = HookManager()
        error_handler = AsyncMock()

        async def failing_handler(ctx):
            raise ValueError("Test error")

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, failing_handler)
        manager.register_error_handler(error_handler)
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        error_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_error_handler(self):
        """Test synchronous error handler works"""
        manager = HookManager()
        error_handler = Mock()

        async def failing_handler(ctx):
            raise ValueError("Test error")

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, failing_handler)
        manager.register_error_handler(error_handler)
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        error_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handler_receives_error_info(self):
        """Test error handler receives error details"""
        manager = HookManager()
        error_handler = AsyncMock()

        async def failing_handler(ctx):
            raise ValueError("Test error message")

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, failing_handler)
        manager.register_error_handler(error_handler)
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        # Error handler should be called with event, error, and context
        call_args = error_handler.call_args[0]
        assert call_args[0] == HookEvent.ON_USER_INPUT
        assert isinstance(call_args[1], ValueError)
        assert call_args[2] == context


@pytest.mark.unit
class TestClearOperations:
    """Tests for clearing handlers"""

    def test_clear_specific_event_handlers(self):
        """Test clearing handlers for specific event"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_AGENT_START, handler2)

        manager.clear_handlers(HookEvent.ON_USER_INPUT)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 0
        assert manager.get_handlers_count(HookEvent.ON_AGENT_START) == 1

    def test_clear_all_handlers(self):
        """Test clearing all handlers"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_AGENT_START, handler2)

        manager.clear_handlers()

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 0
        assert manager.get_handlers_count(HookEvent.ON_AGENT_START) == 0

    def test_clear_error_handlers(self):
        """Test clearing error handlers"""
        manager = HookManager()
        handler = Mock()

        manager.register_error_handler(handler)
        assert len(manager._error_handlers) == 1

        manager.clear_error_handlers()
        assert len(manager._error_handlers) == 0


@pytest.mark.unit
class TestStatistics:
    """Tests for hook statistics"""

    def test_get_handlers_count_empty(self):
        """Test handler count for empty event"""
        manager = HookManager()

        count = manager.get_handlers_count(HookEvent.ON_USER_INPUT)
        assert count == 0

    def test_get_handlers_count_with_handlers(self):
        """Test handler count with registered handlers"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_USER_INPUT, handler2)

        count = manager.get_handlers_count(HookEvent.ON_USER_INPUT)
        assert count == 2

    def test_get_stats(self):
        """Test get_stats returns handler counts"""
        manager = HookManager()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_AGENT_START, handler2)

        stats = manager.get_stats()

        assert HookEvent.ON_USER_INPUT.value in stats
        assert HookEvent.ON_AGENT_START.value in stats
        assert stats[HookEvent.ON_USER_INPUT.value] == 1
        assert stats[HookEvent.ON_AGENT_START.value] == 1

    def test_get_stats_empty(self):
        """Test get_stats with no handlers"""
        manager = HookManager()

        stats = manager.get_stats()

        assert isinstance(stats, dict)
        assert len(stats) == 0


@pytest.mark.unit
class TestIntegration:
    """Integration tests for HookManager"""

    @pytest.mark.asyncio
    async def test_complete_hook_lifecycle(self):
        """Test complete hook registration and execution flow"""
        manager = HookManager()
        call_log = []

        async def handler1(ctx):
            call_log.append("handler1")

        async def handler2(ctx):
            call_log.append("handler2")

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={"input": "test"},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, handler1, priority=1)
        manager.register(HookEvent.ON_USER_INPUT, handler2, priority=10)
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        # Handler2 called first due to priority
        assert call_log == ["handler2", "handler1"]

    @pytest.mark.asyncio
    async def test_unregister_and_retrigger(self):
        """Test unregistering and retriggering"""
        manager = HookManager()
        handler = AsyncMock()

        unregister = manager.register(HookEvent.ON_USER_INPUT, handler)
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        await manager.trigger(HookEvent.ON_USER_INPUT, context)
        assert handler.call_count == 1

        unregister()
        await manager.trigger(HookEvent.ON_USER_INPUT, context)
        assert handler.call_count == 1  # Not called again


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    @pytest.mark.asyncio
    async def test_cancelled_error_propagates(self):
        """Test CancelledError propagates"""
        manager = HookManager()

        async def handler(ctx):
            raise asyncio.CancelledError()

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, handler)

        with pytest.raises(asyncio.CancelledError):
            await manager.trigger(HookEvent.ON_USER_INPUT, context)

    def test_register_with_zero_priority(self):
        """Test registration with zero priority"""
        manager = HookManager()
        handler = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler, priority=0)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 1

    @pytest.mark.asyncio
    async def test_handler_with_exception_in_error_handler(self):
        """Test error handler exception doesn't break trigger"""
        manager = HookManager()

        async def failing_handler(ctx):
            raise ValueError("Test error")

        async def failing_error_handler(event, error, ctx):
            raise RuntimeError("Error handler failed")

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req1",
            agent_id="agent1"
        )

        manager.register(HookEvent.ON_USER_INPUT, failing_handler)
        manager.register_error_handler(failing_error_handler)

        # Should not raise
        await manager.trigger(HookEvent.ON_USER_INPUT, context)
