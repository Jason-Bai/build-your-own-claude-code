# P11 - Structured Action Logging System

## 1. Functional Overview

### 1.1 Problem Statement

**Real-world Scenarios:**

- ❌ **Data Loss on Ctrl+C** - When a user presses Ctrl+C twice, the Session system has not yet persisted data, causing the loss of all ongoing conversations, tool calls, and execution history.
- ❌ **Crash Traceability** - After an abnormal program exit, it is impossible to know what happened before the crash.
- ❌ **Difficult Debugging** - Terminal errors cannot be viewed once they scroll past or the window is closed.
- ❌ **No Audit Trail** - In production environments, there is no way to trace "who executed what operation and when".
- ❌ **Limited Performance Analysis** - Lack of historical data to support trend analysis.

**Solution:**
A real-time structured logging system that immediately persists all user interactions, LLM calls, tool executions, etc., to disk. It uses JSON Lines format, split by day, and provides a dedicated query tool.

**Key Benefits:**

- ✅ **Real-time Persistence** - Every action is written to disk immediately; no data loss even on Ctrl+C.
- ✅ **Crash Recovery** - Full context before a crash can be traced.
- ✅ **Audit Trail** - Complete operation history record.
- ✅ **Debugging Support** - Historical errors and warnings can be viewed at any time.
- ✅ **Performance Analysis** - Historical data supports trend analysis.
- ✅ **Compliance** - Meets security audit requirements.

---

## 2. Architecture Design

### 2.1 Log File Structure

```
~/.tiny-claude-code/logs/
├── 2025-11-21.jsonl        # Today's logs (hot data, real-time write)
├── 2025-11-20.jsonl        # Yesterday's logs
├── 2025-11-19.jsonl.gz     # Compressed old logs (auto-compressed after 7 days)
└── metadata.json           # Log metadata (file index, statistics)
```

### 2.2 System Integration Architecture

```mermaid
graph TD
    SessionManager --> ActionLogger
    EnhancedAgent --> ActionLogger
    ToolExecutor --> ActionLogger
    LLMClients --> ActionLogger
    EventBus --> ActionLogger
    CLIMain --> ActionLogger

    subgraph Logging System
        ActionLogger[ActionLogger (async queue)] --> LogWriter[LogWriter (background)]
        LogWriter --> Files[Real-time JSONL Files]
    end
```

**Integration Points:**

1. **SessionManager** - Records session lifecycle (start/end/pause/resume).
2. **EnhancedAgent** - Records state changes (IDLE → THINKING → USING_TOOL).
3. **ToolExecutor** - Records tool calls (arguments, results, errors).
4. **LLM Clients** - Records requests/responses (with data masking).
5. **EventBus** - Records system events.
6. **CLI Main** - Records user input/commands.

### 2.3 Async Logging Pipeline (Solving Ctrl+C Issue)

**Architecture Components:**

`QueueHandler (sync) → Queue → Background Thread (async) → File Writer`

**Ctrl+C Safety Design:**

```python
# Register signal handler
def signal_handler(sig, frame):
    logger.info("Received interrupt signal, flushing logs...")
    action_logger.flush()  # Force flush all logs in queue
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
```

**Performance Optimization:**

- Caller uses `logger.info()` which returns immediately (no I/O blocking).
- Logs enter an in-memory queue (default size: 1000 entries).
- Background thread batch writes to disk (default 100 entries/batch or 1 second/batch, whichever comes first).
- On Ctrl+C, the queue is forcibly flushed to ensure no data loss.
- Expected performance impact: < 1ms per action.

---

## 3. JSON Schema Definition

### 3.1 Common Fields (Shared by all logs)

```json
{
  "timestamp": "2025-11-21T14:32:15.123456",
  "action_number": 1234,
  "action_type": "tool_call",
  "session_id": "session-20251121143210-123456",
  "execution_id": "exec-abc123",
  "status": "success"
}
```

### 3.2 User Interaction

**USER_INPUT**

```json
{
  "action_type": "user_input",
  "content": "Help me implement a login function",
  "input_mode": "interactive"
}
```

**USER_COMMAND**

```json
{
  "action_type": "user_command",
  "command": "/status",
  "args": []
}
```

### 3.3 Agent State

**AGENT_STATE_CHANGE**

```json
{
  "action_type": "agent_state_change",
  "from_state": "IDLE",
  "to_state": "THINKING",
  "reason": "user_request"
}
```

**AGENT_THINKING**

```json
{
  "action_type": "agent_thinking",
  "thinking_content": "[MASKED]",
  "duration_ms": 1234
}
```

### 3.4 LLM Interaction

**LLM_REQUEST**

```json
{
  "action_type": "llm_request",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "messages_count": 5,
  "tools_count": 8,
  "temperature": 0.7,
  "max_tokens": 4000,
  "request_id": "req-xyz789"
}
```

**LLM_RESPONSE**

```json
{
  "action_type": "llm_response",
  "request_id": "req-xyz789",
  "response_type": "tool_use",
  "tool_calls": [{ "tool": "read_file", "tool_use_id": "toolu_abc123" }],
  "input_tokens": 1234,
  "output_tokens": 567,
  "duration_ms": 2345,
  "status": "success"
}
```

**LLM_ERROR**

```json
{
  "action_type": "llm_error",
  "request_id": "req-xyz789",
  "error_type": "rate_limit_error",
  "error_message": "Rate limit exceeded",
  "retry_after": 60
}
```

### 3.5 Tool Execution

**TOOL_CALL**

```json
{
  "action_type": "tool_call",
  "tool_name": "bash",
  "tool_use_id": "toolu_abc123",
  "args": {
    "command": "ls -la",
    "description": "List files"
  },
  "permission_level": "NORMAL"
}
```

**TOOL_RESULT**

```json
{
  "action_type": "tool_result",
  "tool_use_id": "toolu_abc123",
  "success": true,
  "output": "[TRUNCATED 1000 chars]",
  "duration_ms": 123,
  "status": "success"
}
```

**TOOL_ERROR**

```json
{
  "action_type": "tool_error",
  "tool_use_id": "toolu_abc123",
  "error_type": "execution_error",
  "error_message": "Command not found: xyz",
  "status": "error"
}
```

**TOOL_PERMISSION**

```json
{
  "action_type": "tool_permission",
  "tool_use_id": "toolu_abc123",
  "permission_level": "DANGEROUS",
  "user_decision": "approved",
  "decision_time_ms": 5678
}
```

### 3.6 Session Lifecycle

**SESSION_START/END/PAUSE/RESUME**

```json
{
  "action_type": "session_start",
  "project_name": "my-project",
  "session_id": "session-20251121143210-123456",
  "metadata": {
    "python_version": "3.10.12",
    "platform": "darwin"
  }
}
```

### 3.7 Hook Execution

**HOOK_EXECUTE**

```json
{
  "action_type": "hook_execute",
  "hook_name": "on_tool_execute",
  "hook_type": "command",
  "duration_ms": 45,
  "status": "success"
}
```

### 3.8 System Events

**SYSTEM_ERROR/SYSTEM_WARNING**

```json
{
  "action_type": "system_error",
  "component": "mcp_server",
  "error_message": "Failed to connect to filesystem server",
  "traceback": "[MASKED]",
  "status": "error"
}
```

---

## 4. Privacy and Security Design

### 4.1 Data Masking Rules

**Automatically Masked Sensitive Data:**

1. **API Keys** - Pattern: `sk-[a-zA-Z0-9]{48}`, `Bearer xxx`
2. **Passwords** - Field names: `password`, `passwd`, `secret`, `token`
3. **Personal Info** - Email, Phone Number (optional, via regex)
4. **File Paths** - User directory paths (e.g., `/Users/baiyu/` → `/Users/[USER]/`)

**Masking Method:**

```json
"api_key": "sk-ant-api03-abc...xyz" → "api_key": "sk-**_[MASKED 44 chars]_**"
"password": "secret123" → "password": "[MASKED]"
```

### 4.2 Configurable Sensitive Fields

```json
// settings.json
{
  "logging": {
    "mask_sensitive_data": true,
    "custom_sensitive_fields": ["internal_token", "ssh_key"],
    "mask_thinking": true,
    "truncate_large_output": true,
    "max_output_chars": 1000
  }
}
```

### 4.3 Privacy Mode

**Completely Disable Logging:**

```json
{
  "logging": {
    "enabled": false
  }
}
```

---

## 5. Disk Management Design

### 5.1 Retention Policy

**Default Policy:**

- **Time Retention**: 30 days (configurable)
- **Space Limit**: 1GB total size (configurable)
- **Trigger Condition**: Triggered when any condition is met

```json
// settings.json
{
  "logging": {
    "retention_days": 30,
    "max_total_size_mb": 1024,
    "cleanup_on_startup": true
  }
}
```

### 5.2 Auto Cleanup Mechanism

**Cleanup Logic:**

1. Scan `logs/` directory.
2. Sort all `.jsonl` and `.jsonl.gz` files by time.
3. Delete files older than `retention_days`.
4. If total size still exceeds `max_total_size_mb`, delete oldest files until limit is met.

### 5.3 Log Compression (Optional)

**Auto-compress logs older than 7 days:**

`2025-11-14.jsonl` → `2025-11-14.jsonl.gz`

**Compression Ratio**: Typically 5:1 to 10:1

---

## 6. Query Tool Design

### 6.1 Command Line Tool: `/log`

**Command Format:**

```bash
# Basic query (view today's logs)
/log

# Specific date
/log --date 2025-11-21
/log --date-range 2025-11-15:2025-11-21

# Filter by type
/log --action-type tool_call
/log --action-type llm_request,llm_response

# Filter by session
/log --session-id session-20251121143210-123456

# Filter by status
/log --status error
/log --status success --tool-name bash

# Keyword search
/log --keyword "authentication"
/log --content-match "Failed to connect"

# Output format
/log --format json      # JSON array
/log --format table     # Table (default)
/log --format summary   # Statistical summary

# Limit results
/log --limit 50
/log --tail 20          # Last 20 entries

# Combination example
/log --date 2025-11-21 --action-type tool_error --tool-name bash --format table
```

### 6.2 Query Tool Output Example

**Table Format (Default):**

```
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Timestamp    ┃ Action Type   ┃ Tool       ┃ Status  ┃ Message            ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ 14:32:15.123 │ tool_error    │ bash       │ error   │ Command not found  │
│ 14:35:22.456 │ tool_call     │ read_file  │ success │ Read config.json   │
└──────────────┴───────────────┴────────────┴─────────┴────────────────────┘

Showing 2 of 1,234 total actions
```

**Statistical Summary Format:**

```
=== Log Statistics Summary (2025-11-21) ===

Total Actions: 1,234
Sessions: 3
Errors: 12

Distribution by Type:
- tool_call: 456 (37%)
- llm_request: 234 (19%)
- user_input: 123 (10%)
- agent_state_change: 421 (34%)

Distribution by Status:
- success: 1,222 (99%)
- error: 12 (1%)

Error Types:
- tool_error: 8
- llm_error: 3
- system_error: 1

Disk Usage:
- Today's Log Size: 2.3 MB
- Total Log Size: 45.6 MB (30 days)
```

### 6.3 Programmatic API (Internal Use)

```python
from src.logging import LogQueryEngine

# Python API
query = LogQueryEngine()
results = query.filter(
    date_range=("2025-11-20", "2025-11-21"),
    action_types=["tool_call", "tool_error"],
    session_id="session-20251121143210-123456",
    status="error"
).limit(100).execute()

# Returns: List[Dict[str, Any]]
for record in results:
    print(record['timestamp'], record['action_type'], record['status'])
```

---

## 7. Configuration Design

### 7.1 New User Default Configuration (`templates/settings.json`)

**File Path:** `templates/settings.json`

```json
{
  "model": {
    "provider": "anthropic",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "providers": {
    // ... (omitted)
  },
  "mcp_servers": [],
  "hooks": [],
  "logging": {
    "enabled": true,
    "log_dir": "~/.tiny-claude-code/logs",

    "async_logging": true,
    "queue_size": 1000,
    "batch_size": 100,
    "batch_timeout_sec": 1,

    "mask_sensitive_data": true,
    "custom_sensitive_fields": [],
    "mask_thinking": false,
    "truncate_large_output": true,
    "max_output_chars": 1000,

    "retention_days": 30,
    "max_total_size_mb": 1024,
    "cleanup_on_startup": true,
    "compress_after_days": 7,

    "action_types": {
      "user_input": true,
      "user_command": true,
      "agent_state_change": true,
      "agent_thinking": false,
      "llm_request": true,
      "llm_response": true,
      "llm_error": true,
      "tool_call": true,
      "tool_result": true,
      "tool_error": true,
      "tool_permission": true,
      "session_start": true,
      "session_end": true,
      "session_pause": true,
      "session_resume": true,
      "hook_execute": false,
      "hook_error": true,
      "system_error": true,
      "system_warning": true
    }
  }
}
```

**Key Defaults Explanation:**

- `enabled: true` - Logging enabled by default (user can disable).
- `async_logging: true` - Use async logging to avoid performance impact.
- `mask_sensitive_data: true` - Enable data masking by default for privacy.
- `mask_thinking: false` - Do not mask agent thinking by default (for debugging).
- `agent_thinking: false` - Do not log thinking content by default (reduce log volume).
- `hook_execute: false` - Do not log hook execution by default (reduce noise).
- `retention_days: 30` - Retain logs for 30 days.
- `max_total_size_mb: 1024` - Max 1GB disk usage.

### 7.2 User Configuration Example (`~/.tiny-claude-code/settings.json`)

**Full Configuration (Documentation Example):**

```json
{
  "logging": {
    "enabled": true,
    "log_dir": "~/.tiny-claude-code/logs"
    // ... (same as above)
  }
}
```

**Minimal Configuration (Just Enable):**

```json
{
  "logging": {
    "enabled": true
  }
}
```

**Disable Logging:**

```json
{
  "logging": {
    "enabled": false
  }
}
```

### 7.3 Configuration Fields Detail

| Config Item             | Type   | Default                  | Description                          |
| :---------------------- | :----- | :----------------------- | :----------------------------------- |
| enabled                 | bool   | true                     | Enable logging system                |
| log_dir                 | string | ~/.tiny-claude-code/logs | Log file storage directory           |
| async_logging           | bool   | true                     | Use async logging (recommended)      |
| queue_size              | int    | 1000                     | Async queue size                     |
| batch_size              | int    | 100                      | Batch write size (100 entries/batch) |
| batch_timeout_sec       | float  | 1.0                      | Batch write timeout (1 sec/batch)    |
| mask_sensitive_data     | bool   | true                     | Mask sensitive data                  |
| custom_sensitive_fields | list   | []                       | List of custom sensitive field names |
| mask_thinking           | bool   | false                    | Mask agent thinking content          |
| truncate_large_output   | bool   | true                     | Truncate large output                |
| max_output_chars        | int    | 1000                     | Max characters for output            |
| retention_days          | int    | 30                       | Log retention days                   |
| max_total_size_mb       | int    | 1024                     | Total log size limit (MB)            |
| cleanup_on_startup      | bool   | true                     | Auto cleanup old logs on startup     |
| compress_after_days     | int    | 7                        | Auto compress logs after N days      |
| action_types.\*         | bool   | varies                   | Switches for various action types    |

---

## 8. Implementation Phases

### Phase 1: MVP (Core Features)

**Duration:** 3 days

**Features:**

- ✅ Basic `ActionLogger` class (async version, QueueHandler + background thread)
- ✅ JSON Lines writer (with Ctrl+C signal handling)
- ✅ Daily rotation logic
- ✅ Core action types (10 types):
  - USER_INPUT, USER_COMMAND
  - AGENT_STATE_CHANGE
  - LLM_REQUEST, LLM_RESPONSE
  - TOOL_CALL, TOOL_RESULT, TOOL_ERROR
  - SESSION_START, SESSION_END
- ✅ Integration into SessionManager, EnhancedAgent, ToolExecutor
- ✅ Basic data masking (API keys, password fields)
- ✅ Update configuration template (`templates/settings.json`)

**Testing:**

- Unit tests: Log writing, date rotation, data masking, Ctrl+C handling
- Integration tests: Full flow log recording, forced exit data integrity

### Phase 2: Enhanced Features

**Duration:** 2 days

**Features:**

- ✅ Complete action types (19 types)
- ✅ Advanced data masking (regex matching, custom fields)
- ✅ Disk management (retention policy, auto cleanup)
- ✅ Basic query tool (`/log` command, support basic filtering)

**Testing:**

- Performance tests: Async logging throughput
- Stress tests: High volume log writing

### Phase 3: Production Ready

**Duration:** 2 days

**Features:**

- ✅ Log compression (auto compress old logs)
- ✅ Complete query tool (all filter conditions, output formats)
- ✅ Programmatic API (`LogQueryEngine`)
- ✅ Configuration validation and default value handling
- ✅ Monitoring and alerting (log write failure alerts)

**Testing:**

- E2E tests: Complete user scenarios
- Boundary tests: Disk full, permission errors, configuration errors

---

## 9. Relationship with Session System

### 9.1 Complementary Architecture (Not Replacement)

| Aspect           | Session System                               | Logging System                                                              |
| :--------------- | :------------------------------------------- | :-------------------------------------------------------------------------- |
| Purpose          | State recovery, session management           | Audit trail, debugging analysis, crash protection                           |
| Write Timing     | Batch save at session end                    | Real-time write for every action                                            |
| Ctrl+C Behavior  | ❌ Data loss                                 | ✅ Data safe (signal handler forces flush)                                  |
| Storage Format   | Python object serialization (pickle/json)    | JSON Lines (row-based)                                                      |
| Query Method     | Load entire session object                   | Row-based filtering, aggregation statistics                                 |
| Typical Use Case | Restore interrupted session, switch sessions | View lost content after Ctrl+C, crash troubleshooting, performance analysis |

### 9.2 Data Flow Relationship

```
User Action
    │
    ├──► ActionLogger.log() ──► Queue ──► Background Thread ──► JSONL File (Real-time)
    │                                           ↑
    │                                     Force flush on Ctrl+C
    │
    └──► Session.record_xxx() ──► Session Object (Memory)
                                        │
                                        └──► PersistenceManager (At session end)
```

### 9.3 No Disruption to Existing Architecture

- ✅ **Zero Intrusion**: Integrated via event hooks, no modification to core logic.
- ✅ **Optional Feature**: Disabling logging via config does not affect Session system.
- ✅ **Independent Storage**: Log files and Session files are completely separated.

---

## 10. Test Strategy

### 10.1 Unit Tests

`tests/unit/test_action_logger.py`

- `test_log_writing()`
- `test_date_rotation()`
- `test_data_masking()`
- `test_json_schema_validation()`
- `test_ctrl_c_signal_handling()` # New: Test Ctrl+C safety
- `test_queue_flush()` # New: Test queue flush

`tests/unit/test_log_query.py`

- `test_date_filter()`
- `test_action_type_filter()`
- `test_status_filter()`

### 10.2 Integration Tests

`tests/integration/test_logging_integration.py`

- `test_full_session_logging()`
- `test_tool_execution_logging()`
- `test_llm_interaction_logging()`
- `test_error_logging()`
- `test_force_exit_data_integrity()` # New: Test forced exit data integrity

### 10.3 Performance Tests

`tests/performance/test_logging_performance.py`

- `test_async_logging_overhead()` # < 1ms/action
- `test_async_logging_throughput()` # > 1000 actions/sec
- `test_disk_usage()` # Compression ratio verification

---

## 11. Potential Risks and Mitigation

### 11.1 Basic Risk List

| Risk                 | Impact | Mitigation                                                     |
| :------------------- | :----- | :------------------------------------------------------------- |
| Ctrl+C Data Loss     | High   | ✅ Signal handler forces queue flush                           |
| Log File Too Large   | High   | ✅ Auto cleanup, compression, configurable retention policy    |
| Sensitive Data Leak  | High   | ✅ Default masking, configurable masking rules, privacy mode   |
| Performance Overhead | Medium | ✅ Async logging, batch writing, configurable detailed logging |
