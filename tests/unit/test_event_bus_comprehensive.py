"""
Unit tests for EventBus

Tests event subscription, publishing, filtering, async/sync handling,
error handling, and event lifecycle management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.events.event_bus import Event, EventBus, EventType, get_event_bus, reset_event_bus


@pytest.mark.unit
class TestEventInitialization:
    """Tests for Event creation"""

    def test_event_creation_with_type(self):
        """Test creating event with type"""
        event = Event(EventType.AGENT_START)

        assert event.event_type == EventType.AGENT_START
        assert isinstance(event.data, dict)

    def test_event_creation_with_data(self):
        """Test creating event with data"""
        event = Event(EventType.AGENT_START, agent="test", status="ready")

        assert event.event_type == EventType.AGENT_START
        assert event.data["agent"] == "test"
        assert event.data["status"] == "ready"

    def test_event_creation_with_timestamp(self):
        """Test event has timestamp"""
        event = Event(EventType.AGENT_START)

        assert event.timestamp is not None

    def test_event_data_is_dict(self):
        """Test event data is dictionary"""
        event = Event(EventType.TOOL_SELECTED, tool="bash")

        assert isinstance(event.data, dict)
        assert event.data["tool"] == "bash"


@pytest.mark.unit
class TestEventTypeEnum:
    """Tests for EventType enum"""

    def test_event_type_agent_start(self):
        """Test AGENT_START event type"""
        assert EventType.AGENT_START.value == "agent_start"

    def test_event_type_agent_end(self):
        """Test AGENT_END event type"""
        assert EventType.AGENT_END.value == "agent_end"

    def test_event_type_tool_selected(self):
        """Test TOOL_SELECTED event type"""
        assert EventType.TOOL_SELECTED.value == "tool_selected"

    def test_event_type_tool_completed(self):
        """Test TOOL_COMPLETED event type"""
        assert EventType.TOOL_COMPLETED.value == "tool_completed"

    def test_event_type_iteration(self):
        """Test can iterate all event types"""
        types = list(EventType)
        assert len(types) > 0


@pytest.mark.unit
class TestEventBusInitialization:
    """Tests for EventBus initialization"""

    def test_bus_initialization(self):
        """Test EventBus initializes correctly"""
        bus = EventBus()

        assert isinstance(bus._listeners, dict)
        assert isinstance(bus._global_listeners, list)

    def test_bus_empty_on_creation(self):
        """Test EventBus is empty on creation"""
        bus = EventBus()

        assert len(bus._listeners) == 0
        assert len(bus._global_listeners) == 0


@pytest.mark.unit
class TestEventSubscription:
    """Tests for event subscription"""

    def test_subscribe_to_event(self):
        """Test subscribing to specific event"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe(EventType.AGENT_START, callback)

        assert EventType.AGENT_START in bus._listeners
        assert callback in bus._listeners[EventType.AGENT_START]

    def test_subscribe_multiple_callbacks(self):
        """Test multiple callbacks for same event"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)

        assert len(bus._listeners[EventType.AGENT_START]) == 2

    def test_subscribe_all_events(self):
        """Test subscribing to all events"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe_all(callback)

        assert callback in bus._global_listeners

    def test_subscribe_multiple_global_callbacks(self):
        """Test multiple global callbacks"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe_all(callback1)
        bus.subscribe_all(callback2)

        assert len(bus._global_listeners) == 2


@pytest.mark.unit
class TestEventUnsubscription:
    """Tests for event unsubscription"""

    def test_unsubscribe_from_event(self):
        """Test unsubscribing from event"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe(EventType.AGENT_START, callback)
        bus.unsubscribe(EventType.AGENT_START, callback)

        assert callback not in bus._listeners.get(EventType.AGENT_START, [])

    def test_unsubscribe_nonexistent_callback(self):
        """Test unsubscribing nonexistent callback"""
        bus = EventBus()
        callback = Mock()

        # Should not raise error
        bus.unsubscribe(EventType.AGENT_START, callback)

    def test_unsubscribe_all_global(self):
        """Test unsubscribing from global listeners"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe_all(callback)
        bus.unsubscribe_all(callback)

        assert callback not in bus._global_listeners

    def test_unsubscribe_leaves_other_callbacks(self):
        """Test unsubscribing one callback leaves others"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)
        bus.unsubscribe(EventType.AGENT_START, callback1)

        assert callback1 not in bus._listeners[EventType.AGENT_START]
        assert callback2 in bus._listeners[EventType.AGENT_START]


@pytest.mark.unit
class TestEventEmission:
    """Tests for emitting events"""

    @pytest.mark.asyncio
    async def test_emit_to_subscribed_callback(self):
        """Test emit calls subscribed callback"""
        bus = EventBus()
        callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback)
        await bus.emit(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_to_multiple_callbacks(self):
        """Test emit calls all subscribed callbacks"""
        bus = EventBus()
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)
        await bus.emit(event)

        callback1.assert_called_once_with(event)
        callback2.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_to_global_listeners(self):
        """Test emit calls global listeners"""
        bus = EventBus()
        callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe_all(callback)
        await bus.emit(event)

        callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_to_both_specific_and_global(self):
        """Test emit calls both specific and global listeners"""
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
    async def test_emit_unrelated_event(self):
        """Test emit to event with no subscribers"""
        bus = EventBus()
        callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_END, callback)
        await bus.emit(event)

        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_emit_sync_callback(self):
        """Test emit with synchronous callback"""
        bus = EventBus()
        callback = Mock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback)
        await bus.emit(event)

        callback.assert_called_once_with(event)


@pytest.mark.unit
class TestSyncEmission:
    """Tests for synchronous event emission"""

    def test_emit_sync_to_sync_callback(self):
        """Test sync emit calls sync callback"""
        bus = EventBus()
        callback = Mock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback)
        bus.emit_sync(event)

        callback.assert_called_once_with(event)

    def test_emit_sync_multiple_callbacks(self):
        """Test sync emit calls multiple callbacks"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)
        bus.emit_sync(event)

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_emit_sync_skips_async_callback(self):
        """Test sync emit skips async callbacks"""
        bus = EventBus()
        async_callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, async_callback)
        # Should not raise error, but won't call async callback
        bus.emit_sync(event)


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_emit_continues_on_callback_error(self):
        """Test emit continues despite callback error"""
        bus = EventBus()

        async def failing_callback(event):
            raise ValueError("Test error")

        callback2 = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, failing_callback)
        bus.subscribe(EventType.AGENT_START, callback2)
        # Should not raise
        await bus.emit(event)

        # Second callback should still be called
        callback2.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_global_continues_on_error(self):
        """Test global emit continues on error"""
        bus = EventBus()

        async def failing_callback(event):
            raise ValueError("Test error")

        callback2 = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe_all(failing_callback)
        bus.subscribe_all(callback2)
        await bus.emit(event)

        callback2.assert_called_once()


@pytest.mark.unit
class TestClear:
    """Tests for clearing listeners"""

    def test_clear_all_listeners(self):
        """Test clearing all listeners"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe_all(callback2)

        bus.clear()

        assert len(bus._listeners) == 0
        assert len(bus._global_listeners) == 0

    def test_clear_specific_event(self):
        """Test clearing specific event listeners"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_END, callback2)

        # Note: EventBus.clear() doesn't support specific event clearing
        # Only full clear is available
        bus.clear()

        assert len(bus._listeners) == 0


@pytest.mark.unit
class TestGlobalEventBus:
    """Tests for global event bus singleton"""

    def test_get_event_bus_returns_instance(self):
        """Test get_event_bus returns EventBus instance"""
        reset_event_bus()
        bus = get_event_bus()

        assert isinstance(bus, EventBus)

    def test_get_event_bus_singleton(self):
        """Test get_event_bus returns same instance"""
        reset_event_bus()
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_reset_event_bus(self):
        """Test resetting global event bus"""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()

        assert bus1 is not bus2

    def test_global_bus_after_reset(self):
        """Test global bus is fresh after reset"""
        get_event_bus().subscribe(EventType.AGENT_START, Mock())
        reset_event_bus()
        bus = get_event_bus()

        assert len(bus._listeners) == 0


@pytest.mark.unit
class TestEventData:
    """Tests for event data handling"""

    def test_event_data_with_multiple_fields(self):
        """Test event data with multiple fields"""
        event = Event(
            EventType.TOOL_SELECTED,
            tool="bash",
            command="ls",
            timeout=30
        )

        assert event.data["tool"] == "bash"
        assert event.data["command"] == "ls"
        assert event.data["timeout"] == 30

    def test_event_data_with_nested_dict(self):
        """Test event data with nested dictionary"""
        event = Event(
            EventType.TOOL_COMPLETED,
            result={"status": "success", "output": "test"}
        )

        assert event.data["result"]["status"] == "success"

    def test_event_data_with_none_value(self):
        """Test event data with None value"""
        event = Event(EventType.AGENT_END, error=None)

        assert event.data["error"] is None


@pytest.mark.unit
class TestIntegration:
    """Integration tests for EventBus"""

    @pytest.mark.asyncio
    async def test_subscribe_emit_workflow(self):
        """Test complete subscribe and emit workflow"""
        bus = EventBus()
        events_received = []

        async def collector(event):
            events_received.append(event.event_type)

        bus.subscribe(EventType.AGENT_START, collector)
        bus.subscribe(EventType.AGENT_END, collector)

        await bus.emit(Event(EventType.AGENT_START))
        await bus.emit(Event(EventType.AGENT_END))

        assert events_received == [EventType.AGENT_START, EventType.AGENT_END]

    @pytest.mark.asyncio
    async def test_multiple_event_types(self):
        """Test handling multiple event types"""
        bus = EventBus()
        start_count = 0
        end_count = 0

        async def on_start(event):
            nonlocal start_count
            start_count += 1

        async def on_end(event):
            nonlocal end_count
            end_count += 1

        bus.subscribe(EventType.AGENT_START, on_start)
        bus.subscribe(EventType.AGENT_END, on_end)

        await bus.emit(Event(EventType.AGENT_START))
        await bus.emit(Event(EventType.AGENT_START))
        await bus.emit(Event(EventType.AGENT_END))

        assert start_count == 2
        assert end_count == 1

    @pytest.mark.asyncio
    async def test_global_listener_receives_all(self):
        """Test global listener receives all events"""
        bus = EventBus()
        events = []

        async def global_listener(event):
            events.append(event.event_type)

        bus.subscribe_all(global_listener)

        await bus.emit(Event(EventType.AGENT_START))
        await bus.emit(Event(EventType.TOOL_SELECTED))
        await bus.emit(Event(EventType.AGENT_END))

        assert len(events) == 3


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    def test_subscribe_same_callback_multiple_times(self):
        """Test subscribing same callback multiple times"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe(EventType.AGENT_START, callback)
        bus.subscribe(EventType.AGENT_START, callback)

        # Should have callback twice
        assert bus._listeners[EventType.AGENT_START].count(callback) == 2

    @pytest.mark.asyncio
    async def test_emit_empty_data(self):
        """Test emitting event with no data"""
        bus = EventBus()
        callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe(EventType.AGENT_START, callback)
        await bus.emit(event)

        assert callback.call_args[0][0].data == {}

    @pytest.mark.asyncio
    async def test_emit_with_callback_exception_in_global(self):
        """Test global callback exception doesn't block others"""
        bus = EventBus()

        async def failing_global(event):
            raise RuntimeError("Global error")

        callback = AsyncMock()
        event = Event(EventType.AGENT_START)

        bus.subscribe_all(failing_global)
        bus.subscribe_all(callback)
        await bus.emit(event)

        # Second callback should still be called
        callback.assert_called_once()
