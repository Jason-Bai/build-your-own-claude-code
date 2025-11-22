P11 Structured Action Logging System - Design Document: ./p11-structured-action-logging-design-document.md

---

# P11 Structured Action Logging System - Implementation Plan

## 📋 Implementation Overview

**Total Duration**: 7 working days (3 days + 2 days + 2 days)
**Implementation Mode**: Progressive development in three phases
**Key Milestones**: MVP → Enhanced → Production Ready

---

## Phase 1: MVP (Core Features) - 3 Working Days

### Objectives

Validate core value: Real-time log persistence + Ctrl+C safety + Basic queries

### Task Breakdown

#### Day 1: Logging Infrastructure (6-8 hours)

**1.1 Create Logging Module Structure**

```
src/logging/
├── __init__.py
├── action_logger.py    # Core logger
├── log_writer.py       # File writer
├── types.py            # Data type definitions
└── constants.py        # Constants (action types, etc.)
```

**1.2 Implement ActionLogger Class**

- ✅ Asynchronous queue (QueueHandler)
- ✅ Background thread (background worker)
- ✅ Health check mechanism (❗ High priority, 11.2.2)
  - Heartbeat detection
  - Auto-restart
  - Fallback to synchronous mode
- ✅ Ctrl+C signal handler (SIGINT)
- ✅ `flush()` method (force flush queue)

Key code framework:

```python
# src/logging/action_logger.py

class ActionLogger:
    def __init__(self, config: LoggingConfig):
        self._queue = Queue(maxsize=config.queue_size)
        self._worker_thread = None
        self._last_heartbeat = time.time()
        self._running = True
        self._start_worker()
        self._register_signal_handlers()

    def log(self, action_type: str, **data):
        """Log action (asynchronous)"""
        if not self._is_worker_healthy():
            self._handle_unhealthy_worker()

        action_data = self._build_action_data(action_type, **data)
        try:
            self._queue.put_nowait(action_data)
        except queue.Full:
            # Phase 1: Simple drop strategy
            logger.warning("Log queue full, dropping log")

    def _worker(self):
        """Background thread: Batch write logs"""
        try:
            while self._running:
                batch = self._collect_batch()  # 100 entries or 1 second timeout
                if batch:
                    self._writer.write_batch(batch)
                self._last_heartbeat = time.time()
        except Exception as e:
            logger.error(f"Worker crashed: {e}")
            self._worker_alive = False

    def _is_worker_healthy(self) -> bool:
        """Health check (11.2.2 high-risk item)"""
        if not self._worker_thread.is_alive():
            return False
        if time.time() - self._last_heartbeat > 10:
            return False
        return True
```

**1.3 Implement LogWriter Class**

- ✅ JSON Lines format writing
- ✅ Date-based splitting (YYYY-MM-DD.jsonl)
- ✅ Batch write optimization (reduce I/O)
- ✅ File handle management (open/close/rotation)

**1.4 Define Data Types**

```python
# src/logging/types.py

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ActionData:
    timestamp: str
    action_number: int
    action_type: str
    session_id: str
    execution_id: Optional[str]
    status: str
    data: Dict[str, Any]
```

**Deliverables:**

- ✅ Basic logging framework operational
- ✅ Unit tests: Queue operations, health check, signal handling
- ✅ Integration tests: Complete flow (log → queue → worker → file)

---

#### Day 2: Core Integration + Data Masking (6-8 hours)

**2.1 Integration with Existing System**

**Integration Point 1: SessionManager**

```python
# src/sessions/manager.py

from src.logging import get_action_logger

class SessionManager:
    def __init__(self):
        self.logger = get_action_logger()

    def start_session(self, project_name: str):
        session = Session(...)
        self.logger.log("session_start",
                       project_name=project_name,
                       session_id=session.session_id,
                       metadata={...})
        return session

    def end_session(self):
        self.logger.log("session_end",
                       session_id=self.current_session.session_id,
                       duration=...)
```

**Integration Point 2: EnhancedAgent**

```python
# src/agents/enhanced_agent.py

def _transition_state(self, new_state: AgentState):
    old_state = self.state
    self.state = new_state

    self.logger.log("agent_state_change",
                   from_state=old_state.value,
                   to_state=new_state.value,
                   reason="user_request")
```

**Integration Point 3: ToolExecutor**

```python
# src/tools/executor.py

async def execute_tool(self, tool_name: str, args: dict):
    tool_use_id = generate_id()

    self.logger.log("tool_call",
                   tool_name=tool_name,
                   tool_use_id=tool_use_id,
                   args=args,
                   permission_level=tool.permission_level)

    try:
        result = await tool.execute(**args)
        self.logger.log("tool_result",
                       tool_use_id=tool_use_id,
                       success=True,
                       output=result.output[:1000])  # Truncate
    except Exception as e:
        self.logger.log("tool_error",
                       tool_use_id=tool_use_id,
                       error_type=type(e).__name__,
                       error_message=str(e))
```

**Integration Point 4: LLM Clients**

```python
# src/clients/base.py (add to all client base classes)

async def create_message(self, messages, tools=None, **kwargs):
    request_id = generate_id()

    self.logger.log("llm_request",
                   provider=self.provider_name,
                   model=self.model_name,
                   messages_count=len(messages),
                   request_id=request_id)

    try:
        response = await self._do_request(...)
        self.logger.log("llm_response",
                       request_id=request_id,
                       input_tokens=response.usage.input_tokens,
                       output_tokens=response.usage.output_tokens)
    except Exception as e:
        self.logger.log("llm_error",
                       request_id=request_id,
                       error_type=type(e).__name__)
```

**2.2 Data Masking Implementation**

```python
# src/logging/masking.py

class DataMasker:
    def __init__(self, config: MaskingConfig):
        self.enabled = config.mask_sensitive_data
        self.sensitive_fields = config.custom_sensitive_fields
        self._compile_patterns()

    def mask(self, data: dict) -> dict:
        """Recursively mask dictionary data"""
        if not self.enabled:
            return data

        masked = {}
        for key, value in data.items():
            if self._is_sensitive_field(key):
                masked[key] = "[MASKED]"
            elif isinstance(value, str):
                masked[key] = self._mask_patterns(value)
            elif isinstance(value, dict):
                masked[key] = self.mask(value)  # Recursive
            else:
                masked[key] = value
        return masked

    def _mask_patterns(self, text: str) -> str:
        """Pattern-based masking using regex"""
        # API keys: sk-ant-api03-xxx...
        text = re.sub(r'sk-[a-zA-Z0-9]{48}', 'sk-***[MASKED]***', text)
        # Bearer token
        text = re.sub(r'Bearer\s+[A-Za-z0-9\-._~+/]+', 'Bearer [MASKED]', text)
        # File paths
        text = re.sub(r'/Users/[^/]+/', '/Users/[USER]/', text)
        return text
```

**2.3 Implement Core Action Types (10 types)**

- USER_INPUT
- USER_COMMAND
- AGENT_STATE_CHANGE
- LLM_REQUEST
- LLM_RESPONSE
- TOOL_CALL
- TOOL_RESULT
- TOOL_ERROR
- SESSION_START
- SESSION_END

**Deliverables:**

- ✅ All 5 integration points completed
- ✅ Data masking working properly
- ✅ Integration test: Complete user scenario (input → LLM → tool → output)

---

#### Day 3: Configuration System + Basic Query Tool (6-8 hours)

**3.1 Update Configuration Template**

```json
# templates/settings.json

{
  "logging": {
    "enabled": true,
    "log_dir": "~/.tiny-claude-code/logs",
    "async_logging": true,
    "queue_size": 1000,
    "batch_size": 100,
    "batch_timeout_sec": 1,
    "mask_sensitive_data": true,
    "custom_sensitive_fields": [],
    "action_types": {
      "user_input": true,
      "user_command": true,
      ...
    }
  }
}
```

**3.2 Configuration Loading and Validation**

```python
# src/logging/config.py

from pydantic import BaseModel, Field, validator

class LoggingConfig(BaseModel):
    enabled: bool = True
    log_dir: str = "~/.tiny-claude-code/logs"
    async_logging: bool = True
    queue_size: int = Field(default=1000, ge=100, le=10000)
    batch_size: int = Field(default=100, ge=10, le=1000)

    @validator('log_dir')
    def expand_path(cls, v):
        return Path(v).expanduser()
```

**3.3 Implement `/log` Command (MVP Version)**

```python
# src/commands/log_command.py

class LogCommand:
    """Basic query tool (11.2.5 phased implementation)"""

    def execute(self, args: argparse.Namespace):
        # Phase 1 supported features
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        tail = args.tail or 50
        keyword = args.keyword
        format = args.format or "table"

        # Stream read log file
        results = self._query_logs(date, keyword, tail)

        # Format output
        if format == "table":
            self._print_table(results)
        elif format == "json":
            print(json.dumps(results, indent=2))
```

**Supported Query Options (MVP):**

```bash
/log                      # Last 50 entries from today
/log --tail 100           # Last 100 entries
/log --date 2025-11-21    # Specific date
/log --keyword "error"    # Keyword search
/log --format table|json  # Output format
```

**3.4 Register Command**

```python
# src/commands/__init__.py

BUILTIN_COMMANDS = {
    "status": StatusCommand,
    "todos": TodosCommand,
    "log": LogCommand,  # New
    ...
}
```

**Deliverables:**

- ✅ Complete configuration system (template + loading + validation)
- ✅ `/log` command available (MVP features)
- ✅ E2E test: Complete user workflow test

---

### Phase 1 Acceptance Criteria

**Functional Acceptance:**

- Start the program, all actions written in real-time to `~/.tiny-claude-code/logs/YYYY-MM-DD.jsonl`
- Press Ctrl+C twice, verify log file contains all operations before exit
- Check log file, verify API keys are masked
- Run `/log` command, can see today's logs
- Run `/log --keyword "error"`, can filter logs containing "error"

**Performance Acceptance:**

- Each action logging latency < 1ms (async queue)
- No noticeable lag in program execution
- Background thread CPU usage < 5%

**Test Coverage:**

- Unit test coverage > 80%
- Integration tests cover all 5 integration points
- Ctrl+C test passed

---

## Phase 2: Enhanced Features - 2 Working Days

### Objectives

Complete action types + Advanced masking + Disk management + Structured filtering

### Task Breakdown

#### Day 4: Complete Action Types + Advanced Masking (6-8 hours)

**4.1 Add Remaining Action Types (9 types)**

- AGENT_THINKING
- LLM_ERROR
- TOOL_PERMISSION
- SESSION_PAUSE
- SESSION_RESUME
- HOOK_EXECUTE
- HOOK_ERROR
- SYSTEM_ERROR
- SYSTEM_WARNING

**Integration Points:**

- EventBus → SYSTEM_ERROR/WARNING
- HookManager → HOOK_EXECUTE/ERROR
- PermissionManager → TOOL_PERMISSION

**4.2 Advanced Data Masking**

```python
class DataMasker:
    def _mask_patterns(self, text: str) -> str:
        # New patterns
        # Email
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                     '[EMAIL_MASKED]', text)
        # Phone number (China)
        text = re.sub(r'1[3-9]\d{9}', '[PHONE_MASKED]', text)
        # Credit card number
        text = re.sub(r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',
                     '[CARD_MASKED]', text)
        return text
```

**4.3 Configurable Masking Rules**

```python
# Support user-defined sensitive fields
config.custom_sensitive_fields = ["internal_token", "ssh_key"]
```

**Deliverables:**

- ✅ All 19 action types implemented
- ✅ Advanced masking rules in effect
- ✅ Unit tests: Various masking patterns

---

#### Day 5: Disk Management + Structured Filtering (6-8 hours)

**5.1 Disk Management**

```python
# src/logging/cleaner.py

class LogCleaner:
    def __init__(self, config: CleanupConfig):
        self.retention_days = config.retention_days
        self.max_total_size_mb = config.max_total_size_mb

    def cleanup(self):
        """Auto cleanup strategy"""
        log_files = self._scan_log_files()

        # Step 1: Delete files older than retention period
        self._delete_old_files(log_files, self.retention_days)

        # Step 2: Check total size, delete oldest files until limit met
        total_size = self._calculate_total_size(log_files)
        if total_size > self.max_total_size_mb * 1024 * 1024:
            self._delete_until_size_limit(log_files)

    def compress_old_logs(self, days_threshold=7):
        """Compress logs older than N days"""
        for log_file in self._get_old_uncompressed_files(days_threshold):
            self._compress_file(log_file)  # gzip
```

**5.2 Auto Cleanup on Startup**

```python
# src/main.py

def main():
    config = load_config()

    if config.logging.cleanup_on_startup:
        cleaner = LogCleaner(config.logging)
        cleaner.cleanup()

    # ... Start application
```

**5.3 Structured Filtering (Phase 2 Query Features)**

```python
# src/commands/log_command.py (extended)

class LogQueryEngine:
    def filter(self,
               date: str,
               action_types: List[str] = None,
               status: str = None,
               session_id: str = None,
               tool_name: str = None,
               limit: int = 1000):
        """Structured filtering"""
        results = []

        with open(self._get_log_file(date), 'r') as f:
            for line in f:
                record = json.loads(line)

                # Multi-condition filtering
                if action_types and record['action_type'] not in action_types:
                    continue
                if status and record.get('status') != status:
                    continue
                if session_id and record.get('session_id') != session_id:
                    continue
                if tool_name and record.get('tool_name') != tool_name:
                    continue

                results.append(record)
                if len(results) >= limit:
                    break

        return results
```

**New Query Options:**

```bash
/log --action-type tool_error                      # By type
/log --status error                                # By status
/log --session-id session-xxx                      # By session
/log --action-type tool_call --status success --tool-name bash
```

**Deliverables:**

- ✅ Disk cleanup mechanism working
- ✅ Auto-compress logs after 7 days
- ✅ Structured filter queries available
- ✅ Performance test: Large file query performance

---

### Phase 2 Acceptance Criteria

**Functional Acceptance:**

- All 19 action types logged correctly
- Emails and phone numbers auto-masked
- On startup, auto-clean logs older than 30 days
- Logs older than 7 days auto-compressed to .gz
- `/log --action-type tool_error` can precisely filter

**Performance Acceptance:**

- 100MB log file query response time < 2 seconds
- Async logging throughput > 1000 actions/sec

---

## Phase 3: Production Ready - 2 Working Days

### Objectives

Log compression + Complete query tool + Programmatic API + Monitoring & alerts

### Task Breakdown

#### Day 6: Complete Query Tool + Programmatic API (6-8 hours)

**6.1 Advanced Query Features**

```bash
# Date range
/log --date-range 2025-11-15:2025-11-21

# Statistical summary
/log --format summary

# Result limit
/log --limit 50
```

**6.2 Statistical Summary Implementation**

```python
def generate_summary(logs: List[dict]) -> dict:
    """Generate statistical summary"""
    summary = {
        "total_actions": len(logs),
        "sessions": len(set(log['session_id'] for log in logs)),
        "errors": sum(1 for log in logs if 'error' in log['action_type']),
        "type_distribution": Counter(log['action_type'] for log in logs),
        "status_distribution": Counter(log['status'] for log in logs),
    }
    return summary
```

**6.3 Programmatic API**

```python
# src/logging/query.py

class LogQueryEngine:
    """Programmatic API for internal use"""

    def filter(self,
               date_range: Tuple[str, str] = None,
               action_types: List[str] = None,
               session_id: str = None,
               status: str = None) -> 'Query':
        self._filters.update(...)
        return self

    def limit(self, n: int) -> 'Query':
        self._limit = n
        return self

    def execute(self) -> List[Dict[str, Any]]:
        """Execute query, return results"""
        return self._do_query()

# Usage example
from src.logging import LogQueryEngine

results = LogQueryEngine().filter(
    date_range=("2025-11-20", "2025-11-21"),
    action_types=["tool_call", "tool_error"],
    status="error"
).limit(100).execute()
```

**Deliverables:**

- ✅ Complete query features (all filter conditions)
- ✅ Statistical summary generation
- ✅ Programmatic API available

---

#### Day 7: Monitoring & Alerts + Documentation + Final Testing (6-8 hours)

**7.1 Monitoring and Alerts**

```python
# src/logging/monitor.py

class LoggingMonitor:
    def __init__(self):
        self._error_count = 0
        self._last_alert_time = 0

    def on_log_write_failed(self, error: Exception):
        """Alert on log write failure"""
        self._error_count += 1

        # Fallback to stderr
        sys.stderr.write(f"[LOGGING ERROR] {error}\n")

        # If fails 5 times consecutively, trigger alert
        if self._error_count >= 5:
            self._send_alert("Logging system degraded")

    def on_queue_full(self):
        """Alert on queue full"""
        current_time = time.time()
        # Avoid alert storm (max once per minute)
        if current_time - self._last_alert_time > 60:
            self._send_alert("Log queue full, dropping logs")
            self._last_alert_time = current_time

    def _send_alert(self, message: str):
        # Phase 3: Simple output to stderr
        # Phase 4: Can integrate email/Slack/DingTalk notifications
        sys.stderr.write(f"[ALERT] {message}\n")
```

**7.2 Configuration Validation and Default Value Handling**

```python
# src/logging/config.py

class LoggingConfig(BaseModel):
    @validator('queue_size')
    def validate_queue_size(cls, v):
        if v < 100:
            logger.warning(f"queue_size {v} too small, using 100")
            return 100
        if v > 10000:
            logger.warning(f"queue_size {v} too large, using 10000")
            return 10000
        return v
```

**7.3 Update Documentation**

- README.md - Add logging system description
- Create `docs/logging_guide.md` - Detailed usage guide
- Update CLAUDE.md - Add logging system to architecture description

**7.4 Final E2E Testing**

```python
# tests/e2e/test_full_logging_workflow.py

def test_complete_user_workflow():
    """Test complete user workflow logging"""
    # 1. Start session
    # 2. User input
    # 3. LLM call
    # 4. Tool execution
    # 5. Error handling
    # 6. End session
    # 7. Ctrl+C exit
    # 8. Verify log integrity
    pass

def test_disk_full_scenario():
    """Test disk full scenario"""
    # Simulate disk full, verify fallback to stderr
    pass

def test_configuration_errors():
    """Test configuration error scenarios"""
    # Verify configuration validation and default value fallback
    pass
```

**Deliverables:**

- ✅ Monitoring and alert mechanism
- ✅ Robust configuration validation
- ✅ Documentation updates complete
- ✅ All E2E tests passed

---

### Phase 3 Acceptance Criteria

**Functional Acceptance:**

- `/log --format summary` displays complete statistics
- Alert output to stderr on log write failure
- Friendly prompts and default values on configuration errors
- Complete documentation, users can use independently

**Performance Acceptance:**

- Stress test: 10,000 consecutive log writes without loss
- Boundary test: Graceful handling of disk full, permission errors, configuration errors

**Code Quality:**

- Code review passed
- Test coverage > 85%
- No critical-level lint warnings

---

## 📊 Overall Progress Tracking

| Phase             | Time  | Key Deliverables                      | Status      |
| ----------------- | ----- | ------------------------------------- | ----------- |
| Phase 1 Day 1     | 1 day | Logging infrastructure + Health check | ⏳ Pending  |
| Phase 1 Day 2     | 1 day | Core integration + Data masking       | ⏳ Pending  |
| Phase 1 Day 3     | 1 day | Configuration system + Basic query    | ⏳ Pending  |
| Phase 1 Milestone | 3 days| MVP available                         | ⏳ Pending  |
| Phase 2 Day 4     | 1 day | Complete action types + Advanced mask | ⏳ Pending  |
| Phase 2 Day 5     | 1 day | Disk management + Structured filter   | ⏳ Pending  |
| Phase 2 Milestone | 2 days| Enhanced features complete            | ⏳ Pending  |
| Phase 3 Day 6     | 1 day | Complete query + Programmatic API     | ⏳ Pending  |
| Phase 3 Day 7     | 1 day | Monitoring + Documentation + Testing  | ⏳ Pending  |
| Phase 3 Milestone | 2 days| Production ready                      | ⏳ Pending  |

---

## 🎯 Key Risk Mitigation Measures (Embedded in Implementation)

| Risk Item              | Mitigation Solution                           | Implementation Phase |
| ---------------------- | --------------------------------------------- | -------------------- |
| 🔴 Background thread   | Health check + Fallback mechanism             | Phase 1 Day 1 ✅     |
| 🟡 Queue full strategy | Simple drop (MVP) → Tiered (Phase 2)          | Phase 1 → Phase 2    |
| 🟡 Query tool complex  | Phased (tail+grep → Structured → Advanced)    | Phase 1-3 ✅         |
| 🟢 Performance opt     | Not implemented, Phase 4 optional orjson      | Phase 4+             |
| 🟢 Log rotation atomic | Not implemented (single process, not needed)  | Phase 3+             |

---

## 📝 Implementation Notes

### 1. Backward Compatibility

- ✅ Logging system fully optional (disable via config)
- ✅ No modification to existing Session system core logic
- ✅ Integration via dependency injection

### 2. Testing Strategy

- TDD mode: Write tests first, then implementation (especially health check logic)
- Continuous integration: Run full test suite after each day
- Manual testing: Manual acceptance of key features after each phase

### 3. Code Review Checkpoints

- Phase 1 Day 2 end: Code review (core architecture)
- Phase 2 Day 5 end: Code review (feature completeness)
- Phase 3 Day 7 end: Final review (production readiness)

### 4. Performance Monitoring

- Run performance tests at end of each day
- Record key metrics: Log latency, throughput, memory usage
- If performance drops > 20%, investigate immediately

---

## ✅ Final Delivery Checklist

### Code Deliverables:

- `src/logging/` module (5 files)
- 5 integration point code modifications
- `/log` command implementation
- Configuration template update (`templates/settings.json`)

### Test Deliverables:

- Unit tests (`tests/unit/test_action_logger.py`, etc.)
- Integration tests (`tests/integration/test_logging_integration.py`)
- E2E tests (`tests/e2e/test_full_logging_workflow.py`)
- Performance tests (`tests/performance/test_logging_performance.py`)

### Documentation Deliverables:

- README.md update (add logging system description)
- `docs/logging_guide.md` (user usage guide)
- CLAUDE.md update (architecture description)
- Design document (already exists: `p11-structured-action-logging-design-document.md`)
