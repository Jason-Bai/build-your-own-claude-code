"""Unit tests for UICoordinator"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from rich.console import Console

from src.events import EventBus, Event, EventType
from src.cli.ui_coordinator import UICoordinator, UIMode, init_coordinator, reset_coordinator
from src.cli.ui_manager import InterfaceManager


@pytest.fixture
def event_bus():
    """Create a fresh EventBus"""
    return EventBus()


@pytest.fixture
def console():
    """Create a mocked Console"""
    return Mock(spec=Console)


@pytest.fixture
def coordinator(event_bus, console):
    """Create UICoordinator instance"""
    reset_coordinator()
    return UICoordinator(event_bus, console, enable_reactive_ui=True)


@pytest.mark.asyncio
async def test_coordinator_initialization_reactive(event_bus, console):
    """Test coordinator initializes in REACTIVE mode"""
    coordinator = UICoordinator(event_bus, console, enable_reactive_ui=True)

    assert coordinator.current_mode == UIMode.REACTIVE
    assert coordinator.interface_manager is not None
    assert coordinator.enable_reactive


@pytest.mark.asyncio
async def test_coordinator_initialization_legacy(event_bus, console):
    """Test coordinator initializes in LEGACY mode when disabled"""
    coordinator = UICoordinator(event_bus, console, enable_reactive_ui=False)

    assert coordinator.current_mode == UIMode.LEGACY
    assert coordinator.interface_manager is None
    assert not coordinator.enable_reactive


@pytest.mark.asyncio
async def test_permission_requested_switches_to_interactive(coordinator, event_bus):
    """Test PERMISSION_REQUESTED switches to INTERACTIVE mode"""
    # Start in REACTIVE mode
    assert coordinator.current_mode == UIMode.REACTIVE

    # Emit PERMISSION_REQUESTED
    await event_bus.emit(Event(
        EventType.PERMISSION_REQUESTED,
        tool_name="Bash",
        level="dangerous"
    ))

    await asyncio.sleep(0.05)

    # Should switch to INTERACTIVE
    assert coordinator.current_mode == UIMode.INTERACTIVE


@pytest.mark.asyncio
async def test_permission_resolved_switches_back_to_reactive(coordinator, event_bus):
    """Test PERMISSION_RESOLVED switches back to REACTIVE mode"""
    # First switch to INTERACTIVE
    await event_bus.emit(Event(EventType.PERMISSION_REQUESTED, tool_name="Bash"))
    await asyncio.sleep(0.05)
    assert coordinator.current_mode == UIMode.INTERACTIVE

    # Then resolve permission
    await event_bus.emit(Event(EventType.PERMISSION_RESOLVED, tool_name="Bash"))
    await asyncio.sleep(0.05)

    # Should switch back to REACTIVE
    assert coordinator.current_mode == UIMode.REACTIVE


@pytest.mark.asyncio
async def test_permission_flow_pauses_and_resumes_interface(coordinator, event_bus):
    """Test permission flow actually pauses/resumes InterfaceManager"""
    interface = coordinator.interface_manager

    # Mock the pause/resume methods
    interface.pause = AsyncMock()
    interface.resume = AsyncMock()

    # Simulate permission request
    await event_bus.emit(Event(EventType.PERMISSION_REQUESTED, tool_name="Bash"))
    await asyncio.sleep(0.05)

    # Verify pause was called
    interface.pause.assert_called_once()

    # Simulate permission resolved
    await event_bus.emit(Event(EventType.PERMISSION_RESOLVED, tool_name="Bash"))
    await asyncio.sleep(0.05)

    # Verify resume was called
    interface.resume.assert_called_once()


@pytest.mark.asyncio
async def test_mode_query_methods(coordinator):
    """Test is_reactive_mode and is_interactive_mode"""
    # Initially REACTIVE
    assert coordinator.is_reactive_mode()
    assert not coordinator.is_interactive_mode()

    # Switch to INTERACTIVE manually
    coordinator.current_mode = UIMode.INTERACTIVE

    assert not coordinator.is_reactive_mode()
    assert coordinator.is_interactive_mode()


@pytest.mark.asyncio
async def test_global_singleton_init(event_bus, console):
    """Test global coordinator singleton"""
    reset_coordinator()

    # Initialize global
    coord1 = init_coordinator(event_bus, console)
    coord2 = init_coordinator(event_bus, console)  # Should replace

    # Both should be the same instance (second replaces first)
    from src.cli.ui_coordinator import get_coordinator
    global_coord = get_coordinator()

    assert global_coord is coord2
    assert global_coord is not coord1  # Replaced


@pytest.mark.asyncio
async def test_user_pause_does_not_change_mode(coordinator, event_bus):
    """Test USER_INPUT_PAUSED doesn't change mode"""
    initial_mode = coordinator.current_mode

    await event_bus.emit(Event(EventType.USER_INPUT_PAUSED))
    await asyncio.sleep(0.05)

    # Mode should remain the same
    assert coordinator.current_mode == initial_mode


@pytest.mark.asyncio
async def test_legacy_mode_ignores_permission_events(event_bus, console):
    """Test LEGACY mode ignores mode switching events"""
    coordinator = UICoordinator(event_bus, console, enable_reactive_ui=False)

    assert coordinator.current_mode == UIMode.LEGACY

    # Emit PERMISSION_REQUESTED
    await event_bus.emit(Event(EventType.PERMISSION_REQUESTED, tool_name="Bash"))
    await asyncio.sleep(0.05)

    # Should stay in LEGACY
    assert coordinator.current_mode == UIMode.LEGACY


@pytest.mark.asyncio
async def test_multiple_permission_requests_in_sequence(coordinator, event_bus):
    """Test multiple permission requests work correctly"""
    assert coordinator.current_mode == UIMode.REACTIVE

    # First permission request
    await event_bus.emit(Event(EventType.PERMISSION_REQUESTED, tool_name="Bash"))
    await asyncio.sleep(0.05)
    assert coordinator.current_mode == UIMode.INTERACTIVE

    # Resolve first
    await event_bus.emit(Event(EventType.PERMISSION_RESOLVED, tool_name="Bash"))
    await asyncio.sleep(0.05)
    assert coordinator.current_mode == UIMode.REACTIVE

    # Second permission request
    await event_bus.emit(Event(EventType.PERMISSION_REQUESTED, tool_name="Read"))
    await asyncio.sleep(0.05)
    assert coordinator.current_mode == UIMode.INTERACTIVE

    # Resolve second
    await event_bus.emit(Event(EventType.PERMISSION_RESOLVED, tool_name="Read"))
    await asyncio.sleep(0.05)
    assert coordinator.current_mode == UIMode.REACTIVE
