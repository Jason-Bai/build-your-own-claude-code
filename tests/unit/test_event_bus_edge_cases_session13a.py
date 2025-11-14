"""
Unit tests for Event Bus Edge Cases

Tests async emit, error isolation, sync vs async callbacks,
timestamp handling, and edge case scenarios.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.events.event_bus import EventBus, Event, EventType, get_event_bus, reset_event_bus


@pytest.mark.unit
class TestEventInitialization:
    """Tests for Event initialization"""

    def test_event_creation_with_event_type(self):
        """Test event creation with event type"""
        event = Event(EventType.AGENT_START, user_input="test")

        assert event.event_type == EventType.AGENT_START
        assert event.data["user_input"] == "test"

    def test_event_has_timestamp(self):
        """Test event has timestamp"""
        event = Event(EventType.AGENT_START)

        assert hasattr(event, 'timestamp')
        assert event.timestamp >= 0

    def test_event_with_multiple_data_fields(self):
        """Test event with multiple data fields"""
        event = Event(
            EventType.TOOL_COMPLETED,
            tool_name="Read",
            output="file content",
            duration=1.5
        )

        assert event.data["tool_name"] == "Read"
        assert event.data["output"] == "file content"
        assert event.data["duration"] == 1.5


@pytest.mark.unit
class TestEventBusInitialization:
    """Tests for EventBus initialization"""

    def test_event_bus_creates_empty_listeners(self):
        """Test EventBus initializes with empty listeners"""
        bus = EventBus()

        assert bus._listeners == {}
        assert bus._global_listeners == []

    def test_event_bus_creates_event_queue(self):
        """Test EventBus initializes event queue"""
        bus = EventBus()

        assert bus._event_queue is None  # Lazy initialized


@pytest.mark.unit
class TestAsyncEmitErrorHandling:
    """Tests for async emit error handling and isolation"""

    @pytest.mark.asyncio
    async def test_emit_continues_on_callback_error(self):
        """Test emit continues when one callback throws error"""
        bus = EventBus()
        callback1 = Mock(side_effect=Exception("First callback error"))
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)

        event = Event(EventType.AGENT_START)

        # Should not raise, should continue to callback2
        await bus.emit(event)

        callback2.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_isolates_errors_between_callbacks(self):
        """Test errors in one callback don't affect others"""
        bus = EventBus()
        callback1 = Mock(side_effect=RuntimeError("Error in callback1"))
        callback2 = Mock()
        callback3 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)
        bus.subscribe(EventType.AGENT_START, callback3)

        event = Event(EventType.AGENT_START)

        await bus.emit(event)

        # Both callback2 and callback3 should still be called
        callback2.assert_called_once_with(event)
        callback3.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_handles_global_listener_error(self):
        """Test emit handles errors in global listeners"""
        bus = EventBus()
        global_callback = Mock(side_effect=Exception("Global callback error"))
        normal_callback = Mock()

        bus.subscribe_all(global_callback)
        bus.subscribe(EventType.AGENT_START, normal_callback)

        event = Event(EventType.AGENT_START)

        # Should not raise
        await bus.emit(event)

        # Both should be attempted
        global_callback.assert_called_once_with(event)
        normal_callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_async_callback_execution(self):
        """Test emit executes async callbacks correctly"""
        bus = EventBus()
        async_callback = AsyncMock()

        bus.subscribe(EventType.AGENT_START, async_callback)

        event = Event(EventType.AGENT_START)

        await bus.emit(event)

        async_callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_mixed_sync_async_callbacks(self):
        """Test emit handles mixed sync and async callbacks"""
        bus = EventBus()
        sync_callback = Mock()
        async_callback = AsyncMock()

        bus.subscribe(EventType.AGENT_START, sync_callback)
        bus.subscribe(EventType.AGENT_START, async_callback)

        event = Event(EventType.AGENT_START)

        await bus.emit(event)

        sync_callback.assert_called_once_with(event)
        async_callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_emit_to_multiple_event_types(self):
        """Test emit calls correct event type listeners"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_END, callback2)

        event = Event(EventType.AGENT_START)

        await bus.emit(event)

        callback1.assert_called_once_with(event)
        callback2.assert_not_called()


@pytest.mark.unit
class TestSyncEmitWarnings:
    """Tests for sync emit warnings and behavior"""

    def test_emit_sync_with_sync_callback(self):
        """Test emit_sync calls sync callbacks"""
        bus = EventBus()
        callback = Mock()

        bus.subscribe(EventType.AGENT_START, callback)

        event = Event(EventType.AGENT_START)
        bus.emit_sync(event)

        callback.assert_called_once_with(event)

    def test_emit_sync_skips_async_callback(self):
        """Test emit_sync warns and skips async callbacks"""
        bus = EventBus()
        async_callback = AsyncMock()

        bus.subscribe(EventType.AGENT_START, async_callback)

        event = Event(EventType.AGENT_START)

        with patch('src.events.event_bus.logger') as mock_logger:
            bus.emit_sync(event)
            # Should log warning about async callback
            mock_logger.warning.assert_called()

        # Async callback should not be called
        async_callback.assert_not_called()

    def test_emit_sync_handles_callback_error(self):
        """Test emit_sync handles callback errors"""
        bus = EventBus()
        callback = Mock(side_effect=ValueError("Sync error"))

        bus.subscribe(EventType.AGENT_START, callback)

        event = Event(EventType.AGENT_START)

        # Should not raise
        bus.emit_sync(event)

    def test_emit_sync_global_listener_error(self):
        """Test emit_sync handles global listener errors"""
        bus = EventBus()
        global_callback = Mock(side_effect=RuntimeError("Global error"))

        bus.subscribe_all(global_callback)

        event = Event(EventType.AGENT_START)

        # Should not raise
        bus.emit_sync(event)


@pytest.mark.unit
class TestGlobalListeners:
    """Tests for global listener functionality"""

    @pytest.mark.asyncio
    async def test_global_listener_receives_all_events(self):
        """Test global listener receives all event types"""
        bus = EventBus()
        global_callback = AsyncMock()

        bus.subscribe_all(global_callback)

        events = [
            Event(EventType.AGENT_START),
            Event(EventType.AGENT_THINKING),
            Event(EventType.TOOL_SELECTED),
            Event(EventType.AGENT_END),
        ]

        for event in events:
            await bus.emit(event)

        assert global_callback.call_count == 4

    @pytest.mark.asyncio
    async def test_specific_and_global_listeners(self):
        """Test specific and global listeners work together"""
        bus = EventBus()
        specific_callback = AsyncMock()
        global_callback = AsyncMock()

        bus.subscribe(EventType.AGENT_START, specific_callback)
        bus.subscribe_all(global_callback)

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        specific_callback.assert_called_once_with(event)
        global_callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_multiple_global_listeners(self):
        """Test multiple global listeners work together"""
        bus = EventBus()
        global1 = AsyncMock()
        global2 = AsyncMock()
        global3 = AsyncMock()

        bus.subscribe_all(global1)
        bus.subscribe_all(global2)
        bus.subscribe_all(global3)

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        global1.assert_called_once_with(event)
        global2.assert_called_once_with(event)
        global3.assert_called_once_with(event)


@pytest.mark.unit
class TestUnsubscribe:
    """Tests for unsubscribe functionality"""

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_callback(self):
        """Test unsubscribe removes callback from listeners"""
        bus = EventBus()
        callback = AsyncMock()

        bus.subscribe(EventType.AGENT_START, callback)
        bus.unsubscribe(EventType.AGENT_START, callback)

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_unsubscribe_all_removes_global(self):
        """Test unsubscribe_all removes global listener"""
        bus = EventBus()
        callback = AsyncMock()

        bus.subscribe_all(callback)
        bus.unsubscribe_all(callback)

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_unsubscribe_specific_leaves_others(self):
        """Test unsubscribe only removes specified callback"""
        bus = EventBus()
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_START, callback2)

        bus.unsubscribe(EventType.AGENT_START, callback1)

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        callback1.assert_not_called()
        callback2.assert_called_once_with(event)


@pytest.mark.unit
class TestClearFunctionality:
    """Tests for clearing listeners"""

    @pytest.mark.asyncio
    async def test_clear_removes_all_listeners(self):
        """Test clear removes all event listeners"""
        bus = EventBus()
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.subscribe(EventType.AGENT_END, callback2)

        bus.clear()

        event1 = Event(EventType.AGENT_START)
        event2 = Event(EventType.AGENT_END)

        await bus.emit(event1)
        await bus.emit(event2)

        callback1.assert_not_called()
        callback2.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_removes_global_listeners(self):
        """Test clear removes global listeners"""
        bus = EventBus()
        global_callback = AsyncMock()

        bus.subscribe_all(global_callback)
        bus.clear()

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        global_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_clear_removes_both_specific_and_global(self):
        """Test clear removes both specific and global listeners"""
        bus = EventBus()
        specific = AsyncMock()
        global_cb = AsyncMock()

        bus.subscribe(EventType.AGENT_START, specific)
        bus.subscribe_all(global_cb)

        bus.clear()

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        specific.assert_not_called()
        global_cb.assert_not_called()


@pytest.mark.unit
class TestEventQueue:
    """Tests for event queue initialization"""

    @pytest.mark.asyncio
    async def test_ensure_queue_creates_queue(self):
        """Test _ensure_queue creates event queue"""
        bus = EventBus()

        assert bus._event_queue is None

        await bus._ensure_queue()

        assert bus._event_queue is not None
        assert isinstance(bus._event_queue, asyncio.Queue)

    @pytest.mark.asyncio
    async def test_ensure_queue_idempotent(self):
        """Test _ensure_queue is idempotent"""
        bus = EventBus()

        await bus._ensure_queue()
        queue1 = bus._event_queue

        await bus._ensure_queue()
        queue2 = bus._event_queue

        assert queue1 is queue2


@pytest.mark.unit
class TestGlobalEventBus:
    """Tests for global event bus singleton"""

    def test_get_event_bus_returns_singleton(self):
        """Test get_event_bus returns same instance"""
        reset_event_bus()

        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2

    def test_reset_event_bus_clears_singleton(self):
        """Test reset_event_bus clears singleton"""
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()

        assert bus1 is not bus2

    def test_global_bus_persists_listeners(self):
        """Test global bus persists listeners across calls"""
        reset_event_bus()

        bus = get_event_bus()
        callback = Mock()
        bus.subscribe(EventType.AGENT_START, callback)

        bus2 = get_event_bus()
        assert EventType.AGENT_START in bus2._listeners
        assert callback in bus2._listeners[EventType.AGENT_START]


@pytest.mark.unit
class TestEventDataTypes:
    """Tests for various event data types"""

    @pytest.mark.asyncio
    async def test_emit_with_string_data(self):
        """Test emit with string data"""
        bus = EventBus()
        callback = AsyncMock()

        bus.subscribe(EventType.AGENT_START, callback)

        event = Event(EventType.AGENT_START, message="test message")
        await bus.emit(event)

        assert callback.call_args[0][0].data["message"] == "test message"

    @pytest.mark.asyncio
    async def test_emit_with_dict_data(self):
        """Test emit with dict data"""
        bus = EventBus()
        callback = AsyncMock()

        bus.subscribe(EventType.TOOL_COMPLETED, callback)

        result_data = {"status": "success", "lines": 42}
        event = Event(EventType.TOOL_COMPLETED, result=result_data)
        await bus.emit(event)

        assert callback.call_args[0][0].data["result"] == result_data

    @pytest.mark.asyncio
    async def test_emit_with_numeric_data(self):
        """Test emit with numeric data"""
        bus = EventBus()
        callback = AsyncMock()

        bus.subscribe(EventType.AGENT_THINKING, callback)

        event = Event(EventType.AGENT_THINKING, turn=5, total_tokens=1000)
        await bus.emit(event)

        data = callback.call_args[0][0].data
        assert data["turn"] == 5
        assert data["total_tokens"] == 1000


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    @pytest.mark.asyncio
    async def test_emit_with_no_listeners(self):
        """Test emit works with no listeners"""
        bus = EventBus()

        event = Event(EventType.AGENT_START)

        # Should not raise
        await bus.emit(event)

    @pytest.mark.asyncio
    async def test_emit_same_callback_multiple_times(self):
        """Test emit with same callback subscribed multiple times"""
        bus = EventBus()
        callback = AsyncMock()

        bus.subscribe(EventType.AGENT_START, callback)
        bus.subscribe(EventType.AGENT_START, callback)

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        # Callback should be called twice
        assert callback.call_count == 2

    def test_unsubscribe_nonexistent_callback(self):
        """Test unsubscribe with nonexistent callback"""
        bus = EventBus()
        callback = Mock()

        # Should not raise
        bus.unsubscribe(EventType.AGENT_START, callback)

    def test_unsubscribe_all_nonexistent_global(self):
        """Test unsubscribe_all with nonexistent global callback"""
        bus = EventBus()
        callback = Mock()

        # Should not raise
        bus.unsubscribe_all(callback)

    @pytest.mark.asyncio
    async def test_emit_after_clear(self):
        """Test emit works after clear"""
        bus = EventBus()
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        bus.subscribe(EventType.AGENT_START, callback1)
        bus.clear()
        bus.subscribe(EventType.AGENT_START, callback2)

        event = Event(EventType.AGENT_START)
        await bus.emit(event)

        callback1.assert_not_called()
        callback2.assert_called_once_with(event)
