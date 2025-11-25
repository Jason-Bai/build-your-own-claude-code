# Global ESC Monitor - Implementation Plan (V2)

> **Template Version**: 1.0
> **Created**: 2025-11-24
> **Status**: Draft

---

## 📚 Related Documents

**Design Document**: [docs/features/v0.0.1/p12-global-esc-monitor-design-document-v6.md](./p12-global-esc-monitor-design-document-v6.md)

---

## 1. Implementation Steps

### Phase 1: Foundation (Core Logic)

#### Step 1.1: CancellationToken & SessionManager Updates

**Priority**: P0
**Estimated Time**: 2 hours

- [ ] Task 1.1.1: Create `CancellationToken` class

  - Affected files: `src/utils/cancellation.py` (New)
  - Key logic: Thread-safe event handling, `raise_if_cancelled` method.

- [ ] Task 1.1.2: Update `SessionManager` to manage token
  - Affected files: `src/sessions/manager.py`
  - Key logic: Add `_cancellation_token`, `_execution_lock`, `start_new_execution()`, `cancel_all()`.

**Acceptance Criteria**:

- [ ] `CancellationToken` can be cancelled and `is_cancelled()` returns True.
- [ ] `raise_if_cancelled()` raises `asyncio.CancelledError` when cancelled.
- [ ] `SessionManager.start_new_execution()` creates a fresh, uncancelled token.
- [ ] `SessionManager.cancel_all()` cancels the current token.
- [ ] Thread safety verified via concurrent access tests.

---

#### Step 1.2: PromptInputManager State Tracking

**Priority**: P0
**Estimated Time**: 1 hour

- [ ] Task 1.2.1: Add `is_waiting_input` state
  - Affected files: `src/utils/input.py`
  - Key logic: Set flag to True before `prompt_async`, False in `finally` block.

**Acceptance Criteria**:

- [ ] `is_waiting_input` is True while `async_get_input` is awaiting user input.
- [ ] `is_waiting_input` is False after input is received or exception occurs.
- [ ] Verified via unit test mocking `prompt_async`.

---

#### Step 1.3: GlobalKeyboardMonitor Implementation

**Priority**: P0
**Estimated Time**: 3 hours

- [ ] Task 1.3.1: Create `GlobalKeyboardMonitor` class
  - Affected files: `src/cli/monitor.py` (New)
  - Key logic: `pynput` listener, `_on_press` handler, `_is_window_focused` check (macOS specific).

**Acceptance Criteria**:

- [ ] Monitor detects ESC key press globally.
- [ ] Monitor ignores ESC if `input_manager.is_waiting_input` is True.
- [ ] Monitor ignores ESC if window is not focused (on macOS).
- [ ] Monitor calls `session_manager.cancel_all()` when valid ESC detected.

---

### Phase 2: Executor Integration

#### Step 2.1: Tool Executor Updates

**Priority**: P0
**Estimated Time**: 4 hours

- [ ] Task 2.1.1: Define `SubprocessTool` base class

  - Affected files: `src/tools/base.py`
  - Key logic: Abstract methods for `start_async`, `is_running`, `kill`, `result`.

- [ ] Task 2.1.2: Update `AgentToolManager`
  - Affected files: `src/agents/tool_manager.py`
  - Key logic: Add `cancellation_token` support, polling loop for subprocess tools.

**Acceptance Criteria**:

- [ ] `AgentToolManager.execute_tool` accepts `cancellation_token`.
- [ ] Long-running `SubprocessTool` is killed if token is cancelled during execution.
- [ ] Async tools are cancelled if token is cancelled.
- [ ] `CancelledError` is raised upon cancellation.

---

#### Step 2.2: Client Updates (LLM & MCP)

**Priority**: P0
**Estimated Time**: 3 hours

- [ ] Task 2.2.1: Update `BaseClient` (LLM)

  - Affected files: `src/clients/base.py`
  - Key logic: Add `create_message_with_cancellation` wrapper.

- [ ] Task 2.2.2: Update `MCPClient`
  - Affected files: `src/mcps/client.py`
  - Key logic: Add `call_tool_with_cancellation` wrapper.

**Acceptance Criteria**:

- [ ] `create_message_with_cancellation` raises `CancelledError` if token cancelled while waiting.
- [ ] Underlying LLM API call task is cancelled.
- [ ] MCP tool calls can be cancelled via token.

---

#### Step 2.3: EnhancedAgent Integration

**Priority**: P0
**Estimated Time**: 2 hours

- [ ] Task 2.3.1: Update `EnhancedAgent.run`
  - Affected files: `src/agents/enhanced_agent.py`
  - Key logic: Accept `cancellation_token`, propagate to tools/LLM calls.

**Acceptance Criteria**:

- [ ] `EnhancedAgent.run` accepts `cancellation_token`.
- [ ] Token is passed to `_call_llm` and `_execute_tools`.
- [ ] Agent execution stops immediately upon `CancelledError`.

---

### Phase 3: Wiring & Logging

#### Step 3.1: Main Loop Integration

**Priority**: P0
**Estimated Time**: 2 hours

- [ ] Task 3.1.1: Initialize Monitor in `main.py`
  - Affected files: `src/cli/main.py`
  - Key logic: Start monitor, handle `asyncio.CancelledError`.

**Acceptance Criteria**:

- [ ] `GlobalKeyboardMonitor` is started on app launch.
- [ ] `asyncio.CancelledError` in main loop is caught.
- [ ] "Operation cancelled" message is displayed.
- [ ] Session is paused via `session_manager.pause_session_async`.

---

#### Step 3.2: Logging Updates

**Priority**: P0
**Estimated Time**: 1 hour

- [ ] Task 3.2.1: Add `EXECUTION_CANCELLED` ActionType
  - Affected files: `src/logging/types.py`
  - Key logic: Add enum member.

**Acceptance Criteria**:

- [ ] `ActionType.EXECUTION_CANCELLED` exists.
- [ ] Cancellation events are logged with this type.

---

## 2. File Checklist

### 2.1 New Files

- [ ] `src/utils/cancellation.py`

  - **Purpose**: Defines `CancellationToken` class.
  - **Key content**: Thread-safe cancellation logic.

- [ ] `src/cli/monitor.py`

  - **Purpose**: Global keyboard monitoring.
  - **Key content**: `GlobalKeyboardMonitor` class using `pynput`.

- [ ] `tests/unit/test_cancellation_token.py`
- [ ] `tests/unit/test_session_manager_cancellation.py`
- [ ] `tests/unit/test_input_manager_state.py`
- [ ] `tests/integration/test_llm_cancellation.py`
- [ ] `tests/integration/test_tool_cancellation.py`

### 2.2 Modified Files

- [ ] `src/sessions/manager.py`

  - **Changes**:
    - Add `_cancellation_token` and `_execution_lock` to `__init__` (Line ~20)
    - Add `start_new_execution()` method (Line ~25)
    - Add `cancel_all()` method (Line ~30)
    - Add `cancellation_token` property (Line ~35)
  - **Modification locations**:
    - Line 20: `__init__`
    - Line 24: Insert new methods

- [ ] `src/utils/input.py`

  - **Changes**:
    - Add `self._is_waiting_input = False` to `__init__` (Line ~110)
    - Add `is_waiting_input` property (Line ~112)
    - Update `async_get_input` to toggle state (Line ~247)
  - **Modification locations**:
    - Line 110: `__init__`
    - Line 247: `async_get_input`

- [ ] `src/tools/base.py`

  - **Changes**:
    - Add `SubprocessTool` base class definition.
  - **Modification locations**:
    - End of file.

- [ ] `src/agents/tool_manager.py`

  - **Changes**:
    - Update `execute_tool` signature to accept `cancellation_token` (Line ~50)
    - Add cancellation check logic (Line ~57)
  - **Modification locations**:
    - Line 50: `execute_tool`

- [ ] `src/clients/base.py`

  - **Changes**:
    - Add `create_message_with_cancellation` method to `BaseClient` (Line ~165)
  - **Modification locations**:
    - Line 165: `BaseClient`

- [ ] `src/mcps/client.py`

  - **Changes**:
    - Add `call_tool_with_cancellation` method.
  - **Modification locations**:
    - Add new method to `MCPClient` class.

- [ ] `src/agents/enhanced_agent.py`

  - **Changes**:
    - Update `run` signature to accept `cancellation_token` (Line ~116)
    - Pass token to `_call_llm` (Line ~254)
    - Pass token to `_execute_tools` (Line ~368)
  - **Modification locations**:
    - Line 116: `run`
    - Line 254: `_call_llm` call site (inside `run`)
    - Line 368: `_execute_tools` call site

- [ ] `src/cli/main.py`

  - **Changes**:
    - Initialize `GlobalKeyboardMonitor` (Line ~68)
    - Add `try...except asyncio.CancelledError` block in main loop (Line ~93)
  - **Modification locations**:
    - Line 68: Initialization
    - Line 93: Main loop

- [ ] `src/logging/types.py`
  - **Changes**:
    - Add `EXECUTION_CANCELLED` to `ActionType` (Line ~40)
  - **Modification locations**:
    - Line 40: `ActionType`

---

## 3. Core Logic Implementation

### 3.1 CancellationToken Class

```python
# src/utils/cancellation.py
import threading
import asyncio

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

### 3.2 SessionManager Updates

```python
# src/sessions/manager.py

class SessionManager:
    def __init__(self, ...):
        # ... existing init ...
        self._cancellation_token = CancellationToken()
        self._execution_lock = threading.Lock()  # Protects compound operations

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

### 3.3 GlobalKeyboardMonitor

```python
# src/cli/monitor.py
from pynput import keyboard
import threading

class GlobalKeyboardMonitor:
    def __init__(self, session_manager, input_manager):
        self.session_manager = session_manager
        self.input_manager = input_manager
        self._listener = None

    def start(self):
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def _on_press(self, key):
        if key == keyboard.Key.esc:
            # 1. Check if user is in input prompt
            if self.input_manager.is_waiting_input:
                return  # Let prompt_toolkit handle it

            # 2. Check if window is focused
            if self._is_window_focused():
                self.session_manager.cancel_all()

    def _is_window_focused(self) -> bool:
        try:
            from AppKit import NSWorkspace
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            return any(term in active_app.localizedName() for term in ['Terminal', 'iTerm', 'Code', 'Hyper'])
        except ImportError:
            return True  # Fallback
```

### 3.4 Tool Cancellation Logic

```python
# src/agents/tool_manager.py

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

        # ... Case B: Async Tools ...
```

### 3.5 MCP Client Cancellation Wrapper

```python
# src/mcps/client.py

    async def call_tool_with_cancellation(self, server_name, tool_name, arguments, cancellation_token=None):
        """Wrapper to support cancellation for MCP tool calls"""
        task = asyncio.create_task(self.call_tool(server_name, tool_name, arguments))

        try:
            # Wait for task, checking cancellation token periodically if needed
            # Or simply use asyncio.wait with return_when=FIRST_COMPLETED
            if cancellation_token:
                # Polling approach for granular control
                while not task.done():
                    if cancellation_token.is_cancelled():
                        task.cancel()
                        # Optional: Send interrupt notification to MCP server if supported
                        # await self._send_interrupt(server_name)
                        raise asyncio.CancelledError("MCP tool execution cancelled")
                    await asyncio.sleep(0.1)
                return await task
            else:
                return await task
        except asyncio.CancelledError:
            if not task.done():
                task.cancel()
            raise
```

---

## 4. Dependencies

### 4.1 New Dependencies

- **pynput** (v1.7.6+)

  - **Purpose**: Global keyboard event monitoring.
  - **Installation**: `pip install pynput`
  - **License**: LGPL

- **PyObjC** (macOS only, optional)
  - **Purpose**: Window focus detection via AppKit.
  - **Installation**: `pip install pyobjc-framework-Cocoa`
  - **Fallback**: Returns `True` if not available.

### 4.2 Existing Dependencies

- `threading` (stdlib)
- `asyncio` (stdlib)

---

## 5. Testing Strategy

### 5.1 Unit Tests

**File**: `tests/unit/test_cancellation_token.py`

- `test_token_initial_state`: Verify token is not cancelled initially.
- `test_token_cancel`: Verify `cancel()` sets state and reason.
- `test_raise_if_cancelled`: Verify raises `CancelledError`.
- `test_thread_safety`: Verify concurrent access (optional).

**File**: `tests/unit/test_session_manager_cancellation.py`

- `test_start_new_execution`: Verify new token creation.
- `test_cancel_all`: Verify token cancellation via manager.

**File**: `tests/unit/test_input_manager_state.py`

- `test_is_waiting_input_toggle`: Verify state changes during `async_get_input`.

**Coverage Target**: 80%+

### 5.2 Integration Tests

**File**: `tests/integration/test_llm_cancellation.py`

- `test_cancel_llm_call`: Mock slow LLM, trigger cancel, verify exception.

**File**: `tests/integration/test_tool_cancellation.py`

- `test_cancel_subprocess_tool`: Mock `SubprocessTool`, trigger cancel, verify `kill()` called.

### 5.3 Manual Verification

1.  **Input State**: Type text, press ESC. -> Expect input cleared, "Session Paused" message.
2.  **Thinking State**: Send complex query, press ESC while "Thinking...". -> Expect "Operation cancelled", return to prompt.
3.  **Tool State**: Send `bash: sleep 10`, press ESC. -> Expect tool killed, "Operation cancelled".
4.  **Background**: Focus another app, press ESC. -> Expect NO action in terminal.

---

## 6. Definition of Done

### 6.1 Functional Completion

- [ ] `CancellationToken` can be cancelled and checked.
- [ ] `SessionManager` creates new token per execution.
- [ ] `GlobalKeyboardMonitor` detects ESC globally.
- [ ] Input state prevents ESC during prompt.
- [ ] Window focus check works (macOS).
- [ ] Tools can be cancelled mid-execution.
- [ ] LLM calls can be cancelled.
- [ ] Session pauses on cancellation.

### 6.2 Testing Completion

- [ ] Unit tests: 10+ tests, 100% pass.
- [ ] Integration tests: 2+ tests, 100% pass.
- [ ] Code coverage ≥ 80%.
- [ ] Manual verification: 4/4 scenarios pass.

### 6.3 Code Quality

- [ ] `flake8` passes (0 errors).
- [ ] `mypy` type checking passes.
- [ ] All public APIs documented.

### 6.4 Documentation

- [ ] `README.md` updated (Features: "Global ESC Cancellation", Architecture: "Cancellation Flow").
- [ ] `README_zh.md` updated.
- [ ] Review document created after implementation.

---

## 7. Risks & Mitigation

| Risk                           | Impact               | Mitigation                                             |
| :----------------------------- | :------------------- | :----------------------------------------------------- |
| `pynput` permission issues     | High (Monitor fails) | Catch `PermissionError`, show helpful message to user. |
| Window focus check reliability | Medium               | Fallback to "always active" if check fails.            |
| Subprocess zombie states       | Medium               | Ensure `kill()` is robust.                             |

---

## 8. Progress Tracking

### 8.1 Overall Progress

- [ ] Phase 1: Foundation (0%)
- [ ] Phase 2: Executor Integration (0%)
- [ ] Phase 3: Wiring & Logging (0%)

### 8.2 Problems Encountered

| Problem    | Symptom | Cause | Solution |
| :--------- | :------ | :---- | :------- |
| (Template) |         |       |          |

---

## 9. Appendix

### Appendix A: Polling Interval Justification

We use a **0.1s (100ms)** polling interval for tool execution monitoring.

- **Responsiveness**: 100ms is below the typical human reaction time (~200ms), ensuring the system feels responsive to the ESC key.
- **Overhead**: 10 checks per second is negligible for CPU usage.
- **Balance**: A tighter loop (e.g., 10ms) would waste CPU, while a looser loop (e.g., 500ms) would make cancellation feel sluggish.

### Appendix B: Platform-Specific Window Focus

For macOS, we use `AppKit` to check the frontmost application.
For Linux/Windows, we currently fallback to `True` (always active) but can be extended using `python-xlib` (Linux) or `pywin32` (Windows) in the future.

### Appendix C: SubprocessTool Interface

The `SubprocessTool` abstract base class ensures all process-based tools implement standard lifecycle methods (`start_async`, `is_running`, `kill`, `result`), enabling uniform cancellation handling by the `AgentToolManager`.
