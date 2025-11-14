"""
Unit tests for Hook Manager and Builder

Tests hook registration, triggering, priority ordering, error handling,
and context builder functionality.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.hooks.manager import HookManager
from src.hooks.builder import HookContextBuilder
from src.hooks.types import HookEvent, HookContext


@pytest.mark.unit
class TestHookManagerInitialization:
    """Tests for HookManager initialization"""

    def test_hook_manager_default_initialization(self):
        """Test creating HookManager with default settings"""
        manager = HookManager()

        assert manager._enable_error_logging is True
        assert len(manager._handlers) > 0
        assert len(manager._error_handlers) == 0

    def test_hook_manager_with_error_logging_disabled(self):
        """Test creating HookManager with error logging disabled"""
        manager = HookManager(enable_error_logging=False)

        assert manager._enable_error_logging is False

    def test_hook_manager_initializes_all_events(self):
        """Test that all HookEvent types have handler lists"""
        manager = HookManager()

        for event in HookEvent:
            assert event in manager._handlers
            assert isinstance(manager._handlers[event], list)
            assert len(manager._handlers[event]) == 0


@pytest.mark.unit
class TestHookManagerRegistration:
    """Tests for hook registration and unregistration"""

    @pytest.mark.asyncio
    async def test_register_simple_handler(self):
        """Test registering a basic hook handler"""
        manager = HookManager()
        handler_called = False

        async def test_handler(context: HookContext):
            nonlocal handler_called
            handler_called = True

        unregister = manager.register(HookEvent.ON_AGENT_START, test_handler)

        assert callable(unregister)
        assert manager.get_handlers_count(HookEvent.ON_AGENT_START) == 1

        # Trigger and verify
        context = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_AGENT_START, context)
        assert handler_called is True

    @pytest.mark.asyncio
    async def test_register_multiple_handlers(self):
        """Test registering multiple handlers for same event"""
        manager = HookManager()
        calls = []

        async def handler1(context: HookContext):
            calls.append("handler1")

        async def handler2(context: HookContext):
            calls.append("handler2")

        async def handler3(context: HookContext):
            calls.append("handler3")

        manager.register(HookEvent.ON_TOOL_EXECUTE, handler1)
        manager.register(HookEvent.ON_TOOL_EXECUTE, handler2)
        manager.register(HookEvent.ON_TOOL_EXECUTE, handler3)

        assert manager.get_handlers_count(HookEvent.ON_TOOL_EXECUTE) == 3

        context = HookContext(
            event=HookEvent.ON_TOOL_EXECUTE,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_TOOL_EXECUTE, context)

        assert len(calls) == 3
        assert "handler1" in calls
        assert "handler2" in calls
        assert "handler3" in calls

    @pytest.mark.asyncio
    async def test_register_with_priority(self):
        """Test handlers execute in priority order (highest first)"""
        manager = HookManager()
        execution_order = []

        async def low_priority(context: HookContext):
            execution_order.append("low")

        async def medium_priority(context: HookContext):
            execution_order.append("medium")

        async def high_priority(context: HookContext):
            execution_order.append("high")

        # Register in random order
        manager.register(HookEvent.ON_AGENT_START, medium_priority, priority=5)
        manager.register(HookEvent.ON_AGENT_START, high_priority, priority=10)
        manager.register(HookEvent.ON_AGENT_START, low_priority, priority=0)

        context = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_AGENT_START, context)

        assert execution_order == ["high", "medium", "low"]

    def test_unregister_via_return_function(self):
        """Test unregistering handler using returned function"""
        manager = HookManager()

        async def test_handler(context: HookContext):
            pass

        unregister = manager.register(HookEvent.ON_TOOL_RESULT, test_handler)
        assert manager.get_handlers_count(HookEvent.ON_TOOL_RESULT) == 1

        unregister()
        assert manager.get_handlers_count(HookEvent.ON_TOOL_RESULT) == 0

    def test_unregister_via_method(self):
        """Test unregistering handler using unregister method"""
        manager = HookManager()

        async def test_handler(context: HookContext):
            pass

        manager.register(HookEvent.ON_OUTPUT_SEND, test_handler)
        assert manager.get_handlers_count(HookEvent.ON_OUTPUT_SEND) == 1

        result = manager.unregister(HookEvent.ON_OUTPUT_SEND, test_handler)
        assert result is True
        assert manager.get_handlers_count(HookEvent.ON_OUTPUT_SEND) == 0

    def test_unregister_nonexistent_handler(self):
        """Test unregistering handler that doesn't exist"""
        manager = HookManager()

        async def test_handler(context: HookContext):
            pass

        result = manager.unregister(HookEvent.ON_ERROR, test_handler)
        assert result is False

    def test_unregister_twice_via_function(self):
        """Test calling unregister function twice handles gracefully"""
        manager = HookManager()

        async def test_handler(context: HookContext):
            pass

        unregister = manager.register(HookEvent.ON_SHUTDOWN, test_handler)
        unregister()  # First call should work
        unregister()  # Second call should not raise


@pytest.mark.unit
class TestHookManagerTrigger:
    """Tests for hook triggering"""

    @pytest.mark.asyncio
    async def test_trigger_single_handler(self):
        """Test triggering a single handler"""
        manager = HookManager()
        received_context = None

        async def test_handler(context: HookContext):
            nonlocal received_context
            received_context = context

        manager.register(HookEvent.ON_THINKING, test_handler)

        context = HookContext(
            event=HookEvent.ON_THINKING,
            timestamp=time.time(),
            data={"thought": "analyzing code"},
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_THINKING, context)

        assert received_context is not None
        assert received_context.event == HookEvent.ON_THINKING
        assert received_context.data["thought"] == "analyzing code"

    @pytest.mark.asyncio
    async def test_trigger_no_handlers(self):
        """Test triggering event with no handlers doesn't error"""
        manager = HookManager()

        context = HookContext(
            event=HookEvent.ON_METRICS,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )

        # Should not raise
        await manager.trigger(HookEvent.ON_METRICS, context)

    @pytest.mark.asyncio
    async def test_trigger_handler_with_error(self):
        """Test handler error doesn't interrupt other handlers"""
        manager = HookManager(enable_error_logging=False)
        calls = []

        async def failing_handler(context: HookContext):
            calls.append("failing")
            raise ValueError("Test error")

        async def successful_handler(context: HookContext):
            calls.append("successful")

        manager.register(HookEvent.ON_TOOL_ERROR, failing_handler, priority=10)
        manager.register(HookEvent.ON_TOOL_ERROR, successful_handler, priority=0)

        context = HookContext(
            event=HookEvent.ON_TOOL_ERROR,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_TOOL_ERROR, context)

        # Both should be called despite error in first
        assert "failing" in calls
        assert "successful" in calls

    @pytest.mark.asyncio
    async def test_trigger_cancellation_propagates(self):
        """Test that CancelledError propagates correctly"""
        manager = HookManager()

        async def cancelling_handler(context: HookContext):
            raise asyncio.CancelledError()

        manager.register(HookEvent.ON_AGENT_END, cancelling_handler)

        context = HookContext(
            event=HookEvent.ON_AGENT_END,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )

        with pytest.raises(asyncio.CancelledError):
            await manager.trigger(HookEvent.ON_AGENT_END, context)

    @pytest.mark.asyncio
    async def test_trigger_passes_correct_context(self):
        """Test context is passed correctly to handlers"""
        manager = HookManager()
        received_data = None

        async def test_handler(context: HookContext):
            nonlocal received_data
            received_data = context.data

        manager.register(HookEvent.ON_DECISION, test_handler)

        test_data = {"decision": "use_tool", "tool_name": "bash"}
        context = HookContext(
            event=HookEvent.ON_DECISION,
            timestamp=time.time(),
            data=test_data,
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_DECISION, context)

        assert received_data == test_data


@pytest.mark.unit
class TestHookManagerErrorHandling:
    """Tests for error handling in HookManager"""

    @pytest.mark.asyncio
    async def test_register_error_handler(self):
        """Test registering global error handler"""
        manager = HookManager(enable_error_logging=False)
        error_captured = None

        async def error_handler(event, error, context):
            nonlocal error_captured
            error_captured = (event, error, context)

        manager.register_error_handler(error_handler)

        async def failing_handler(context: HookContext):
            raise ValueError("Test error")

        manager.register(HookEvent.ON_RECOVERY, failing_handler)

        context = HookContext(
            event=HookEvent.ON_RECOVERY,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_RECOVERY, context)

        assert error_captured is not None
        assert error_captured[0] == HookEvent.ON_RECOVERY
        assert isinstance(error_captured[1], ValueError)
        assert error_captured[2] == context

    @pytest.mark.asyncio
    async def test_multiple_error_handlers(self):
        """Test multiple error handlers are all called"""
        manager = HookManager(enable_error_logging=False)
        calls = []

        async def error_handler1(event, error, context):
            calls.append("handler1")

        async def error_handler2(event, error, context):
            calls.append("handler2")

        manager.register_error_handler(error_handler1)
        manager.register_error_handler(error_handler2)

        async def failing_handler(context: HookContext):
            raise RuntimeError("Test error")

        manager.register(HookEvent.ON_AGENT_ERROR, failing_handler)

        context = HookContext(
            event=HookEvent.ON_AGENT_ERROR,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_AGENT_ERROR, context)

        assert "handler1" in calls
        assert "handler2" in calls

    @pytest.mark.asyncio
    async def test_error_handler_error_is_isolated(self):
        """Test error in error handler doesn't break system"""
        manager = HookManager(enable_error_logging=False)

        async def broken_error_handler(event, error, context):
            raise RuntimeError("Error handler error")

        manager.register_error_handler(broken_error_handler)

        async def failing_handler(context: HookContext):
            raise ValueError("Original error")

        manager.register(HookEvent.ON_PERMISSION_CHECK, failing_handler)

        context = HookContext(
            event=HookEvent.ON_PERMISSION_CHECK,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )

        # Should not raise despite both handlers erroring
        await manager.trigger(HookEvent.ON_PERMISSION_CHECK, context)

    @pytest.mark.asyncio
    async def test_sync_error_handler(self):
        """Test synchronous error handlers are supported"""
        manager = HookManager(enable_error_logging=False)
        error_captured = None

        def sync_error_handler(event, error, context):
            nonlocal error_captured
            error_captured = error

        manager.register_error_handler(sync_error_handler)

        async def failing_handler(context: HookContext):
            raise ValueError("Test sync error")

        manager.register(HookEvent.ON_OUTPUT_FORMAT, failing_handler)

        context = HookContext(
            event=HookEvent.ON_OUTPUT_FORMAT,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456",
        )
        await manager.trigger(HookEvent.ON_OUTPUT_FORMAT, context)

        assert error_captured is not None
        assert isinstance(error_captured, ValueError)


@pytest.mark.unit
class TestHookManagerUtilities:
    """Tests for HookManager utility methods"""

    def test_get_handlers_count(self):
        """Test getting handler count for event"""
        manager = HookManager()

        async def handler1(context: HookContext):
            pass

        async def handler2(context: HookContext):
            pass

        assert manager.get_handlers_count(HookEvent.ON_TOOL_SELECT) == 0

        manager.register(HookEvent.ON_TOOL_SELECT, handler1)
        assert manager.get_handlers_count(HookEvent.ON_TOOL_SELECT) == 1

        manager.register(HookEvent.ON_TOOL_SELECT, handler2)
        assert manager.get_handlers_count(HookEvent.ON_TOOL_SELECT) == 2

    def test_clear_handlers_specific_event(self):
        """Test clearing handlers for specific event"""
        manager = HookManager()

        async def handler(context: HookContext):
            pass

        manager.register(HookEvent.ON_USER_INPUT, handler)
        manager.register(HookEvent.ON_COMMAND_PARSE, handler)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 1
        assert manager.get_handlers_count(HookEvent.ON_COMMAND_PARSE) == 1

        manager.clear_handlers(HookEvent.ON_USER_INPUT)

        assert manager.get_handlers_count(HookEvent.ON_USER_INPUT) == 0
        assert manager.get_handlers_count(HookEvent.ON_COMMAND_PARSE) == 1

    def test_clear_all_handlers(self):
        """Test clearing all handlers"""
        manager = HookManager()

        async def handler(context: HookContext):
            pass

        manager.register(HookEvent.ON_AGENT_START, handler)
        manager.register(HookEvent.ON_AGENT_END, handler)
        manager.register(HookEvent.ON_TOOL_EXECUTE, handler)

        manager.clear_handlers()

        for event in HookEvent:
            assert manager.get_handlers_count(event) == 0

    def test_clear_error_handlers(self):
        """Test clearing error handlers"""
        manager = HookManager()

        async def error_handler(event, error, context):
            pass

        manager.register_error_handler(error_handler)
        manager.register_error_handler(error_handler)

        assert len(manager._error_handlers) == 2

        manager.clear_error_handlers()

        assert len(manager._error_handlers) == 0

    def test_get_stats_empty(self):
        """Test getting stats with no handlers"""
        manager = HookManager()
        stats = manager.get_stats()

        assert isinstance(stats, dict)
        assert len(stats) == 0

    def test_get_stats_with_handlers(self):
        """Test getting stats with registered handlers"""
        manager = HookManager()

        async def handler(context: HookContext):
            pass

        manager.register(HookEvent.ON_AGENT_START, handler)
        manager.register(HookEvent.ON_AGENT_START, handler)
        manager.register(HookEvent.ON_TOOL_EXECUTE, handler)

        stats = manager.get_stats()

        assert "agent.start" in stats
        assert stats["agent.start"] == 2
        assert "tool.execute" in stats
        assert stats["tool.execute"] == 1


@pytest.mark.unit
class TestHookContextBuilder:
    """Tests for HookContextBuilder"""

    def test_builder_initialization_with_defaults(self):
        """Test creating builder with auto-generated IDs"""
        builder = HookContextBuilder()

        assert builder.request_id is not None
        assert len(builder.request_id) == 8
        assert builder.agent_id is not None
        assert len(builder.agent_id) == 8
        assert builder.base_timestamp > 0

    def test_builder_initialization_with_custom_ids(self):
        """Test creating builder with custom IDs"""
        builder = HookContextBuilder(
            request_id="custom-req-123",
            agent_id="custom-agent-456",
        )

        assert builder.request_id == "custom-req-123"
        assert builder.agent_id == "custom-agent-456"

    def test_build_basic_context(self):
        """Test building a basic context"""
        builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")

        context = builder.build(
            event=HookEvent.ON_TOOL_EXECUTE,
            tool_name="read",
            file_path="/test/file.py",
        )

        assert context.event == HookEvent.ON_TOOL_EXECUTE
        assert context.request_id == "req-123"
        assert context.agent_id == "agent-456"
        assert context.data["tool_name"] == "read"
        assert context.data["file_path"] == "/test/file.py"

    def test_build_with_user_id(self):
        """Test building context with user ID"""
        builder = HookContextBuilder()

        context = builder.build(
            event=HookEvent.ON_USER_INPUT,
            user_id="user-789",
            input_text="test command",
        )

        assert context.user_id == "user-789"
        assert context.data["input_text"] == "test command"

    def test_build_with_metadata(self):
        """Test building context with metadata"""
        builder = HookContextBuilder()

        metadata = {"priority": "high", "source": "cli"}
        context = builder.build(
            event=HookEvent.ON_AGENT_START,
            metadata=metadata,
            task="analyze code",
        )

        assert context.metadata["priority"] == "high"
        assert context.metadata["source"] == "cli"

    def test_build_with_parent(self):
        """Test building child context from parent"""
        builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")

        parent = builder.build(
            event=HookEvent.ON_AGENT_START,
            user_id="user-789",
            metadata={"session": "abc"},
        )

        child = builder.build_with_parent(
            event=HookEvent.ON_TOOL_EXECUTE,
            parent_context=parent,
            tool_name="bash",
        )

        # Child inherits from parent
        assert child.request_id == parent.request_id
        assert child.agent_id == parent.agent_id
        assert child.user_id == parent.user_id
        assert child.metadata["session"] == "abc"
        assert child.metadata["parent_event"] == "agent.start"

    def test_build_with_parent_override_metadata(self):
        """Test child context can override parent metadata"""
        builder = HookContextBuilder()

        parent = builder.build(
            event=HookEvent.ON_AGENT_START,
            metadata={"level": "info", "session": "abc"},
        )

        child = builder.build_with_parent(
            event=HookEvent.ON_TOOL_ERROR,
            parent_context=parent,
            metadata={"level": "error", "retry": True},
        )

        assert child.metadata["level"] == "error"  # Overridden
        assert child.metadata["session"] == "abc"  # Inherited
        assert child.metadata["retry"] is True  # Added

    def test_reset_builder(self):
        """Test resetting builder state"""
        builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")

        original_req_id = builder.request_id
        original_agent_id = builder.agent_id

        builder.reset(new_request_id=False)

        assert builder.request_id == original_req_id  # Unchanged
        assert builder.agent_id != original_agent_id  # Changed

    def test_reset_builder_with_new_request_id(self):
        """Test resetting builder with new request ID"""
        builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")

        original_req_id = builder.request_id
        original_agent_id = builder.agent_id

        builder.reset(new_request_id=True)

        assert builder.request_id != original_req_id  # Changed
        assert builder.agent_id != original_agent_id  # Changed

    def test_create_child_builder(self):
        """Test creating child builder with shared request ID"""
        parent_builder = HookContextBuilder(
            request_id="req-123", agent_id="agent-456"
        )

        child_builder = parent_builder.create_child_builder()

        assert child_builder.request_id == parent_builder.request_id  # Shared
        assert child_builder.agent_id != parent_builder.agent_id  # Different

    def test_generate_id_uniqueness(self):
        """Test generated IDs are unique"""
        builder1 = HookContextBuilder()
        builder2 = HookContextBuilder()

        assert builder1.request_id != builder2.request_id
        assert builder1.agent_id != builder2.agent_id


@pytest.mark.unit
class TestHookIntegration:
    """Integration tests for hooks system"""

    @pytest.mark.asyncio
    async def test_complete_hook_workflow(self):
        """Test complete workflow: register, build context, trigger"""
        manager = HookManager()
        builder = HookContextBuilder(request_id="req-123", agent_id="agent-456")

        events_received = []

        async def workflow_handler(context: HookContext):
            events_received.append(
                {"event": context.event.value, "data": context.data}
            )

        # Register handlers
        manager.register(HookEvent.ON_AGENT_START, workflow_handler)
        manager.register(HookEvent.ON_TOOL_EXECUTE, workflow_handler)
        manager.register(HookEvent.ON_AGENT_END, workflow_handler)

        # Build and trigger contexts
        start_ctx = builder.build(event=HookEvent.ON_AGENT_START, task="test")
        await manager.trigger(HookEvent.ON_AGENT_START, start_ctx)

        tool_ctx = builder.build_with_parent(
            event=HookEvent.ON_TOOL_EXECUTE,
            parent_context=start_ctx,
            tool_name="read",
        )
        await manager.trigger(HookEvent.ON_TOOL_EXECUTE, tool_ctx)

        end_ctx = builder.build(event=HookEvent.ON_AGENT_END, status="success")
        await manager.trigger(HookEvent.ON_AGENT_END, end_ctx)

        # Verify workflow
        assert len(events_received) == 3
        assert events_received[0]["event"] == "agent.start"
        assert events_received[1]["event"] == "tool.execute"
        assert events_received[2]["event"] == "agent.end"

    @pytest.mark.asyncio
    async def test_hook_chain_with_priorities(self):
        """Test hook chain executes in priority order"""
        manager = HookManager()
        builder = HookContextBuilder()

        execution_log = []

        async def preprocessing(context: HookContext):
            execution_log.append("preprocess")

        async def main_processing(context: HookContext):
            execution_log.append("main")

        async def postprocessing(context: HookContext):
            execution_log.append("postprocess")

        # Register with explicit priority
        manager.register(HookEvent.ON_OUTPUT_FORMAT, postprocessing, priority=-10)
        manager.register(HookEvent.ON_OUTPUT_FORMAT, preprocessing, priority=10)
        manager.register(HookEvent.ON_OUTPUT_FORMAT, main_processing, priority=0)

        context = builder.build(
            event=HookEvent.ON_OUTPUT_FORMAT, content="test output"
        )
        await manager.trigger(HookEvent.ON_OUTPUT_FORMAT, context)

        assert execution_log == ["preprocess", "main", "postprocess"]

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error recovery through hooks"""
        manager = HookManager(enable_error_logging=False)
        builder = HookContextBuilder()

        errors = []
        recoveries = []

        async def error_tracking_handler(event, error, context):
            errors.append({"event": event.value, "error": str(error)})

        async def recovery_handler(context: HookContext):
            recoveries.append(context.data)

        manager.register_error_handler(error_tracking_handler)
        manager.register(HookEvent.ON_RECOVERY, recovery_handler)

        # Trigger error
        async def failing_op(context: HookContext):
            raise ValueError("Operation failed")

        manager.register(HookEvent.ON_TOOL_EXECUTE, failing_op)

        error_ctx = builder.build(event=HookEvent.ON_TOOL_EXECUTE, tool="bash")
        await manager.trigger(HookEvent.ON_TOOL_EXECUTE, error_ctx)

        # Trigger recovery
        recovery_ctx = builder.build(
            event=HookEvent.ON_RECOVERY, error="Operation failed", retry=True
        )
        await manager.trigger(HookEvent.ON_RECOVERY, recovery_ctx)

        assert len(errors) == 1
        assert errors[0]["event"] == "tool.execute"
        assert len(recoveries) == 1
        assert recoveries[0]["retry"] is True
