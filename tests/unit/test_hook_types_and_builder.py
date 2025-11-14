"""
Unit tests for Hook Types and Context Builder

Tests HookEvent enum, HookContext dataclass, and HookContextBuilder helper.
"""

import pytest
import time
from src.hooks.types import HookEvent, HookContext, HookHandler
from src.hooks.builder import HookContextBuilder


@pytest.mark.unit
class TestHookEventEnum:
    """Tests for HookEvent enum"""

    def test_hook_event_user_input(self):
        """Test USER_INPUT event exists"""
        assert HookEvent.ON_USER_INPUT.value == "user.input"

    def test_hook_event_agent_start(self):
        """Test AGENT_START event exists"""
        assert HookEvent.ON_AGENT_START.value == "agent.start"

    def test_hook_event_agent_end(self):
        """Test AGENT_END event exists"""
        assert HookEvent.ON_AGENT_END.value == "agent.end"

    def test_hook_event_agent_error(self):
        """Test AGENT_ERROR event exists"""
        assert HookEvent.ON_AGENT_ERROR.value == "agent.error"

    def test_hook_event_tool_select(self):
        """Test TOOL_SELECT event exists"""
        assert HookEvent.ON_TOOL_SELECT.value == "tool.select"

    def test_hook_event_tool_execute(self):
        """Test TOOL_EXECUTE event exists"""
        assert HookEvent.ON_TOOL_EXECUTE.value == "tool.execute"

    def test_hook_event_tool_error(self):
        """Test TOOL_ERROR event exists"""
        assert HookEvent.ON_TOOL_ERROR.value == "tool.error"

    def test_hook_event_permission_check(self):
        """Test PERMISSION_CHECK event exists"""
        assert HookEvent.ON_PERMISSION_CHECK.value == "permission.check"

    def test_hook_event_thinking(self):
        """Test THINKING event exists"""
        assert HookEvent.ON_THINKING.value == "agent.thinking"

    def test_hook_event_decision(self):
        """Test DECISION event exists"""
        assert HookEvent.ON_DECISION.value == "agent.decision"

    def test_hook_event_iteration(self):
        """Test can iterate over all events"""
        events = list(HookEvent)
        assert len(events) > 0
        assert all(isinstance(e, HookEvent) for e in events)

    def test_hook_event_value_format(self):
        """Test event values follow naming convention"""
        for event in HookEvent:
            # Values should be lowercase with dots
            assert event.value.islower()
            assert "." in event.value


@pytest.mark.unit
class TestHookContextInitialization:
    """Tests for HookContext initialization"""

    def test_context_creation_required_fields(self):
        """Test HookContext creation with required fields"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890,
            data={"input": "test"},
            request_id="req_123",
            agent_id="agent_456"
        )

        assert context.event == HookEvent.ON_USER_INPUT
        assert context.timestamp == 1234567890
        assert context.data == {"input": "test"}
        assert context.request_id == "req_123"
        assert context.agent_id == "agent_456"

    def test_context_creation_with_optional_fields(self):
        """Test HookContext creation with optional fields"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890,
            data={},
            request_id="req_1",
            agent_id="agent_1",
            user_id="user_1",
            metadata={"key": "value"}
        )

        assert context.user_id == "user_1"
        assert context.metadata == {"key": "value"}

    def test_context_user_id_optional(self):
        """Test user_id is optional (defaults to None)"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req_1",
            agent_id="agent_1"
        )

        assert context.user_id is None

    def test_context_metadata_default_empty(self):
        """Test metadata defaults to empty dict"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req_1",
            agent_id="agent_1"
        )

        assert context.metadata == {}


@pytest.mark.unit
class TestHookContextSerialization:
    """Tests for HookContext serialization"""

    def test_context_to_dict(self):
        """Test converting context to dictionary"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=1234567890,
            data={"input": "test"},
            request_id="req_1",
            agent_id="agent_1"
        )

        context_dict = context.to_dict()

        assert isinstance(context_dict, dict)
        assert context_dict["event"] == "user.input"
        assert context_dict["timestamp"] == 1234567890
        assert context_dict["data"] == {"input": "test"}
        assert context_dict["request_id"] == "req_1"

    def test_context_to_dict_includes_all_fields(self):
        """Test to_dict includes all fields"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req_1",
            agent_id="agent_1",
            user_id="user_1",
            metadata={"key": "value"}
        )

        context_dict = context.to_dict()

        assert "event" in context_dict
        assert "timestamp" in context_dict
        assert "data" in context_dict
        assert "request_id" in context_dict
        assert "agent_id" in context_dict
        assert "user_id" in context_dict
        assert "metadata" in context_dict

    def test_context_from_dict(self):
        """Test creating context from dictionary"""
        data = {
            "event": "user.input",
            "timestamp": 1234567890,
            "data": {"input": "test"},
            "request_id": "req_1",
            "agent_id": "agent_1"
        }

        context = HookContext.from_dict(data)

        assert context.event == HookEvent.ON_USER_INPUT
        assert context.timestamp == 1234567890
        assert context.data == {"input": "test"}
        assert context.request_id == "req_1"

    def test_context_roundtrip(self):
        """Test serialization roundtrip"""
        original = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=9876543210,
            data={"agent": "test_agent"},
            request_id="req_abc",
            agent_id="agent_xyz",
            user_id="user_123",
            metadata={"source": "cli"}
        )

        serialized = original.to_dict()
        restored = HookContext.from_dict(serialized)

        assert restored.event == original.event
        assert restored.timestamp == original.timestamp
        assert restored.data == original.data
        assert restored.request_id == original.request_id
        assert restored.agent_id == original.agent_id
        assert restored.user_id == original.user_id
        assert restored.metadata == original.metadata


@pytest.mark.unit
class TestHookContextBuilderInitialization:
    """Tests for HookContextBuilder initialization"""

    def test_builder_initialization_default(self):
        """Test builder initializes with generated IDs"""
        builder = HookContextBuilder()

        assert builder.request_id is not None
        assert builder.agent_id is not None
        assert builder.base_timestamp is not None
        assert len(builder.request_id) == 8
        assert len(builder.agent_id) == 8

    def test_builder_initialization_custom_ids(self):
        """Test builder initializes with custom IDs"""
        builder = HookContextBuilder(
            request_id="custom_req",
            agent_id="custom_agent"
        )

        assert builder.request_id == "custom_req"
        assert builder.agent_id == "custom_agent"

    def test_builder_initialization_partial_ids(self):
        """Test builder with only request_id"""
        builder = HookContextBuilder(request_id="req_custom")

        assert builder.request_id == "req_custom"
        assert builder.agent_id is not None


@pytest.mark.unit
class TestHookContextBuilderBuild:
    """Tests for building contexts"""

    def test_build_simple_context(self):
        """Test building simple context"""
        builder = HookContextBuilder()
        context = builder.build(HookEvent.ON_USER_INPUT, input="test")

        assert context.event == HookEvent.ON_USER_INPUT
        assert context.request_id == builder.request_id
        assert context.agent_id == builder.agent_id
        assert context.data == {"input": "test"}

    def test_build_with_user_id(self):
        """Test building context with user_id"""
        builder = HookContextBuilder()
        context = builder.build(HookEvent.ON_USER_INPUT, user_id="user_1")

        assert context.user_id == "user_1"

    def test_build_with_metadata(self):
        """Test building context with metadata"""
        builder = HookContextBuilder()
        metadata = {"source": "cli", "version": "1.0"}
        context = builder.build(
            HookEvent.ON_USER_INPUT,
            metadata=metadata,
            input="test"
        )

        assert context.metadata == metadata

    def test_build_multiple_data_fields(self):
        """Test building context with multiple data fields"""
        builder = HookContextBuilder()
        context = builder.build(
            HookEvent.ON_TOOL_EXECUTE,
            tool_name="bash",
            command="ls",
            timeout=30
        )

        assert context.data["tool_name"] == "bash"
        assert context.data["command"] == "ls"
        assert context.data["timeout"] == 30

    def test_build_preserves_builder_ids(self):
        """Test that multiple builds preserve same IDs"""
        builder = HookContextBuilder()
        request_id = builder.request_id
        agent_id = builder.agent_id

        context1 = builder.build(HookEvent.ON_USER_INPUT)
        context2 = builder.build(HookEvent.ON_AGENT_START)

        assert context1.request_id == request_id
        assert context2.request_id == request_id
        assert context1.agent_id == agent_id
        assert context2.agent_id == agent_id


@pytest.mark.unit
class TestHookContextBuilderWithParent:
    """Tests for building contexts with parent context"""

    def test_build_with_parent_context(self):
        """Test building context from parent"""
        builder = HookContextBuilder()
        parent = builder.build(HookEvent.ON_USER_INPUT, input="test")

        child = builder.build_with_parent(
            HookEvent.ON_AGENT_START,
            parent
        )

        assert child.request_id == parent.request_id
        assert child.agent_id == parent.agent_id

    def test_build_with_parent_inherits_user_id(self):
        """Test child inherits user_id from parent"""
        builder = HookContextBuilder()
        parent = builder.build(HookEvent.ON_USER_INPUT, user_id="user_123")

        child = builder.build_with_parent(HookEvent.ON_AGENT_START, parent)

        assert child.user_id == "user_123"

    def test_build_with_parent_overrides_user_id(self):
        """Test child can override user_id"""
        builder = HookContextBuilder()
        parent = builder.build(HookEvent.ON_USER_INPUT, user_id="user_123")

        child = builder.build_with_parent(
            HookEvent.ON_AGENT_START,
            parent,
            user_id="user_456"
        )

        assert child.user_id == "user_456"

    def test_build_with_parent_metadata_merge(self):
        """Test child metadata merges with parent"""
        builder = HookContextBuilder()
        parent = builder.build(
            HookEvent.ON_USER_INPUT,
            metadata={"source": "cli"}
        )

        child = builder.build_with_parent(
            HookEvent.ON_AGENT_START,
            parent,
            metadata={"action": "start"}
        )

        assert child.metadata["source"] == "cli"
        assert child.metadata["action"] == "start"

    def test_build_with_parent_includes_parent_event(self):
        """Test child metadata includes parent event"""
        builder = HookContextBuilder()
        parent = builder.build(HookEvent.ON_USER_INPUT)

        child = builder.build_with_parent(HookEvent.ON_AGENT_START, parent)

        assert child.metadata["parent_event"] == "user.input"


@pytest.mark.unit
class TestHookContextBuilderReset:
    """Tests for resetting builder"""

    def test_reset_regenerates_agent_id(self):
        """Test reset generates new agent_id"""
        builder = HookContextBuilder()
        original_agent_id = builder.agent_id

        builder.reset()

        assert builder.agent_id != original_agent_id

    def test_reset_preserves_request_id(self):
        """Test reset preserves request_id by default"""
        builder = HookContextBuilder()
        original_request_id = builder.request_id

        builder.reset()

        assert builder.request_id == original_request_id

    def test_reset_with_new_request_id(self):
        """Test reset with new_request_id=True"""
        builder = HookContextBuilder()
        original_request_id = builder.request_id
        original_agent_id = builder.agent_id

        builder.reset(new_request_id=True)

        assert builder.request_id != original_request_id
        assert builder.agent_id != original_agent_id

    def test_reset_updates_base_timestamp(self):
        """Test reset updates base_timestamp"""
        builder = HookContextBuilder()
        original_timestamp = builder.base_timestamp

        time.sleep(0.01)  # Small delay
        builder.reset()

        assert builder.base_timestamp > original_timestamp


@pytest.mark.unit
class TestHookContextBuilderChildBuilder:
    """Tests for creating child builders"""

    def test_create_child_builder_shares_request_id(self):
        """Test child builder shares request_id"""
        parent = HookContextBuilder(request_id="req_parent")
        child = parent.create_child_builder()

        assert child.request_id == parent.request_id

    def test_create_child_builder_different_agent_id(self):
        """Test child builder has different agent_id"""
        parent = HookContextBuilder()
        child = parent.create_child_builder()

        assert child.agent_id != parent.agent_id

    def test_child_builder_independence(self):
        """Test child builder is independent"""
        parent = HookContextBuilder()
        child = parent.create_child_builder()

        child.reset(new_request_id=True)

        assert child.request_id != parent.request_id

    def test_child_builder_nesting(self):
        """Test nested child builders"""
        grandparent = HookContextBuilder(request_id="req_grand")
        parent = grandparent.create_child_builder()
        child = parent.create_child_builder()

        assert child.request_id == "req_grand"
        assert parent.request_id == "req_grand"


@pytest.mark.unit
class TestHookContextBuilderIntegration:
    """Integration tests for builder"""

    def test_complete_context_chain(self):
        """Test building a complete context chain"""
        builder = HookContextBuilder()

        user_input = builder.build(
            HookEvent.ON_USER_INPUT,
            user_id="user_1",
            input="test"
        )

        agent_start = builder.build_with_parent(
            HookEvent.ON_AGENT_START,
            user_input
        )

        tool_select = builder.build_with_parent(
            HookEvent.ON_TOOL_SELECT,
            agent_start,
            tool="bash"
        )

        # All should share same request_id
        assert user_input.request_id == agent_start.request_id
        assert agent_start.request_id == tool_select.request_id

        # Parent event tracking
        assert agent_start.metadata["parent_event"] == "user.input"
        assert tool_select.metadata["parent_event"] == "agent.start"


@pytest.mark.unit
class TestHookHandler:
    """Tests for HookHandler type"""

    def test_hook_handler_is_callable(self):
        """Test HookHandler is a callable type"""
        # HookHandler should be Callable[[HookContext], Awaitable[None]]
        import inspect
        from typing import get_type_hints

        # Just verify the type alias exists and is callable
        assert HookHandler is not None

    @pytest.mark.asyncio
    async def test_hook_handler_signature(self):
        """Test hook handler can be called with context"""
        context = HookContext(
            event=HookEvent.ON_USER_INPUT,
            timestamp=0,
            data={},
            request_id="req_1",
            agent_id="agent_1"
        )

        called = False

        async def my_handler(ctx: HookContext):
            nonlocal called
            called = True
            assert ctx == context

        await my_handler(context)
        assert called is True
