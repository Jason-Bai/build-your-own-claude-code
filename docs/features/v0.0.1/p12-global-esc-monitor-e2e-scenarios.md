# P12: Global ESC Monitor - E2E Test Scenarios

**Related Documents:**
- [Design Document](./p12-global-esc-monitor-design-document-v6.md)
- [Implementation Plan](./p12-global-esc-monitor-implement-plan-v2.md)

---

## Purpose

This document defines End-to-End test scenarios for the Global ESC Monitor feature. These scenarios simulate **real user behavior** to expose gaps between design assumptions and actual system behavior.

**Test-First Principle**: These scenarios are written BEFORE fixing current implementation issues. They are expected to FAIL initially, exposing real-world problems.

---

## Test Environment Prerequisites

### Required Permissions

| Platform | Permission | How to Verify |
|----------|-----------|---------------|
| macOS | Accessibility Access | System Settings → Privacy & Security → Accessibility |
| Linux | Input Device Access | Check `/dev/input` permissions |
| Windows | No special permission | N/A |

### Test Fixtures

- **Mock LLM Server**: Simulates slow API responses (controllable delay)
- **Mock Tool Execution**: Simulates long-running subprocess
- **Terminal Emulator**: Real terminal process (not simulated)

---

## Scenario 1: Permission Detection on Startup

**User Story**: As a user, I want to know if ESC cancellation is available when I start the CLI.

### 1.1 Startup WITHOUT Accessibility Permissions (macOS)

**Given**:
- Terminal NOT listed in Accessibility permissions
- User starts CLI: `python -m src.main`

**Expected Behavior**:
```
⚠️  GlobalKeyboardMonitor disabled: macOS Accessibility permissions required.
   To enable ESC cancellation, grant Terminal accessibility access in:
   System Preferences → Security & Privacy → Privacy → Accessibility

✨ Tiny Claude Code started (session: abc123)
👤 You: _
```

**Acceptance Criteria**:
- ✅ CLI starts successfully (no crash)
- ✅ Warning message displayed clearly
- ✅ User can still use CLI normally (just no ESC cancellation)
- ✅ Log contains permission error details

**Current Status**: ❓ UNKNOWN (needs testing)

---

### 1.2 Startup WITH Accessibility Permissions (macOS)

**Given**:
- Terminal IS listed in Accessibility permissions
- User starts CLI: `python -m src.main`

**Expected Behavior**:
```
✨ Tiny Claude Code started (session: abc123)
👤 You: _
```

**Acceptance Criteria**:
- ✅ CLI starts successfully
- ✅ NO warning message (permission granted)
- ✅ Log contains "GlobalKeyboardMonitor started"

**Current Status**: ❓ UNKNOWN (needs testing)

---

## Scenario 2: ESC During LLM Execution

**User Story**: As a user, I want to cancel a long-running LLM request by pressing ESC.

### 2.1 Cancel LLM Call with ESC (Happy Path)

**Given**:
- CLI running with valid permissions
- User sends: "帮我生成一个包含1000个函数的Python模块"
- LLM starts processing (simulated 10s delay)

**When**:
- User presses ESC after 2 seconds

**Expected Behavior**:
```
👤 You: 帮我生成一个包含1000个函数的Python模块
🤖 Thinking...

[User presses ESC]

⚠️  Execution cancelled by user (ESC pressed)

👤 You: _
```

**Acceptance Criteria**:
- ✅ Cancellation happens within 1 second of ESC press
- ✅ LLM HTTP request is aborted (via `task.cancel()`)
- ✅ "Execution cancelled" message displayed
- ✅ Session logged cancellation event
- ✅ CLI returns to input prompt (not crashed)

**Current Status**: ❌ FAILING (permission issue prevents ESC detection)

---

### 2.2 ESC with Terminal NOT Focused

**Given**:
- CLI running with permissions
- User sends: "执行长时间操作"
- User switches to browser (terminal loses focus)

**When**:
- User presses ESC (while browser is focused)

**Expected Behavior**:
- ❓ **Design Assumption**: ESC should be IGNORED (terminal not focused)
- ❓ **Reality Check**: Does `_is_window_focused()` correctly detect focus?

**Acceptance Criteria**:
- If `require_window_focus=True`:
  - ✅ ESC is ignored (operation continues)
  - ✅ Log: "ESC blocked: terminal not focused"
- If `require_window_focus=False`:
  - ✅ ESC triggers cancellation (operation stops)
  - ✅ Log: "ESC allowed: window focus check disabled"

**Current Status**: ❓ UNKNOWN (needs testing with different terminals)

---

### 2.3 Multiple ESC Presses (Idempotency)

**Given**:
- LLM call in progress

**When**:
- User presses ESC 3 times rapidly

**Expected Behavior**:
- First ESC: Triggers cancellation
- Second/Third ESC: Ignored (already cancelled)

**Acceptance Criteria**:
- ✅ No crash or duplicate cancellation errors
- ✅ Clean cancellation (no hanging tasks)
- ✅ Log shows only one cancellation event

**Current Status**: ❓ UNKNOWN (needs testing)

---

## Scenario 3: ESC During Tool Execution

**User Story**: As a user, I want to cancel a long-running tool/command by pressing ESC.

### 3.1 Cancel Subprocess Tool with ESC

**Given**:
- User triggers tool that spawns subprocess
- Example: `BashTool.execute("sleep 30")`

**When**:
- User presses ESC after 2 seconds

**Expected Behavior**:
```
🤖 Using tool: bash
   Command: sleep 30

[User presses ESC]

⚠️  Tool execution cancelled by user

👤 You: _
```

**Acceptance Criteria**:
- ✅ Subprocess is killed (via `process.kill()`)
- ✅ Tool returns `ToolResult(success=False, error="Cancelled")`
- ✅ No zombie processes left
- ✅ Agent catches cancellation and returns gracefully

**Current Status**: ❓ UNKNOWN (needs testing)

---

### 3.2 Cancel MCP Tool Call with ESC

**Given**:
- User triggers MCP tool
- Example: `filesystem.read_large_file`

**When**:
- User presses ESC during MCP call

**Expected Behavior**:
- MCP task cancelled (note: MCP protocol has no native interrupt mechanism)
- Agent receives `CancelledError`

**Acceptance Criteria**:
- ✅ MCP client task is cancelled
- ✅ Client cleans up connection state
- ✅ No hanging network requests

**Current Status**: ❓ UNKNOWN (needs testing)

---

## Scenario 4: ESC During Input Prompt

**User Story**: As a user, I want ESC to clear my input (not cancel execution) when I'm typing.

### 4.1 ESC While Typing Input

**Given**:
- CLI at input prompt
- User types: "帮我创建一个Flas"

**When**:
- User presses ESC (before hitting Enter)

**Expected Behavior**:
```
👤 You: 帮我创建一个Flas█

[User presses ESC]

👤 You: _
```

**Acceptance Criteria**:
- ✅ Input is cleared (prompt_toolkit default behavior)
- ✅ NO cancellation triggered
- ✅ Log shows "ESC blocked: user is in input prompt"
- ✅ `is_waiting_input` flag correctly set to `True`

**Current Status**: ✅ PASSING (based on design, needs verification)

---

## Scenario 5: Edge Cases

### 5.1 ESC Before First User Input

**Given**:
- CLI just started
- User at initial prompt (no execution running)

**When**:
- User presses ESC

**Expected Behavior**:
- No effect (nothing to cancel)
- Log: "ESC pressed but no execution running"

**Acceptance Criteria**:
- ✅ No crash
- ✅ No error message

**Current Status**: ❓ UNKNOWN

---

### 5.2 ESC After Execution Completes

**Given**:
- LLM call just finished
- Response displayed, back at prompt

**When**:
- User presses ESC immediately after

**Expected Behavior**:
- No effect (execution already done)

**Acceptance Criteria**:
- ✅ No cancellation event logged
- ✅ No error message

**Current Status**: ❓ UNKNOWN

---

### 5.3 Cancellation Token Reuse

**Given**:
- User cancels execution with ESC
- User immediately sends new query

**Expected Behavior**:
- New execution uses NEW `CancellationToken`
- Old cancelled token is discarded

**Acceptance Criteria**:
- ✅ New query executes normally
- ✅ `session_manager.start_new_execution()` creates fresh token
- ✅ No "already cancelled" errors

**Current Status**: ❓ UNKNOWN

---

## Scenario 6: Platform-Specific Behavior

### 6.1 Terminal Type Detection (macOS)

**Terminal Applications to Test**:
- Terminal.app (macOS default)
- iTerm2
- VS Code integrated terminal
- PyCharm terminal
- Alacritty
- kitty
- WezTerm

**Test**:
- Run CLI in each terminal
- Trigger LLM call
- Press ESC
- Verify: Is terminal name detected correctly by `_is_window_focused()`?

**Expected Behavior**:
- All common terminals should be recognized
- If unrecognized terminal, fallback to `True` (always allow ESC)

**Current Status**: ❌ PARTIAL (only a few terminals in hardcoded list)

---

### 6.2 Linux Support

**Given**:
- Running on Linux
- No AppKit available

**Expected Behavior**:
- `_is_window_focused()` returns `True` (fallback)
- ESC always works (no focus check)

**Current Status**: ❓ UNKNOWN (needs Linux testing)

---

### 6.3 Windows Support

**Given**:
- Running on Windows
- No AppKit available

**Expected Behavior**:
- `_is_window_focused()` returns `True` (fallback)
- ESC always works (no focus check)

**Current Status**: ❓ UNKNOWN (needs Windows testing)

---

## Test Execution Plan

### Phase 1: Permission Detection Tests
- [ ] Test 1.1: Startup without permissions
- [ ] Test 1.2: Startup with permissions

### Phase 2: Core Cancellation Tests
- [ ] Test 2.1: Cancel LLM call with ESC
- [ ] Test 2.2: ESC with terminal not focused
- [ ] Test 2.3: Multiple ESC presses

### Phase 3: Tool Cancellation Tests
- [ ] Test 3.1: Cancel subprocess tool
- [ ] Test 3.2: Cancel MCP tool

### Phase 4: Input Handling Tests
- [ ] Test 4.1: ESC while typing input

### Phase 5: Edge Case Tests
- [ ] Test 5.1: ESC before first input
- [ ] Test 5.2: ESC after execution completes
- [ ] Test 5.3: Cancellation token reuse

### Phase 6: Platform Tests
- [ ] Test 6.1: Terminal type detection (macOS)
- [ ] Test 6.2: Linux support
- [ ] Test 6.3: Windows support

---

## Known Issues (Pre-Testing)

Based on current debugging:

1. **Permission Issue**: pynput cannot detect keyboard events without Accessibility permissions
   - **Impact**: ALL ESC cancellation scenarios fail silently
   - **Fix Required**: Better permission detection and user guidance

2. **Window Focus Check**: Current implementation uses hardcoded terminal names
   - **Impact**: May not work with all terminal emulators
   - **Fix Required**: Expand terminal name list or make focus check optional

3. **asyncio.Event vs threading.Event**: Fixed in recent commit, but needs E2E verification
   - **Impact**: Cancellation response time
   - **Fix Required**: Already implemented, needs validation

---

## Success Metrics

**Definition of Done**:
- ✅ At least 80% of scenarios pass on macOS (with permissions)
- ✅ At least 60% of scenarios pass on Linux/Windows
- ✅ All "permission denied" cases handled gracefully (no crashes)
- ✅ Cancellation happens within 1 second of ESC press
- ✅ No zombie processes or hanging tasks after cancellation

**Current Pass Rate**: ~0% (permission issue blocks all tests)

**Target Pass Rate**: 100% after fixes
