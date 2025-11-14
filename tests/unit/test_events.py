"""
Unit tests for Event System

Tests event bus functionality, event types, subscriptions, and event emission.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.events import EventBus, EventType, Event, get_event_bus, reset_event_bus


@pytest.mark.unit
class TestEventType:
    """Tests for EventType enum"""

    def test_event_type_agent_lifecycle(self):
        """Test agent lifecycle event types"""
        assert EventType.AGENT_START.value == "agent_start"
        assert EventType.AGENT_END.value == "agent_end"
        assert EventType.AGENT_ERROR.value == "agent_error"

    def test_event_type_thinking_phase(self):
        """Test thinking phase event types"""
        assert EventType.AGENT_THINKING.value == "agent_thinking"
        assert EventType.AGENT_THINKING_END.value == "agent_thinking_end"

    def test_event_type_tool_selection(self):
        """Test tool selection event types"""
        assert EventType.TOOL_SELECTED.value == "tool_selected"

    def test_event_type_tool_execution(self):
        """Test tool execution event types"""
        assert EventType.TOOL_EXECUTING.value == "tool_executing"
        assert EventType.TOOL_COMPLETED.value == "tool_completed"
        assert EventType.TOOL_ERROR.value == "tool_error"

    def test_event_type_llm_communication(self):
        """Test LLM communication event types"""
        assert EventType.LLM_CALLING.value == "llm_calling"
        assert EventType.LLM_RESPONSE.value == "llm_response"

    def test_event_type_status(self):
        """Test status update event types"""
        assert EventType.STATUS_UPDATE.value == "status_update"


@pytest.mark.unit
class TestEvent:
    """Tests for Event data class"""

    def test_event_creation_with_type_only(self):
        """Test creating an event with only type"""
        event = Event(EventType.AGENT_START)

        assert event.event_type == EventType.AGENT_START
        assert event.data == {}
        assert event.timestamp is not None

    def test_event_creation_with_data(self):
        """Test creating an event with data"""
        event = Event(EventType.AGENT_START, user_input="test", session_id="123")

        assert event.event_type == EventType.AGENT_START
        assert event.data["user_input"] == "test"
        assert event.data["session_id"] == "123"

    def test_event_timestamp(self):
        """Test that event has timestamp"""
        event = Event(EventType.AGENT_START)
        assert isinstance(event.timestamp, (int, float))

    def test_event_data_persistence(self):
        """Test that event data persists"""
        data = {
            "tool_name": "Bash",
            "tool_id": "tool_123",
            "input": {"command": "ls"}
        }
        event = Event(EventType.TOOL_SELECTED, **data)

        assert event.data == data

    def test_event_multiple_data_fields(self):
        """Test event with multiple data fields"""
        event = Event(
            EventType.TOOL_COMPLETED,
            tool_name="Read",
            output="file contents",
            duration=0.5
        )

        assert event.data["tool_name"] == "Read"
        assert event.data["output"] == "file contents"
        assert event.data["duration"] == 0.5


@pytest.mark.unit
class TestEventBusBasics:
    """Tests for EventBus basic functionality"""

    def test_event_bus_initialization(self):
        """Test EventBus initialization"""
        bus = EventBus()

        assert bus._listeners == {}
        assert bus._global_listeners == []

    def test_event_bus_subscribe_single_event(self):
        """Test subscribing to a single event type"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe(EventType.AGENT_START, callback)

        assert EventType.AGENT_START in bus._listeners
        assert callback in bus._listeners[EventType.AGENT_START]

    def test_event_bus_subscribe_multiple_callbacks(self):
        """Test subscribing multiple callbacks to same event"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)

        assert len(bus._listeners[EventType.AGENT_START]) == 2
        assert callback1 in bus._listeners[EventType.AGENT_START]
        assert callback2 in bus._listeners[EventType.AGENT_START]

    def test_event_bus_subscribe_multiple_event_types(self):
        """Test subscribing to multiple event types"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.TOOL_SELECTED, callback2)

        assert EventType.AGENT_START in bus._listeners
        assert EventType.TOOL_SELECTED in bus._listeners

    def test_event_bus_subscribe_all(self):
        """Test subscribing to all events"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe_all(callback)

        assert callback in bus._global_listeners

    def test_event_bus_unsubscribe(self):
        """Test unsubscribing from specific event"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe(EventType.AGENT_START, callback)
        bus.unsubscribe(EventType.AGENT_START, callback)

        assert callback not in bus._listeners.get(EventType.AGENT_START, [])

    def test_event_bus_unsubscribe_all(self):
        """Test unsubscribing from all events"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe_all(callback)
        bus.unsubscribe_all(callback)

        assert callback not in bus._global_listeners

    def test_event_bus_clear(self):
        """Test clearing all listeners"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe_all(callback2)

        bus.clear()

        assert len(bus._listeners) == 0
        assert len(bus._global_listeners) == 0


@pytest.mark.unit
class TestEventBusEmission:
    """Tests for EventBus event emission"""

    @pytest.mark.asyncio
    async def test_emit_calls_specific_subscriber(self):
        """Test that emit calls specific event subscribers"""
        bus = EventBus()
        callback = AsyncMock()
        event = Event(EventType.AGENT_START, user_input="test")

        bus.subscribe(EventType.AGENT_START, callback)
        await bus.emit(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_calls_multiple_subscribers(self):
        """Test that emit calls multiple subscribers"""
        bus = EventBus()
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)
        await bus.emit(event)

        callback1.assert_called_once()
        callback2.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_calls_global_subscribers(self):
        """Test that emit calls global subscribers"""
        bus = EventBus()
        callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe_all(callback)
        await bus.emit(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_calls_both_specific_and_global(self):
        """Test that emit calls both specific and global subscribers"""
        bus = EventBus()
        specific_callback = AsyncMock()
        global_callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, specific_callback)
        bus.subscribe_all(global_callback)
        await bus.emit(event)

        specific_callback.assert_called_once()
        global_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_does_not_call_unsubscribed(self):
        """Test that emit doesn't call unsubscribed callbacks"""
        bus = EventBus()
        callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback)
        bus.unsubscribe(EventType.AGENT_START, callback)
        await bus.emit(event)

        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_emit_different_event_types(self):
        """Test that emit only calls callbacks for matching event types"""
        bus = EventBus()
        start_callback = AsyncMock()
        tool_callback = AsyncMock()

        bus.subscribe(EventType.AGENT_START, start_callback)
        bus.subscribe(EventType.TOOL_SELECTED, tool_callback)

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        start_callback.assert_called_once()
        tool_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_emit_with_sync_callback(self):
        """Test that emit can call sync callbacks"""
        bus = EventBus()
        callback = Mock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback)
        await bus.emit(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_handles_callback_errors(self):
        """Test that emit handles errors in callbacks gracefully"""
        bus = EventBus()
        error_callback = AsyncMock(side_effect=Exception("Test error"))
        good_callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, error_callback)
        bus.subscribe(EventType.AGENT_START, good_callback)

        # Should not raise, should continue to next callback
        await bus.emit(event)

        good_callback.assert_called_once()


@pytest.mark.unit
class TestEventBusSync:
    """Tests for EventBus sync emission"""

    def test_emit_sync_calls_sync_callback(self):
        """Test that emit_sync calls sync callbacks"""
        bus = EventBus()
        callback = Mock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback)
        bus.emit_sync(event)

        callback.assert_called_once_with(event)

    def test_emit_sync_calls_global_callback(self):
        """Test that emit_sync calls global callbacks"""
        bus = EventBus()
        callback = Mock()
        event = Event(EventType.AGENT_START)

        bus.subscribe_all(callback)
        bus.emit_sync(event)

        callback.assert_called_once_with(event)

    def test_emit_sync_handles_errors(self):
        """Test that emit_sync handles errors gracefully"""
        bus = EventBus()
        error_callback = Mock(side_effect=Exception("Test error"))
        good_callback = Mock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, error_callback)
        bus.subscribe(EventType.AGENT_START, good_callback)

        # Should not raise
        bus.emit_sync(event)

        good_callback.assert_called_once()


@pytest.mark.unit
class TestGlobalEventBus:
    """Tests for global event bus singleton"""

    def test_get_event_bus_returns_same_instance(self):
        """Test that get_event_bus returns same instance"""
        reset_event_bus()

        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_get_event_bus_creates_instance_on_first_call(self):
        """Test that get_event_bus creates instance on first call"""
        reset_event_bus()

        bus = get_event_bus()

        assert isinstance(bus, EventBus)

    def test_reset_event_bus_clears_instance(self):
        """Test that reset_event_bus clears the global instance"""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()

        assert bus1 is not bus2

    def test_global_bus_state_persistence(self):
        """Test that global bus state persists"""
        reset_event_bus()
        bus = get_event_bus()
        callback = Mock()

        bus.subscribe(EventType.AGENT_START, callback)

        # Get bus again
        bus2 = get_event_bus()
        assert EventType.AGENT_START in bus2._listeners


@pytest.mark.unit
class TestEventBusIntegration:
    """Integration tests for event bus"""

    @pytest.mark.asyncio
    async def test_multiple_event_types_workflow(self):
        """Test realistic event workflow"""
        bus = EventBus()
        events_captured = []

        async def capture_event(event: Event):
            events_captured.append(event.event_type)

        # Subscribe to multiple events
        bus.subscribe(EventType.AGENT_START, capture_event)
        bus.subscribe(EventType.AGENT_THINKING, capture_event)
        bus.subscribe(EventType.TOOL_SELECTED, capture_event)
        bus.subscribe(EventType.TOOL_COMPLETED, capture_event)
        bus.subscribe(EventType.AGENT_END, capture_event)

        # Emit workflow
        await bus.emit(Event(EventType.AGENT_START, user_input="test"))
        await bus.emit(Event(EventType.AGENT_THINKING))
        await bus.emit(Event(EventType.TOOL_SELECTED, tool_name="Read"))
        await bus.emit(Event(EventType.TOOL_COMPLETED, output="result"))
        await bus.emit(Event(EventType.AGENT_END, success=True))

        assert len(events_captured) == 5
        assert events_captured[0] == EventType.AGENT_START
        assert events_captured[4] == EventType.AGENT_END

    @pytest.mark.asyncio
    async def test_event_data_preservation_through_emission(self):
        """Test that event data is preserved through emission"""
        bus = EventBus()
        captured_event = None

        async def capture(event: Event):
            nonlocal captured_event
            captured_event = event

        bus.subscribe(EventType.TOOL_COMPLETED, capture)

        original_event = Event(
            EventType.TOOL_COMPLETED,
            tool_name="Bash",
            output="command output",
            duration=1.5
        )
        await bus.emit(original_event)

        assert captured_event.data["tool_name"] == "Bash"
        assert captured_event.data["output"] == "command output"
        assert captured_event.data["duration"] == 1.5

    @pytest.mark.asyncio
    async def test_conditional_subscription(self):
        """Test conditional event handling"""
        bus = EventBus()
        tool_events = []

        async def capture_tool_event(event: Event):
            if event.data.get("tool_name") == "Bash":
                tool_events.append(event)

        bus.subscribe_all(capture_tool_event)

        await bus.emit(Event(EventType.TOOL_SELECTED, tool_name="Bash"))
        await bus.emit(Event(EventType.TOOL_SELECTED, tool_name="Read"))
        await bus.emit(Event(EventType.TOOL_COMPLETED, tool_name="Bash"))

        assert len(tool_events) == 2

    @pytest.mark.asyncio
    async def test_concurrent_event_emission(self):
        """Test concurrent event emissions"""
        bus = EventBus()
        callback_count = {"count": 0}

        async def count_callback(event: Event):
            callback_count["count"] += 1

        bus.subscribe_all(count_callback)

        # Emit multiple events concurrently
        await asyncio.gather(
            bus.emit(Event(EventType.AGENT_START)),
            bus.emit(Event(EventType.AGENT_THINKING)),
            bus.emit(Event(EventType.TOOL_SELECTED, tool_name="Bash")),
            bus.emit(Event(EventType.TOOL_COMPLETED, output="result")),
        )

        assert callback_count["count"] == 4
