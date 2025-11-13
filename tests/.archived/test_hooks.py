"""
Unit tests for the hooks system

Tests for HookManager, HookContext, and HookContextBuilder
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, call

from src.hooks import (
    HookEvent,
    HookContext,
    HookManager,
    HookContextBuilder,
)


class TestHookContext:
    """Tests for HookContext dataclass"""

    def test_hook_context_creation(self):
        """Test creating a HookContext"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890.0,
            data={"input": "test"},
            request_id="req-123",
            agent_id="agent-456",
            user_id="user-789",
            metadata={"key": "value"},
        )

        assert context.event == HookEvent.ON_USER_INPUT
        assert context.timestamp == 1234567890.0
        assert context.data == {"input": "test"}
        assert context.request_id == "req-123"
        assert context.agent_id == "agent-456"
        assert context.user_id == "user-789"
        assert context.metadata == {"key": "value"}

    def test_hook_context_to_dict(self):
        """Test converting HookContext to dict"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890.0,
            data={"input": "test"},
            request_id="req-123",
            agent_id="agent-456",
            user_id="user-789",
            metadata={"key": "value"},
        )

        context_dict = context.to_dict()
        assert context_dict["event"] == "user.input"
        assert context_dict["timestamp"] == 1234567890.0
        assert context_dict["data"] == {"input": "test"}
        assert context_dict["request_id"] == "req-123"
        assert context_dict["agent_id"] == "agent-456"
        assert context_dict["user_id"] == "user-789"
        assert context_dict["metadata"] == {"key": "value"}

    def test_hook_context_from_dict(self):
        """Test creating HookContext from dict"""
        context_dict = {
            "event": "user.input",
            "timestamp": 1234567890.0,
            "data": {"input": "test"},
            "request_id": "req-123",
            "agent_id": "agent-456",
            "user_id": "user-789",
            "metadata": {"key": "value"},
        }

        context = HookContext.from_dict(context_dict)
        assert context.event == HookEvent.ON_USER_INPUT
        assert context.timestamp == 1234567890.0
        assert context.data == {"input": "test"}
        assert context.request_id == "req-123"
        assert context.agent_id == "agent-456"
        assert context.user_id == "user-789"
        assert context.metadata == {"key": "value"}


class TestHookContextBuilder:
    """Tests for HookContextBuilder"""

    def test_builder_initialization(self):
        """Test initializing HookContextBuilder"""
        builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")
        assert builder.request_id == "req-123"
        assert builder.agent_id == "agent-456"

    def test_builder_auto_generates_ids(self):
        """Test that builder auto-generates IDs if not provided"""
        builder = HookContextBuilder()
        assert builder.request_id
        assert builder.agent_id
        assert len(builder.request_id) > 0
        assert len(builder.agent_id) > 0

    def test_builder_build(self):
        """Test building a HookContext"""
        builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")
        context = builder.build(
            HookEvent.ON_USER_INPUT,
            user_id="user-789",
            input="test input"
        )

        assert context.event == HookEvent.ON_USER_INPUT
        assert context.request_id == "req-123"
        assert context.agent_id == "agent-456"
        assert context.user_id == "user-789"
        assert context.data == {"input": "test input"}

    def test_builder_build_with_parent(self):
        """Test building a context with parent inheritance"""
        parent_context = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=1234567890.0,
            data={},
            request_id="req-123",
            agent_id="agent-456",
            user_id="user-789",
            metadata={"parent": True},
        )

        builder = HookContextBuilder()
        child_context = builder.build_with_parent(
            HookEvent.ON_TOOL_EXECUTE,
            parent_context,
            tool_name="test_tool"
        )

        assert child_context.event == HookEvent.ON_TOOL_EXECUTE
        assert child_context.request_id == parent_context.request_id
        assert child_context.agent_id == parent_context.agent_id
        assert child_context.user_id == parent_context.user_id
        assert "parent_event" in child_context.metadata
        assert child_context.metadata["parent_event"] == "agent.start"

    def test_builder_reset(self):
        """Test resetting the builder"""
        builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")
        original_request_id = builder.request_id

        builder.reset(new_request_id=False)
        assert builder.request_id == original_request_id

        builder.reset(new_request_id=True)
        assert builder.request_id != original_request_id

    def test_builder_create_child_builder(self):
        """Test creating a child builder"""
        parent_builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")
        child_builder = parent_builder.create_child_builder()

        assert child_builder.request_id == parent_builder.request_id
        assert child_builder.agent_id != parent_builder.agent_id


class TestHookManager:
    """Tests for HookManager"""

    def test_hook_manager_initialization(self):
        """Test initializing HookManager"""
        manager = HookManager()
        assert manager is not None
        assert manager._handlers is not None

    @pytest.mark.asyncio
    async def test_register_and_trigger_handler(self):
        """Test registering and triggering a hook handler"""
        manager = HookManager()
        handler = AsyncMock()

        unregister = manager.register(HookEvent.ON_USER_INPUT, handler, priority=0)

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890.0,
            data={"input": "test"},
            request_id="req-123",
            agent_id="agent-456",
        )

        await manager.trigger(HookEvent.ON_USER_INPUT, context)
        handler.assert_called_once_with(context)

    @pytest.mark.asyncio
    async def test_handler_priority_execution_order(self):
        """Test that handlers execute in priority order"""
        manager = HookManager()
        call_order = []

        async def handler1(context):
            call_order.append(1)

        async def handler2(context):
            call_order.append(2)

        async def handler3(context):
            call_order.append(3)

        # Register with different priorities
        manager.register(HookEvent.ON_USER_INPUT, handler1, priority=1)
        manager.register(HookEvent.ON_USER_INPUT, handler2, priority=3)
        manager.register(HookEvent.ON_USER_INPUT, handler3, priority=2)

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890.0,
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )

        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        # Handlers should execute in priority order (highest first)
        assert call_order == [2, 3, 1]

    @pytest.mark.asyncio
    async def test_unregister_handler(self):
        """Test unregistering a handler"""
        manager = HookManager()
        handler = AsyncMock()

        unregister = manager.register(HookEvent.ON_USER_INPUT, handler)
        unregister()

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890.0,
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )

        await manager.trigger(HookEvent.ON_USER_INPUT, context)
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_unregister_by_method(self):
        """Test unregistering handler using unregister method"""
        manager = HookManager()
        handler = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, handler)
        success = manager.unregister(HookEvent.ON_USER_INPUT, handler)

        assert success is True

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890.0,
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )

        await manager.trigger(HookEvent.ON_USER_INPUT, context)
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_handler_error_isolation(self):
        """Test that handler errors don't interrupt other handlers"""
        manager = HookManager()

        async def failing_handler(context):
            raise ValueError("Test error")

        successful_handler = AsyncMock()

        manager.register(HookEvent.ON_USER_INPUT, failing_handler, priority=10)
        manager.register(HookEvent.ON_USER_INPUT, successful_handler, priority=1)

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890.0,
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )

        # Should not raise, but handler error should be handled
        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        # Successful handler should still be called
        successful_handler.assert_called_once_with(context)

    @pytest.mark.asyncio
    async def test_error_handler_callback(self):
        """Test error handler callback is invoked"""
        manager = HookManager()
        error_handler = AsyncMock()

        async def failing_handler(context):
            raise ValueError("Test error")

        manager.register_error_handler(error_handler)
        manager.register(HookEvent.ON_USER_INPUT, failing_handler)

        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890.0,
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )

        await manager.trigger(HookEvent.ON_USER_INPUT, context)

        # Error handler should be called
        error_handler.assert_called_once()
        args = error_handler.call_args[0]
        assert args[0] == HookEvent.ON_USER_INPUT
        assert isinstance(args[1], ValueError)

    def test_get_handlers_count(self):
        """Test getting the count of handlers for an event"""
        manager = HookManager()
        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 0

        async def handler1(context):
            pass

        async def handler2(context):
            pass

        manager.register(HookEvent.ON_USER_INPUT, handler1)
        manager.register(HookEvent.ON_USER_INPUT, handler2)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 2

    def test_clear_handlers_for_event(self):
        """Test clearing handlers for a specific event"""
        manager = HookManager()

        async def handler(context):
            pass

        manager.register(HookEvent.ON_USER_INPUT, handler)
        manager.register(HookEvent.ON_AGENT_START, handler)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 1
        assert manager.get_handlers_count(HookEvent.ON_AGENT_START) == 1

        manager.clear_handlers(HookEvent.ON_USER_INPUT)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 0
        assert manager.get_handlers_count(HookEvent.ON_AGENT_START) == 1

    def test_clear_all_handlers(self):
        """Test clearing all handlers"""
        manager = HookManager()

        async def handler(context):
            pass

        manager.register(HookEvent.ON_USER_INPUT, handler)
        manager.register(HookEvent.ON_AGENT_START, handler)

        manager.clear_handlers()

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 0
        assert manager.get_handlers_count(HookEvent.ON_AGENT_START) == 0

    def test_get_stats(self):
        """Test getting handler statistics"""
        manager = HookManager()

        async def handler(context):
            pass

        manager.register(HookEvent.ON_USER_INPUT, handler)
        manager.register(HookEvent.ON_USER_INPUT, handler)
        manager.register(HookEvent.ON_AGENT_START, handler)

        stats = manager.get_stats()

        assert stats["user.input"] == 2
        assert stats["agent.start"] == 1
        assert len(stats) == 2


@pytest.mark.asyncio
async def test_multiple_events_independent(self):
    """Test that different events have independent handler lists"""
    manager = HookManager()

    user_input_handler = AsyncMock()
    agent_start_handler = AsyncMock()

    manager.register(HookEvent.ON_USER_INPUT, user_input_handler)
    manager.register(HookEvent.ON_AGENT_START, agent_start_handler)

    context = HookContext(
        event=HookEvent.ON_USER_INPUT,
        timestamp=1234567890.0,
        data={},
        request_id="req-123",
        agent_id="agent-456",
    )

    await manager.trigger(HookEvent.ON_USER_INPUT, context)

    user_input_handler.assert_called_once()
    agent_start_handler.assert_not_called()
