# Global ESC Monitor Design V6 (Final Polish)

## 1. Overview

This document outlines the V6 design for the Global ESC Monitor. It builds upon the **Session-Centric** architecture of V5, adding final implementation details for thread safety, tool interfaces, and platform-specific window focus checks.

### Core Philosophy

1.  **Centralized Control**: The `SessionManager` is the single source of truth for execution state.
2.  **Cooperative Cancellation**: Components explicitly check for cancellation signals using a `CancellationToken`.
3.  **Unified Executor Interface**: All long-running operations (LLM calls, Tool execution) are wrapped in `Executor` classes that support cancellation.
4.  **Safe Interrupts**: Global key presses (ESC) trigger a thread-safe cancellation signal on the `SessionManager`.

---

## 2. Architecture

```mermaid
graph TD
    subgraph "Input Layer"
        A[GlobalKeyboardMonitor] -->|ESC Press| B{Context Check}
        B -->|Input Prompting| C[Ignore (Handled by prompt_toolkit)]
        B -->|Window Focused| D[SessionManager.cancel_all()]
    end

    subgraph "Core Logic"
        D -->|Trigger| E[CancellationToken]
        E -->|Propagate| F[Agent Executor]
        E -->|Propagate| G[Tool Executor]
    end

    subgraph "Execution Layer"
        F -->|Check Token| H[LLM Client]
        G -->|Check Token| I[Tool/MCP Process]
    end
```

---

## 3. Component Design

### 3.1 `CancellationToken`

A thread-safe token passed down the call stack.

```python
class CancellationToken:
    def __init__(self):
        self._cancelled = threading.Event()
        self._reason = ""

    def cancel(self, reason="User cancelled"):
        self._reason = reason
        self._cancelled.set()

    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    def raise_if_cancelled(self):
        if self.is_cancelled():
            raise asyncio.CancelledError(self._reason)
```

### 3.2 `SessionManager` Enhancements

The `SessionManager` acts as the central controller.

```python
class SessionManager:
    def __init__(self, ...):
        self._cancellation_token = CancellationToken()
        # Protects compound operations on execution state
        self._execution_lock = threading.Lock()

    def start_new_execution(self):
        """Called before starting a new user query"""
        with self._execution_lock:
            self._cancellation_token = CancellationToken()

    def cancel_all(self, reason="User cancelled"):
        """Called by Global Monitor"""
        with self._execution_lock:
            self._cancellation_token.cancel(reason)

    @property
    def cancellation_token(self):
        return self._cancellation_token
```

### 3.3 `PromptInputManager` State Tracking

To correctly identify when the user is typing (and thus ESC should be handled by `prompt_toolkit`), we must track the input state.

```python
# src/utils/input.py
class PromptInputManager:
    def __init__(self):
        self._is_waiting_input = False  # New state flag

    @property
    def is_waiting_input(self) -> bool:
        return self._is_waiting_input

    async def async_get_input(self, prompt: str = "👤 You: ", default: str = "") -> str:
        self._is_waiting_input = True  # ✅ Enter input state
        try:
            text = await self.session.prompt_async(...)
            return text.strip()
        finally:
            self._is_waiting_input = False  # ✅ Exit input state
```

### 3.4 `GlobalKeyboardMonitor` & Input Coordination

The monitor uses `is_waiting_input` to decide whether to act, and checks window focus.

```python
class GlobalKeyboardMonitor:
    def __init__(self, session_manager, input_manager):
        self.session_manager = session_manager
        self.input_manager = input_manager

    def _on_press(self, key):
        if key == keyboard.Key.esc:
            # 1. Check if user is in input prompt
            if self.input_manager.is_waiting_input:
                return  # Let prompt_toolkit handle it

            # 2. Check if window is focused
            if self._is_window_focused():
                self.session_manager.cancel_all()

    def _is_window_focused(self) -> bool:
        """
        Check if terminal window is focused.

        Platform-specific implementation:
        - macOS: Use AppKit to check frontmost app
        - Linux: Use xdotool or wmctrl to check active window
        - Windows: Use win32gui to check foreground window

        Note: If implementation is too complex, can default to True
        (always respond to ESC) as a simpler fallback.
        """
        try:
            # macOS example
            from AppKit import NSWorkspace
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            # Check for common terminal names
            return any(term in active_app.localizedName() for term in ['Terminal', 'iTerm', 'Code', 'Hyper'])
        except ImportError:
            # Fallback for other platforms or if dependency missing
            return True
```

### 3.5 Tool Executor Cancellation & `SubprocessTool`

We define a `SubprocessTool` base class to standardize process control.

```python
# src/tools/base.py
class SubprocessTool(BaseTool):
    """Base class for tools that run external processes"""

    async def start_async(self, params):
        """Start process and return handle"""
        raise NotImplementedError

    def is_running(self) -> bool:
        """Check if process is still running"""
        raise NotImplementedError

    def kill(self):
        """Forcefully terminate process"""
        raise NotImplementedError

    def result(self) -> "ToolResult":
        """
        Get process result after completion.

        Returns:
            ToolResult: Contains stdout, stderr, exit code

        Raises:
            RuntimeError: If process is still running
        """
        raise NotImplementedError
```

**Cancellation Logic:**

```python
# src/agents/tool_manager.py
class AgentToolManager:
    async def execute_tool(self, tool_name, params, cancellation_token=None):
        if cancellation_token:
            cancellation_token.raise_if_cancelled()

        tool = self.get_tool(tool_name)

        # Case A: Subprocess Tools
        if isinstance(tool, SubprocessTool):
            process = await tool.start_async(params)

            # Polling Interval Justification:
            # - 0.1s is fast enough for user experience (< 200ms reaction time)
            # - Low CPU overhead (10 checks/sec)
            while process.is_running():
                if cancellation_token and cancellation_token.is_cancelled():
                    process.kill()
                    raise asyncio.CancelledError("Tool execution cancelled")
                await asyncio.sleep(0.1)
            return process.result()

        # Case B: Async Tools
        else:
            task = asyncio.create_task(tool.execute(**params))
            while not task.done():
                if cancellation_token and cancellation_token.is_cancelled():
                    task.cancel()
                    raise asyncio.CancelledError("Tool execution cancelled")
                await asyncio.sleep(0.1)
            return await task
```

### 3.6 LLM Client Cancellation Strategy

```python
class BaseClient:
    async def create_message_with_cancellation(self, messages, tools=None, cancellation_token=None, **kwargs):
        task = asyncio.create_task(
            self.create_message(messages, tools, **kwargs)
        )

        while not task.done():
            if cancellation_token and cancellation_token.is_cancelled():
                task.cancel()
                raise asyncio.CancelledError(cancellation_token._reason)
            await asyncio.sleep(0.1)  # 100ms polling

        return await task
```

### 3.7 MCP Cancellation

MCP protocol support for interrupts is evolving. We implement a placeholder.

```python
# src/clients/mcp_client.py
class MCPClient:
    async def _send_interrupt(self, server_name, tool_name):
        """
        Send interrupt to MCP server if protocol supports it.

        Note: As of 2024, MCP protocol does not have standard interrupt mechanism.
        This is a placeholder for future protocol enhancements.
        """
        # TODO: Check if MCP v2.0 adds interrupt support
        pass

    async def call_tool_with_cancellation(self, server_name, tool_name, arguments, cancellation_token=None):
        task = asyncio.create_task(
            self.call_tool(server_name, tool_name, arguments)
        )

        while not task.done():
            if cancellation_token and cancellation_token.is_cancelled():
                task.cancel()
                try:
                    await self._send_interrupt(server_name, tool_name)
                except:
                    pass
                raise asyncio.CancelledError("MCP call cancelled")
            await asyncio.sleep(0.1)

        return await task
```

### 3.8 Logging Updates

We must ensure the `EXECUTION_CANCELLED` action type exists.

```python
# src/logging/types.py
class ActionType(str, Enum):
    # ... existing types ...
    EXECUTION_CANCELLED = "execution_cancelled"
```

---

## 4. Main Loop Integration

```python
async def main():
    # ... initialization ...
    monitor = GlobalKeyboardMonitor(session_manager, input_manager)
    monitor.start()

    while True:
        try:
            user_input = await input_manager.async_get_input()

            if user_input == "__SESSION_PAUSED__":
                await session_manager.pause_session_async(reason="user_input_paused")
                continue

            session_manager.start_new_execution()

            result = await agent.run(
                user_input,
                cancellation_token=session_manager.cancellation_token
            )

        except asyncio.CancelledError as e:
            OutputFormatter.warning(f"\n⚠️  Operation cancelled: {e}")

            action_logger.log(
                action_type=ActionType.EXECUTION_CANCELLED,
                session_id=session.session_id,
                reason=str(e)
            )

            await session_manager.pause_session_async(reason="execution_cancelled")
            continue

        except KeyboardInterrupt:
            OutputFormatter.info("Use /exit to quit properly")
            continue
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

- `tests/unit/test_cancellation_token.py`: Verify token state changes.
- `tests/unit/test_session_manager_cancellation.py`: Verify `cancel_all`.
- `tests/unit/test_input_manager_state.py`: Verify `is_waiting_input` toggles correctly.

### 5.2 Integration Tests

- `tests/integration/test_llm_cancellation.py`: Mock slow LLM, cancel via token.
- `tests/integration/test_tool_cancellation.py`: Mock `SubprocessTool`, verify `kill()` is called.

### 5.3 Manual Verification

1.  **Input State**: Type, press ESC -> Input cleared.
2.  **Thinking State**: Send query, press ESC -> Cancelled.
3.  **Tool State**: `bash: sleep 10`, press ESC -> Process killed.
4.  **Background**: Focus other app, press ESC -> Ignored.

---

## 6. Rollout Plan

1.  **Core**: Implement `CancellationToken`, update `SessionManager`, add `ActionType`.
2.  **Input**: Update `PromptInputManager` with `is_waiting_input`.
3.  **Executors**: Implement `SubprocessTool`, update `AgentToolManager`, `BaseClient`, `MCPClient`.
4.  **Monitor**: Implement `GlobalKeyboardMonitor` and integrate into `main.py`.
5.  **Verify**: Execute testing strategy.
