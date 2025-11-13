"""
Unit tests for Hook System module

Tests hook event types, context management, and hook lifecycle.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from src.hooks.types import HookEvent, HookContext, HookHandler


@pytest.mark.unit
class TestHookEventEnum:
    """Tests for HookEvent enumeration"""

    def test_all_hook_events_exist(self):
        """Test all hook event types are defined"""
        events = [
            HookEvent.ON_USER_INPUT,
            HookEvent.ON_COMMAND_PARSE,
            HookEvent.ON_AGENT_START,
            HookEvent.ON_AGENT_END,
            HookEvent.ON_AGENT_ERROR,
            HookEvent.ON_THINKING,
            HookEvent.ON_DECISION,
            HookEvent.ON_TOOL_SELECT,
            HookEvent.ON_TOOL_EXECUTE,
            HookEvent.ON_TOOL_RESULT,
            HookEvent.ON_TOOL_ERROR,
            HookEvent.ON_PERMISSION_CHECK,
            HookEvent.ON_OUTPUT_FORMAT,
            HookEvent.ON_OUTPUT_RENDER,
            HookEvent.ON_OUTPUT_SEND,
            HookEvent.ON_ERROR,
            HookEvent.ON_RECOVERY,
            HookEvent.ON_SHUTDOWN,
            HookEvent.ON_METRICS,
        ]
        assert len(events) == 19

    def test_hook_event_values(self):
        """Test hook event values are properly formatted"""
        assert HookEvent.ON_USER_INPUT.value == "user.input"
        assert HookEvent.ON_AGENT_START.value == "agent.start"
        assert HookEvent.ON_TOOL_EXECUTE.value == "tool.execute"
        assert HookEvent.ON_SHUTDOWN.value == "system.shutdown"

    def test_hook_event_categories(self):
        """Test hook events are organized by category"""
        user_events = [e for e in HookEvent if "user." in e.value]
        agent_events = [e for e in HookEvent if "agent." in e.value]
        tool_events = [e for e in HookEvent if "tool." in e.value]
        system_events = [e for e in HookEvent if "system." in e.value]

        assert len(user_events) >= 1
        assert len(agent_events) >= 3
        assert len(tool_events) >= 4
        assert len(system_events) >= 4


@pytest.mark.unit
class TestHookContext:
    """Tests for HookContext dataclass"""

    def test_hook_context_initialization(self):
        """Test creating a HookContext"""
        context = HookContext(
            event=HookEvent.ON_TOOL_EXECUTE,
            timestamp=time.time(),
            data={"tool_name": "read"},
            request_id="req-123",
            agent_id="agent-456",
            user_id="user-789"
        )

        assert context.event == HookEvent.ON_TOOL_EXECUTE
        assert context.data["tool_name"] == "read"
        assert context.request_id == "req-123"
        assert context.agent_id == "agent-456"
        assert context.user_id == "user-789"

    def test_hook_context_default_values(self):
        """Test HookContext with default values"""
        context = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456"
        )

        assert context.user_id is None
        assert context.metadata == {}

    def test_hook_context_to_dict(self):
        """Test converting HookContext to dictionary"""
        timestamp = time.time()
        context = HookContext(
            event=HookEvent.ON_TOOL_EXECUTE,
            timestamp=timestamp,
            data={"tool": "bash"},
            request_id="req-123",
            agent_id="agent-456",
            user_id="user-789",
            metadata={"priority": "high"}
        )

        data = context.to_dict()
        assert data["event"] == "tool.execute"
        assert data["timestamp"] == timestamp
        assert data["data"]["tool"] == "bash"
        assert data["request_id"] == "req-123"
        assert data["metadata"]["priority"] == "high"

    def test_hook_context_from_dict(self):
        """Test creating HookContext from dictionary"""
        original_data = {
            "event": "tool.execute",
            "timestamp": time.time(),
            "data": {"tool": "read"},
            "request_id": "req-123",
            "agent_id": "agent-456",
            "user_id": "user-789",
            "metadata": {"source": "cli"}
        }

        context = HookContext.from_dict(original_data)

        assert context.event == HookEvent.ON_TOOL_EXECUTE
        assert context.data["tool"] == "read"
        assert context.request_id == "req-123"
        assert context.metadata["source"] == "cli"

    def test_hook_context_roundtrip(self):
        """Test roundtrip conversion to/from dict"""
        original = HookContext(
            event=HookEvent.ON_AGENT_ERROR,
            timestamp=time.time(),
            data={"error": "test error"},
            request_id="req-123",
            agent_id="agent-456",
            user_id="user-789",
            metadata={"severity": "high"}
        )

        data = original.to_dict()
        restored = HookContext.from_dict(data)

        assert restored.event == original.event
        assert restored.timestamp == original.timestamp
        assert restored.data == original.data
        assert restored.request_id == original.request_id
        assert restored.metadata == original.metadata

    def test_hook_context_with_complex_data(self):
        """Test HookContext with complex nested data"""
        complex_data = {
            "tool": "bash",
            "params": {"command": "ls -la"},
            "result": {
                "output": "file1.txt\nfile2.txt",
                "status": "success"
            },
            "metadata": {
                "execution_time": 0.123,
                "retry_count": 2
            }
        }

        context = HookContext(
            event=HookEvent.ON_TOOL_RESULT,
            timestamp=time.time(),
            data=complex_data,
            request_id="req-123",
            agent_id="agent-456"
        )

        assert context.data["params"]["command"] == "ls -la"
        assert context.data["result"]["status"] == "success"

    def test_hook_context_missing_user_id(self):
        """Test HookContext handles missing user_id gracefully"""
        data = {
            "event": "agent.start",
            "timestamp": time.time(),
            "data": {},
            "request_id": "req-123",
            "agent_id": "agent-456"
        }

        context = HookContext.from_dict(data)
        assert context.user_id is None

    def test_hook_context_metadata_isolation(self):
        """Test that metadata doesn't share state between instances"""
        context1 = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=time.time(),
            data={},
            request_id="req-1",
            agent_id="agent-1"
        )
        context1.metadata["key"] = "value1"

        context2 = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=time.time(),
            data={},
            request_id="req-2",
            agent_id="agent-2"
        )

        assert "key" not in context2.metadata
        assert context1.metadata["key"] == "value1"


@pytest.mark.unit
class TestHookEventCategories:
    """Tests for hook event categories"""

    def test_user_interaction_events(self):
        """Test user interaction event category"""
        events = [HookEvent.ON_USER_INPUT, HookEvent.ON_COMMAND_PARSE]
        for event in events:
            assert "user." in event.value or "command." in event.value

    def test_agent_lifecycle_events(self):
        """Test agent lifecycle event category"""
        events = [
            HookEvent.ON_AGENT_START,
            HookEvent.ON_AGENT_END,
            HookEvent.ON_AGENT_ERROR
        ]
        for event in events:
            assert "agent." in event.value

    def test_tool_execution_events(self):
        """Test tool execution event category"""
        events = [
            HookEvent.ON_TOOL_SELECT,
            HookEvent.ON_TOOL_EXECUTE,
            HookEvent.ON_TOOL_RESULT,
            HookEvent.ON_TOOL_ERROR
        ]
        for event in events:
            assert "tool." in event.value

    def test_system_events(self):
        """Test system event category"""
        events = [
            HookEvent.ON_ERROR,
            HookEvent.ON_RECOVERY,
            HookEvent.ON_SHUTDOWN,
            HookEvent.ON_METRICS
        ]
        for event in events:
            assert "system." in event.value

    def test_output_events(self):
        """Test output event category"""
        events = [
            HookEvent.ON_OUTPUT_FORMAT,
            HookEvent.ON_OUTPUT_RENDER,
            HookEvent.ON_OUTPUT_SEND
        ]
        for event in events:
            assert "output." in event.value


@pytest.mark.unit
class TestHookContextEdgeCases:
    """Tests for edge cases in HookContext"""

    def test_hook_context_empty_data(self):
        """Test HookContext with empty data"""
        context = HookContext(
            event=HookEvent.ON_SHUTDOWN,
            timestamp=time.time(),
            data={},
            request_id="req-123",
            agent_id="agent-456"
        )

        assert context.data == {}
        assert context.to_dict()["data"] == {}

    def test_hook_context_timestamp_precision(self):
        """Test HookContext preserves timestamp precision"""
        timestamp = time.time()
        context = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=timestamp,
            data={},
            request_id="req-123",
            agent_id="agent-456"
        )

        assert context.timestamp == timestamp

    def test_hook_context_special_characters_in_ids(self):
        """Test HookContext with special characters in IDs"""
        context = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=time.time(),
            data={},
            request_id="req-123-456_789",
            agent_id="agent:special:id",
            user_id="user@example.com"
        )

        assert context.request_id == "req-123-456_789"
        assert context.agent_id == "agent:special:id"
        assert context.user_id == "user@example.com"

    def test_hook_context_large_data(self):
        """Test HookContext with large data payload"""
        large_data = {
            "content": "x" * 10000,
            "items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]
        }

        context = HookContext(
            event=HookEvent.ON_OUTPUT_SEND,
            timestamp=time.time(),
            data=large_data,
            request_id="req-123",
            agent_id="agent-456"
        )

        assert len(context.data["content"]) == 10000
        assert len(context.data["items"]) == 1000

    def test_hook_context_unicode_support(self):
        """Test HookContext with unicode data"""
        context = HookContext(
            event=HookEvent.ON_AGENT_START,
            timestamp=time.time(),
            data={"message": "你好 🎉 مرحبا"},
            request_id="req-123",
            agent_id="agent-456"
        )

        assert context.data["message"] == "你好 🎉 مرحبا"


@pytest.mark.unit
class TestHookTypeSystem:
    """Tests for hook type system"""

    def test_hook_handler_type_hint(self):
        """Test HookHandler type hint is defined"""
        # HookHandler should be a callable that takes HookContext and returns Awaitable[None]
        assert HookHandler is not None

    def test_hook_event_enumeration_complete(self):
        """Test all hook events are properly enumerated"""
        hook_events = list(HookEvent)
        assert len(hook_events) > 0
        for event in hook_events:
            assert isinstance(event, HookEvent)
            assert isinstance(event.value, str)

    def test_hook_context_serializable(self):
        """Test HookContext can be serialized and deserialized"""
        original = HookContext(
            event=HookEvent.ON_TOOL_EXECUTE,
            timestamp=time.time(),
            data={"test": "data"},
            request_id="req-123",
            agent_id="agent-456"
        )

        # Simulate serialization
        serialized = original.to_dict()
        deserialized = HookContext.from_dict(serialized)

        # Compare all fields
        assert deserialized.event == original.event
        assert deserialized.timestamp == original.timestamp
        assert deserialized.data == original.data
        assert deserialized.request_id == original.request_id
        assert deserialized.agent_id == original.agent_id
