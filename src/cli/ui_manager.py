"""Reactive UI Manager for CLI"""

import asyncio
import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.status import Status
from rich.text import Text
from rich.style import Style

from src.events import EventBus, EventType, Event
from src.agents.state import AgentState


class InterfaceManager:
    """
    Manages the CLI interface in a reactive way based on events.
    State machine:
    IDLE -> THINKING (Spinner) -> USING_TOOL (Live Panel) -> THINKING ... -> IDLE

    Features:
    - Concurrency-safe with asyncio locks
    - Performance-optimized with throttled UI updates
    - Robust error handling for callbacks
    """

    def __init__(self, event_bus: EventBus, console: Console,
                 refresh_rate: float = 0.1):
        """
        Args:
            event_bus: Event bus for subscribing to events
            console: Rich Console instance
            refresh_rate: Minimum time between UI refreshes (seconds)
        """
        self.event_bus = event_bus
        self.console = console
        self.live_display: Live | None = None
        self.spinner: Status | None = None

        # Concurrency control
        self._ui_lock = asyncio.Lock()

        # Buffer for tool output
        self.current_tool_output = Text()
        self.current_tool_name = ""

        # Performance optimization: throttle UI updates
        self._refresh_rate = refresh_rate
        self._last_refresh_time = 0.0
        self._pending_chunks = []  # Buffer for chunks waiting to be rendered
        self._refresh_task = None

        # Subscribe to events
        self._subscribe_events()

    def _subscribe_events(self):
        """Subscribe to relevant events"""
        self.event_bus.subscribe(EventType.AGENT_STATE_CHANGED, self.handle_state_change)
        self.event_bus.subscribe(EventType.TOOL_SELECTED, self.handle_tool_selected)
        self.event_bus.subscribe(EventType.TOOL_OUTPUT_CHUNK, self.handle_tool_output)
        self.event_bus.subscribe(EventType.TOOL_COMPLETED, self.handle_tool_completed)
        self.event_bus.subscribe(EventType.TOOL_ERROR, self.handle_tool_error)
        self.event_bus.subscribe(EventType.USER_INPUT_PAUSED, self.handle_user_pause)

    async def _stop_all_visuals(self):
        """Stop any active visuals (spinner or live display)

        Thread-safe: Must be called within _ui_lock context
        """
        # Cancel any pending refresh task
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            self._refresh_task = None

        if self.spinner:
            self.spinner.stop()
            self.spinner = None

        if self.live_display:
            self.live_display.stop()
            self.live_display = None

        # Clear buffers
        self._pending_chunks.clear()
        self._last_refresh_time = 0.0

    async def handle_state_change(self, event: Event):
        """Handle agent state transitions (thread-safe)"""
        async with self._ui_lock:
            new_state = event.data.get('state')

            # We only react to major state changes to switch visual modes
            if new_state == AgentState.THINKING:
                await self._stop_all_visuals()
                self.spinner = self.console.status("Claude is thinking...", spinner="dots")
                self.spinner.start()

            elif new_state == AgentState.USING_TOOL:
                await self._stop_all_visuals()
                # We don't start Live display here immediately,
                # we wait for TOOL_SELECTED to know what tool it is.

            elif new_state == AgentState.IDLE or new_state == AgentState.COMPLETED or new_state == AgentState.ERROR:
                await self._stop_all_visuals()

    async def handle_tool_selected(self, event: Event):
        """Handle tool selection - Start the Live Display (thread-safe)"""
        async with self._ui_lock:
            # Ensure visuals are stopped before starting a new one
            await self._stop_all_visuals()

            self.current_tool_name = event.data.get('tool_name', 'Unknown Tool')
            brief_desc = event.data.get('brief_description', '')

            self.current_tool_output = Text("")

            title = f"Tool: {self.current_tool_name}"
            if brief_desc:
                title += f" ({brief_desc})"

            panel = Panel(
                self.current_tool_output,
                title=title,
                border_style="cyan",
                padding=(1, 2)
            )

            self.live_display = Live(panel, console=self.console, refresh_per_second=10)
            self.live_display.start()

            # Start background refresh task for throttled updates
            self._refresh_task = asyncio.create_task(self._background_refresh())

    async def handle_tool_output(self, event: Event):
        """Handle streaming output from tools (throttled for performance)"""
        chunk = event.data.get('chunk', '')
        if chunk:
            # Add to pending buffer (no lock needed for append)
            self._pending_chunks.append(chunk)

    async def _background_refresh(self):
        """Background task that throttles UI refreshes"""
        try:
            while self.live_display:
                await asyncio.sleep(self._refresh_rate)

                # Check if there are pending chunks
                if self._pending_chunks:
                    async with self._ui_lock:
                        if not self.live_display:  # Display might have been stopped
                            break

                        # Drain all pending chunks
                        chunks_to_render = self._pending_chunks[:]
                        self._pending_chunks.clear()

                        # Append all chunks to output
                        for chunk in chunks_to_render:
                            self.current_tool_output.append(chunk)

                        # Refresh display
                        self.live_display.refresh()
                        self._last_refresh_time = time.time()

        except asyncio.CancelledError:
            # Task was cancelled, cleanup
            pass
        except Exception as e:
            # Log error but don't crash
            import logging
            logging.getLogger(__name__).error(f"Error in background refresh: {e}")

    async def handle_tool_completed(self, event: Event):
        """Handle tool completion - update panel to success state (thread-safe)"""
        async with self._ui_lock:
            # Flush any remaining pending chunks
            if self._pending_chunks and self.live_display:
                for chunk in self._pending_chunks:
                    self.current_tool_output.append(chunk)
                self._pending_chunks.clear()

            if self.live_display:
                # Update panel style to indicate success
                panel = self.live_display.renderable
                if isinstance(panel, Panel):
                    panel.border_style = "green"
                    panel.title = f"✅ {panel.title}"
                self.live_display.refresh()
                # We don't stop it here, we wait for state change back to THINKING
                # or we could stop it.
                # Better to let handle_state_change(THINKING) stop it
                # so the user can see the final result for a split second
                # or until the agent starts thinking again.

    async def handle_tool_error(self, event: Event):
        """Handle tool error - update panel to error state (thread-safe)"""
        async with self._ui_lock:
            error = event.data.get('error', 'Unknown Error')

            # Flush any remaining pending chunks
            if self._pending_chunks and self.live_display:
                for chunk in self._pending_chunks:
                    self.current_tool_output.append(chunk)
                self._pending_chunks.clear()

            if self.live_display:
                self.current_tool_output.append(f"\n❌ Error: {error}", style="bold red")
                panel = self.live_display.renderable
                if isinstance(panel, Panel):
                    panel.border_style = "red"
                    panel.title = f"❌ {panel.title}"
                self.live_display.refresh()

    async def handle_user_pause(self, event: Event):
        """Handle user pressing ESC - clear visuals gracefully"""
        async with self._ui_lock:
            await self._stop_all_visuals()
            # Optionally show a message
            # self.console.print("⏸️  Input paused", style="yellow")

    # ========== Pause/Resume for UICoordinator ==========

    async def pause(self):
        """
        Pause UI for synchronous interaction (e.g., permission input)

        Workflow:
        1. Save current state (spinner/live_display/buffers)
        2. Stop all visuals
        3. Print static snapshot for user context

        This allows synchronous input() to work without Rich Live interference
        """
        async with self._ui_lock:
            if hasattr(self, '_paused') and self._paused:
                return  # Already paused

            # Save current state
            self._paused_state = {
                'spinner_active': self.spinner is not None,
                'live_active': self.live_display is not None,
                'tool_name': self.current_tool_name,
                'tool_output': Text.from_markup(str(self.current_tool_output)),  # Deep copy
                'pending_chunks': self._pending_chunks.copy()
            }

            # Stop all visuals
            await self._stop_all_visuals()

            # Mark as paused
            self._paused = True

            # 不再打印暂停提示 - Permission请求本身已经足够明显
            # 用户不需要知道UI内部的暂停/恢复机制

    async def resume(self):
        """
        Resume UI after synchronous interaction

        Workflow:
        1. Check if paused
        2. Restore spinner or live_display based on saved state
        3. Clear paused flag

        Note: If tool was running, it will continue from where it left off
        """
        async with self._ui_lock:
            if not hasattr(self, '_paused') or not self._paused:
                return  # Not paused

            # 不再打印恢复提示 - 保持UI简洁，用户不需要感知内部状态切换

            # Restore state
            if self._paused_state['live_active']:
                # Tool was running, restore Live Display
                self.current_tool_name = self._paused_state['tool_name']
                self.current_tool_output = self._paused_state['tool_output']
                self._pending_chunks = self._paused_state['pending_chunks']

                # Recreate panel
                panel = Panel(
                    self.current_tool_output,
                    title=f"Tool: {self.current_tool_name}",
                    border_style="cyan",
                    padding=(1, 2)
                )

                self.live_display = Live(panel, console=self.console, refresh_per_second=10)
                self.live_display.start()

                # Restart background refresh task
                self._refresh_task = asyncio.create_task(self._background_refresh())

            elif self._paused_state['spinner_active']:
                # Agent was thinking, restore spinner
                self.spinner = self.console.status("Claude is thinking...", spinner="dots")
                self.spinner.start()

            # Clear paused state
            self._paused = False
            self._paused_state = None
