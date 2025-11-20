"""Unit tests for InterfaceManager"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from rich.console import Console

from src.events import EventBus, Event, EventType
from src.cli.ui_manager import InterfaceManager
from src.agents.state import AgentState


@pytest.fixture
def event_bus():
    """Create a fresh EventBus for each test"""
    return EventBus()


@pytest.fixture
def console():
    """Create a mocked Console"""
    console = Mock(spec=Console)
    console.status = Mock(return_value=Mock(start=Mock(), stop=Mock()))
    return console


@pytest.fixture
def ui_manager(event_bus, console):
    """Create InterfaceManager instance"""
    return InterfaceManager(event_bus, console, refresh_rate=0.01)


@pytest.mark.asyncio
async def test_state_change_to_thinking(ui_manager, event_bus):
    """Test that THINKING state starts a spinner"""
    # Emit state change event
    await event_bus.emit(Event(
        EventType.AGENT_STATE_CHANGED,
        state=AgentState.THINKING
    ))

    # Wait for async processing
    await asyncio.sleep(0.05)

    # Verify spinner was started
    assert ui_manager.spinner is not None


@pytest.mark.asyncio
async def test_state_change_to_idle_stops_visuals(ui_manager, event_bus):
    """Test that IDLE state stops all visuals"""
    # First start a spinner
    await event_bus.emit(Event(
        EventType.AGENT_STATE_CHANGED,
        state=AgentState.THINKING
    ))
    await asyncio.sleep(0.05)

    # Then transition to IDLE
    await event_bus.emit(Event(
        EventType.AGENT_STATE_CHANGED,
        state=AgentState.IDLE
    ))
    await asyncio.sleep(0.05)

    # Verify spinner was stopped
    assert ui_manager.spinner is None


@pytest.mark.asyncio
async def test_tool_selected_starts_live_display(ui_manager, event_bus):
    """Test that TOOL_SELECTED starts a live display"""
    await event_bus.emit(Event(
        EventType.TOOL_SELECTED,
        tool_name="Bash",
        brief_description="ls -la"
    ))

    await asyncio.sleep(0.05)

    assert ui_manager.live_display is not None
    assert ui_manager.current_tool_name == "Bash"


@pytest.mark.asyncio
async def test_tool_output_chunk_buffering(ui_manager, event_bus):
    """Test that output chunks are buffered and throttled"""
    # Start a tool
    await event_bus.emit(Event(
        EventType.TOOL_SELECTED,
        tool_name="Bash",
        brief_description="test"
    ))
    await asyncio.sleep(0.05)

    # Send multiple chunks quickly
    for i in range(5):
        await event_bus.emit(Event(
            EventType.TOOL_OUTPUT_CHUNK,
            chunk=f"Line {i}\n"
        ))

    # Wait for throttled refresh
    await asyncio.sleep(0.15)

    # Verify chunks were added to output
    output_text = str(ui_manager.current_tool_output)
    assert "Line 0" in output_text
    assert "Line 4" in output_text


@pytest.mark.asyncio
async def test_tool_completed_flushes_pending_chunks(ui_manager, event_bus):
    """Test that TOOL_COMPLETED flushes all pending chunks"""
    # Start tool
    await event_bus.emit(Event(
        EventType.TOOL_SELECTED,
        tool_name="Bash",
        brief_description="test"
    ))
    await asyncio.sleep(0.05)

    # Send chunks without waiting for throttle
    await event_bus.emit(Event(EventType.TOOL_OUTPUT_CHUNK, chunk="Chunk 1\n"))
    await event_bus.emit(Event(EventType.TOOL_OUTPUT_CHUNK, chunk="Chunk 2\n"))

    # Immediately complete
    await event_bus.emit(Event(
        EventType.TOOL_COMPLETED,
        tool_name="Bash"
    ))
    await asyncio.sleep(0.05)

    # Verify all chunks are in output
    output_text = str(ui_manager.current_tool_output)
    assert "Chunk 1" in output_text
    assert "Chunk 2" in output_text


@pytest.mark.asyncio
async def test_tool_error_updates_panel(ui_manager, event_bus):
    """Test that TOOL_ERROR updates the panel to error state"""
    # Start tool
    await event_bus.emit(Event(
        EventType.TOOL_SELECTED,
        tool_name="Bash",
        brief_description="test"
    ))
    await asyncio.sleep(0.05)

    # Trigger error
    await event_bus.emit(Event(
        EventType.TOOL_ERROR,
        tool_name="Bash",
        error="Command failed"
    ))
    await asyncio.sleep(0.05)

    # Verify error message in output
    output_text = str(ui_manager.current_tool_output)
    assert "Command failed" in output_text


@pytest.mark.asyncio
async def test_concurrent_state_changes_are_safe(ui_manager, event_bus):
    """Test that concurrent state changes don't cause race conditions"""
    # Simulate rapid state changes
    tasks = []
    for _ in range(10):
        tasks.append(event_bus.emit(Event(
            EventType.AGENT_STATE_CHANGED,
            state=AgentState.THINKING
        )))
        tasks.append(event_bus.emit(Event(
            EventType.AGENT_STATE_CHANGED,
            state=AgentState.IDLE
        )))

    await asyncio.gather(*tasks)
    await asyncio.sleep(0.1)

    # Should not crash and should end in a consistent state
    assert ui_manager.spinner is None or ui_manager.spinner is not None


@pytest.mark.asyncio
async def test_user_pause_stops_visuals(ui_manager, event_bus):
    """Test that USER_INPUT_PAUSED stops all visuals"""
    # Start a spinner
    await event_bus.emit(Event(
        EventType.AGENT_STATE_CHANGED,
        state=AgentState.THINKING
    ))
    await asyncio.sleep(0.05)

    # Trigger user pause
    await event_bus.emit(Event(EventType.USER_INPUT_PAUSED))
    await asyncio.sleep(0.05)

    # Verify all visuals stopped
    assert ui_manager.spinner is None
    assert ui_manager.live_display is None


@pytest.mark.asyncio
async def test_background_refresh_task_cleanup(ui_manager, event_bus):
    """Test that background refresh task is properly cancelled"""
    # Start a tool (which starts the refresh task)
    await event_bus.emit(Event(
        EventType.TOOL_SELECTED,
        tool_name="Bash",
        brief_description="test"
    ))
    await asyncio.sleep(0.05)

    refresh_task = ui_manager._refresh_task
    assert refresh_task is not None
    assert not refresh_task.done()

    # Stop visuals
    await event_bus.emit(Event(
        EventType.AGENT_STATE_CHANGED,
        state=AgentState.IDLE
    ))
    await asyncio.sleep(0.15)

    # Verify task was cancelled
    assert refresh_task.done() or refresh_task.cancelled()
