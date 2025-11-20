# Hotfix: Comprehensive UX Revamp (V3 Final)

**Version**: `v2025.11.20`
**Hotfix ID**: `hf3-comprehensive-ux-revamp-v3`
**Architecture**: Event-Driven Reactive UI
**Status**: Approved for Implementation

## 1. Overview

This is the definitive design for the UI/UX overhaul. It supersedes all previous drafts. The goal is to transform the CLI from a static request-response tool into a reactive, living application using an **Event-Driven Architecture**.

### Key Features
1.  **Reactive UI**: The UI updates in real-time based on internal system events (Thinking -> Tool Execution -> Streaming Output -> Completion).
2.  **Decoupled Architecture**: The `Agent` knows nothing about `rich` or the CLI. It only emits events.
3.  **Interactive Input**: Users can gracefully interrupt input using `ESC`.
4.  **Polished Onboarding**: A professional welcome screen.

## 2. Architecture Design

### 2.1. Event Schema (The Contract)

We will leverage the existing `EventBus`. We need to formalize the events to support the UI.

**File**: `src/events/types.py` (or `src/events/event_bus.py` depending on current structure)

New Event Types needed:
- `AGENT_STATE_CHANGED`: When agent switches between `IDLE`, `THINKING`, `USING_TOOL`.
- `TOOL_OUTPUT_CHUNK`: Real-time stdout/stderr from tools.

```python
# Conceptual Event Payload Structure
class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    USING_TOOL = "using_tool"

# Payload for TOOL_OUTPUT_CHUNK
{
    "tool_name": "bash",
    "chunk": "installing packages...\n"
}
```

### 2.2. The UI State Machine (`InterfaceManager`)

Instead of scattered `print` statements, a single class `InterfaceManager` in `src/cli/` will subscribe to the EventBus. It manages the exclusivity of UI elements (e.g., stopping the "Thinking" spinner before showing the "Tool Output" panel).

**Transitions:**
1.  **Input Submitted** -> Agent emits `THINKING` -> UI shows **Spinner**.
2.  **Agent decides to use tool** -> Agent emits `USING_TOOL` -> UI stops Spinner, starts **Live Panel**.
3.  **Tool runs** -> Tool emits `CHUNK` -> UI updates **Live Panel** content.
4.  **Tool finishes** -> Agent emits `THINKING` (analyzing result) -> UI stops Live Panel (leaves summary), restarts **Spinner**.
5.  **Agent finishes** -> Agent emits `IDLE` -> UI stops all active displays.

## 3. Detailed Implementation Steps

### Step 1: Core Event & Tool Enhancements

**Goal**: Enable tools to stream output and the Agent to broadcast it.

1.  **Modify `BaseTool.execute`**:
    Update the signature to accept an optional `on_chunk` callback. This keeps the Tool logic pure but allows streaming.

    ```python
    # src/tools/base.py
    class BaseTool(ABC):
        async def execute(self, input_data: Any, on_chunk: Callable[[str], Awaitable[None]] = None) -> ToolResult:
            ...
    ```

2.  **Implement Streaming in `BashTool`**:
    Use `asyncio.subprocess` to read stdout line-by-line.

    ```python
    # src/tools/bash.py
    async def execute(self, command: str, on_chunk: Callable = None, **kwargs):
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        # ... loop reading process.stdout ...
        # await on_chunk(decoded_line)
    ```

3.  **Update `EnhancedAgent`**:
    Inject a bridge callback when calling tools.

    ```python
    # src/agents/enhanced_agent.py
    
    # Define the bridge
    async def _stream_bridge(chunk: str):
        await self.event_bus.emit(Event(EventType.TOOL_OUTPUT_CHUNK, chunk=chunk, tool_name=tool_name))

    # Pass to tool
    await tool.execute(..., on_chunk=_stream_bridge)
    ```

### Step 2: Input Handling (The Pause Feature)

**Goal**: Allow `ESC` to interrupt input.

1.  **Create Exception**: `src/cli/exceptions.py` -> `class SessionPausedException(Exception): pass`.
2.  **Update `PromptInputManager`**: Add `escape` key binding in `src/utils/input.py`.
3.  **Update `main.py` loop**: Catch exception and `continue`.

### Step 3: The Reactive UI Manager

**Goal**: Centralize UI rendering logic.

**File**: `src/cli/ui_manager.py` (New)

```python
class InterfaceManager:
    def __init__(self, event_bus: EventBus, console: Console):
        self.console = console
        self.live_display = None
        self.spinner = None
        
        # Subscriptions
        event_bus.subscribe(EventType.AGENT_STATE_CHANGED, self.handle_state_change)
        event_bus.subscribe(EventType.TOOL_OUTPUT_CHUNK, self.handle_tool_output)
        # ... other events

    async def handle_state_change(self, event: Event):
        new_state = event.data['state']
        
        # Cleanup previous state visuals
        if self.spinner: self.spinner.stop()
        if self.live_display: self.live_display.stop()

        if new_state == AgentState.THINKING:
            self.spinner = self.console.status("Claude is thinking...")
            self.spinner.start()
        elif new_state == AgentState.USING_TOOL:
            # Initialize empty panel for streaming
            self.live_display = Live(Panel("Initializing..."), console=self.console)
            self.live_display.start()

    async def handle_tool_output(self, event: Event):
        if self.live_display:
            # Append text to the panel content and refresh
            self._update_panel(event.data['chunk'])
```

### Step 4: Main Entry Point Integration

**File**: `src/cli/main.py`

1.  Display Welcome Message (utilizing `src/utils/output.py`).
2.  Instantiate `InterfaceManager(event_bus, console)`.
3.  Remove the old `with console.status(...)` block since `InterfaceManager` handles it now.

## 4. Verification & Testing Strategy

### 4.1. Unit Tests
*   **Tools**: Mock `on_chunk` and verify `BashTool` calls it with partial output.
*   **UI Logic**: Since testing `rich.Live` is hard, verify the *Internal State* of `InterfaceManager`.
    *   *Test*: Emit `AGENT_STATE_CHANGED(THINKING)` -> Assert `manager.current_mode == 'spinner'`.
    *   *Test*: Emit `TOOL_OUTPUT_CHUNK` -> Assert `manager.buffer` contains the text.

### 4.2. Integration Tests
*   **Event Flow**: Trigger an agent action that uses a tool. Verify that `TOOL_OUTPUT_CHUNK` events appear in the EventBus logs.

### 4.3. Manual UX Checklist
1.  [ ] Run app -> See Welcome Panel?
2.  [ ] Type `sleep 5` (simulated bash) -> See Spinner stop? See "Tool Execution" panel appear?
3.  [ ] Type long text -> Press ESC -> Does it clear line and reset prompt?

## 5. Why this is the "Robust" version

1.  **Concurrency Safe**: By using `rich.Live` exclusively within the `InterfaceManager`, we avoid race conditions where multiple parts of the app try to write to stdout simultaneously.
2.  **Extensible**: Adding a Web Interface later just means adding a `WebInterfaceManager` that listens to the same events and pushes via WebSocket. No Agent code changes required.
3.  **Observability**: Every UI action is triggered by an Event, meaning we can log these events to debug exactly *why* the UI showed a specific state.
