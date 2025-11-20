# Hotfix: Comprehensive & Dynamic UI/UX Enhancement (V2 Final)

**Version**: `v2025.11.19`
**Hotfix ID**: `hf3-comprehensive-ux-revamp-v2`
**Author**: Gemini (Refined by Antigravity)

## 1. Overview

This document provides the **final, consolidated design** for a comprehensive hotfix to create a **dynamic, interactive, and polished user experience**. This V2 version integrates architectural improvements to ensure the UI remains decoupled from the Agent core logic by leveraging the **EventBus** system.

The revamp is built on three pillars:

1.  **A Welcoming Onboarding**: Introducing a welcome screen to properly greet and guide users.
2.  **Interactive Input Control**: Allowing users to pause input gracefully using the `ESC` key.
3.  **Dynamic, Streaming Feedback**: Transforming the application from a static request-response model to a real-time, streaming one, using an **Event-Driven Architecture**.

## 2. Current State Analysis

-   **Abrupt Start**: The application begins with a bare prompt.
-   **Lack of Input Control**: Users cannot interrupt or pause their input.
-   **Blocking Tool Execution**: The UI freezes during long-running tool operations.
-   **Coupling Risks**: Previous designs risked coupling the Agent logic directly to the CLI UI.

## 3. Detailed Design and Implementation

### Part A: The Welcome Experience

-   **Goal**: Greet the user with a helpful welcome message.
-   **Action**: Create a `display_welcome_message` method in `src/utils/output.py` and call it from `src/cli/main.py`.
-   **Code (`src/utils/output.py`)**:

    ```python
    from rich.panel import Panel
    from rich.text import Text

    class OutputFormatter:
        # ...
        def display_welcome_message(self, session_id: str):
            title = Text("Build Your Own Claude Code", style="bold magenta", justify="center")
            content = Text(f"Welcome! Session ID: {session_id}\nType '/help' for commands.", justify="center")
            self.console.print(Panel(content, title=title, border_style="magenta"))
    ```

-   **Code (`src/cli/main.py`)**:
    ```python
    # ... (inside main, after formatter is created)
    if output_formatter.level != OutputLevel.QUIET:
        output_formatter.display_welcome_message(session_id)
    ```

### Part B: Interactive Input Handling (ESC to Pause)

-   **Goal**: Allow users to silently pause input by pressing the `ESC` key.
-   **Action 1**: Create `src/cli/exceptions.py`.
    ```python
    class SessionPausedException(Exception):
        """Raised when the user pauses the session via the ESC key."""
        pass
    ```
-   **Action 2**: Modify `PromptInputManager` in `src/utils/input.py`.

    ```python
    from prompt_toolkit.key_binding import KeyBindings
    from src.cli.exceptions import SessionPausedException

    class PromptInputManager:
        # ...
        def _create_key_bindings(self):
            bindings = KeyBindings()
            @bindings.add('escape')
            def _(event):
                raise SessionPausedException
            return bindings
            
        def __init__(self, ...):
            # ...
            self.session = PromptSession(..., key_bindings=self._create_key_bindings())
    ```

-   **Action 3**: Handle exception in `src/cli/main.py`.
    ```python
    while True:
        try:
            user_input = await input_manager.async_get_input(...)
        except SessionPausedException:
            continue # Silently loop back
    ```

### Part C: Dynamic In-Session Feedback (Event-Driven)

-   **Goal**: Provide real-time feedback for tool output *without* coupling Agent to UI.
-   **Architecture**:
    1.  **Tool**: Emits output chunks via a callback.
    2.  **Agent**: Provides a callback that emits `TOOL_OUTPUT_CHUNK` events to the `EventBus`.
    3.  **CLI**: Listens to `EventBus` and updates `rich.Live` display.

#### Step 1: Define New Event
-   **File**: `src/events.py`
-   **Action**: Add `TOOL_OUTPUT_CHUNK` to `EventType`.

#### Step 2: Update Tool Interface
-   **File**: `src/tools/base.py` & `src/tools/bash.py`
-   **Action**: Update `execute` signature to accept `on_chunk`.

    ```python
    # src/tools/bash.py
    async def execute(self, command: str, on_chunk: Callable[[str], Awaitable[None]] = None, **kwargs) -> ToolResult:
        # ... setup process ...
        while True:
            line = await process.stdout.readline()
            if not line: break
            decoded_line = line.decode('utf-8')
            
            if on_chunk:
                await on_chunk(decoded_line)
            
            output += decoded_line
        # ...
    ```

#### Step 3: Update Agent & Tool Execution
-   **File**: `src/agents/enhanced_agent.py`
-   **Action**: Pass an event-emitting callback to tools.

    ```python
    # Inside _execute_tools method
    async def _emit_chunk(chunk: str):
        await self.event_bus.emit(Event(
            EventType.TOOL_OUTPUT_CHUNK,
            tool_id=tool_id,
            chunk=chunk
        ))

    # Pass this callback when executing tool
    result = await self.tool_manager.execute_tool(
        tool_name, 
        tool_input, 
        on_chunk=_emit_chunk
    )
    ```

#### Step 4: CLI Event Handler
-   **File**: `src/cli/ui_handler.py` (New File)
-   **Action**: Create a handler that subscribes to events and manages `rich.Live`.

    ```python
    from rich.live import Live
    from rich.panel import Panel
    from src.events import EventBus, EventType, Event

    class UIEventHandler:
        def __init__(self, event_bus: EventBus, console):
            self.console = console
            self.live = None
            self.current_panel_content = None
            
            # Subscribe to events
            event_bus.subscribe(EventType.TOOL_SELECTED, self.on_tool_start)
            event_bus.subscribe(EventType.TOOL_OUTPUT_CHUNK, self.on_tool_chunk)
            event_bus.subscribe(EventType.TOOL_COMPLETED, self.on_tool_end)
            event_bus.subscribe(EventType.TOOL_ERROR, self.on_tool_error)

        async def on_tool_start(self, event: Event):
            # Initialize Live display with Panel
            pass

        async def on_tool_chunk(self, event: Event):
            # Update content and refresh Live
            pass

        async def on_tool_end(self, event: Event):
            # Stop Live display
            pass
    ```

#### Step 5: Integrate into Main
-   **File**: `src/cli/main.py`
-   **Action**: Initialize `UIEventHandler`.

    ```python
    # ...
    event_bus = get_event_bus()
    ui_handler = UIEventHandler(event_bus, output_formatter.console)
    # ...
    await agent.run(user_input) 
    # No need to pass callback_manager to agent.run!
    ```

## 4. Verification Plan

### 4.1. Welcome & Pause
1.  **Verify Welcome**: Run `python -m src.main`. Check for welcome panel.
2.  **Verify ESC**: Press `ESC` during input. Check for silent reset.

### 4.2. Dynamic Feedback
1.  **Verify Streaming**: Run `bash` command: `for i in {1..3}; do echo $i; sleep 1; done`.
2.  **Observation**:
    -   "Tool Call" panel appears.
    -   Numbers 1, 2, 3 appear sequentially (streaming).
    -   Panel closes/updates on completion.
    -   **Crucial**: Ensure no errors in console regarding EventBus.

## 5. Summary of Benefits

-   **Superior UX**: Modern, responsive, professional feel.
-   **Decoupled Architecture**: UI logic stays in `src/cli/`, Agent logic stays in `src/agents/`.
-   **Extensibility**: Other interfaces (Web, API) can simply subscribe to `TOOL_OUTPUT_CHUNK` events to show real-time progress without modifying the Agent.
