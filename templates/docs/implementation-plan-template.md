# [PX/HFX] Feature/Fix Name - Implementation Plan

> **Template Version**: 2.0 (Added E2E Test Scenarios section)
> **Created**: YYYY-MM-DD
> **Status**: Draft | In Progress | Completed
>
> **v2.0 Changes**:
> - Added Section 4: E2E Test Scenarios & Execution Plan
> - E2E tests now written BEFORE implementation
> - Manual test checklist for scenarios that cannot be automated

---

## 📚 Related Documents

**Design Document**: [docs/features/vX.X.X/pX-xxx-design-document.md](./pX-xxx-design-document.mdd) or [docs/hotfixes/vYYYY-MM-DD/hX-xxx-design-document.md](./hX-xxx-design-document.mdd)

---

## 1. Implementation Steps

### Phase 1: Core Features

#### Step 1.1: [Step name]

**Priority**: P0
**Estimated Time**: [X hours/days]

- [ ] Task 1.1.1: [Specific task description]

  - Affected files: `src/module/file.py`
  - Key logic: [Brief explanation]

- [ ] Task 1.1.2: [...]
  - Affected files: `src/module/another.py`
  - Key logic: [...]

**Acceptance Criteria**:

- [ ] Feature functional
- [ ] Unit tests pass

---

#### Step 1.2: [Step name]

**Priority**: P0
**Estimated Time**: [X hours/days]

- [ ] Task 1.2.1: [...]
- [ ] Task 1.2.2: [...]

**Acceptance Criteria**:

- [ ] ...

---

### Phase 2: Extended Features

#### Step 2.1: [Step name]

**Priority**: P1
**Estimated Time**: [X hours/days]

- [ ] Task 2.1.1: [...]
- [ ] Task 2.1.2: [...]

**Acceptance Criteria**:

- [ ] ...

---

## 2. File Checklist

### 2.1 New Files

#### Core Module Files

- [ ] `src/logging/__init__.py`

  - **Purpose**: Module initialization, export public API
  - **Key content**: `get_action_logger()` singleton function

- [ ] `src/logging/action_logger.py`

  - **Purpose**: Core logger
  - **Key class**: `ActionLogger`
  - **Dependencies**: `queue`, `threading`, `logging`

- [ ] `src/logging/types.py`

  - **Purpose**: Type definitions
  - **Key classes**: `ActionType`, `ActionData`, `ActionStatus`
  - **Dependencies**: `Pydantic`, `datetime`

- [ ] `src/logging/log_writer.py`

  - **Purpose**: File writer
  - **Key class**: `LogWriter`
  - **Dependencies**: `Path`, `json`

- [ ] `src/logging/constants.py`
  - **Purpose**: Constant definitions
  - **Key constants**: `DEFAULT_QUEUE_SIZE`, `DEFAULT_BATCH_SIZE`

#### Test Files

- [ ] `tests/unit/logging/test_action_logger.py`

  - **Purpose**: ActionLogger unit tests
  - **Coverage**: Initialization, log(), flush(), shutdown()

- [ ] `tests/unit/logging/test_masking.py`

  - **Purpose**: Data masking tests
  - **Coverage**: Various sensitive data patterns

- [ ] `tests/integration/test_logging_integration.py`
  - **Purpose**: End-to-end integration tests
  - **Coverage**: Complete logging workflow

#### Documentation Files

- [ ] `docs/features/vX.X.X/pX-feature-name.md` (Design document)
- [ ] `docs/features/vX.X.X/pX-feature-name-implement-plan.md` (This document)
- [ ] `docs/reports/vX.X.X/pX-feature-name-report.md` (Review document, create after implementation)

---

### 2.2 Modified Files

- [ ] `src/cli/main.py`

  - **Changes**:
    - Import `get_action_logger()`
    - Initialize logger on startup
    - Add cleanup logic in finally block
  - **Modification locations**:
    - Line ~10: Import statements
    - Line ~70: Initialization
    - Line ~180: Finally block

- [ ] `src/sessions/manager.py`

  - **Changes**:
    - Add `get_current_session_id()` method
    - Log in `start_session()`
    - Log in `end_session()`
  - **Modification locations**:
    - Line ~24: Add getter method
    - Line ~50: Log session start
    - Line ~65: Log session end

- [ ] `src/commands/builtin.py`

  - **Changes**:
    - ExitCommand add cleanup logic
  - **Modification locations**:
    - Line ~75: Add cleanup before sys.exit()

- [ ] `src/agents/enhanced_agent.py`

  - **Changes**:
    - Log at key state transitions
  - **Modification locations**:
    - Various state transition points

- [ ] `README.md` and `README_zh.md`
  - **Changes**:
    - Add logging feature to Core Features section
    - Add logging system explanation to Architecture section
    - Update test statistics in Testing section

---

## 3. Core Logic Implementation

### 3.1 ActionLogger Class Design

```python
class ActionLogger:
    """
    Action logger

    Responsibilities:
    - Async logging (non-blocking)
    - Background thread batch writing
    - Health checks and auto-recovery
    """

    def __init__(
        self,
        log_dir: Path,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        batch_timeout: float = DEFAULT_BATCH_TIMEOUT,
        enabled: bool = True,
        session_manager=None,
    ):
        """Initialize logger"""
        self.enabled = enabled
        self.log_dir = Path(log_dir).expanduser()
        self._queue = queue.Queue(maxsize=queue_size)
        self._session_manager = session_manager

        # Start background thread
        self._start_worker()

    def log(
        self,
        action_type: str,
        session_id: Optional[str] = None,
        status: str = ActionStatus.SUCCESS,
        **data
    ) -> None:
        """Log action (async, non-blocking)"""
        if not self.enabled:
            return

        # Auto-retrieve session_id
        if session_id is None and self._session_manager:
            session_id = self._session_manager.get_current_session_id()

        if session_id is None:
            session_id = "unknown"

        # Create action data
        action_data = ActionData.create(
            action_type=action_type,
            session_id=session_id,
            status=status,
            **data
        )

        # Mask sensitive data
        masked_dict = self._masker.mask(action_data.to_dict())

        # Put in queue (non-blocking)
        try:
            self._queue.put_nowait(masked_dict)
        except queue.Full:
            logger.warning(f"Log queue full, dropping log: {action_type}")

    def flush(self) -> None:
        """Force flush all logs in queue"""
        batch = []
        while not self._queue.empty():
            try:
                record = self._queue.get_nowait()
                batch.append(record)
            except queue.Empty:
                break

        if batch:
            self._writer.write_batch(batch)

    def shutdown(self) -> None:
        """Shutdown logger"""
        # Stop background thread
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)

        # Flush remaining logs
        self.flush()

        # Close files
        self._writer.close()

    def _start_worker(self) -> None:
        """Start background thread"""
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker,
            name="ActionLogger-Worker",
            daemon=True
        )
        self._worker_thread.start()

    def _worker(self) -> None:
        """Background thread: batch write logs"""
        while self._running:
            batch = self._collect_batch()
            if batch:
                try:
                    self._writer.write_batch(batch)
                except Exception as e:
                    logger.error(f"Worker failed to write batch: {e}")

    def _collect_batch(self) -> List[Dict[str, Any]]:
        """Collect a batch of logs from queue"""
        batch = []
        deadline = time.time() + self.batch_timeout

        while len(batch) < self.batch_size and time.time() < deadline:
            try:
                timeout = max(0.01, deadline - time.time())
                record = self._queue.get(timeout=timeout)
                batch.append(record)
            except queue.Empty:
                break

        return batch
```

---

### 3.2 Singleton Pattern Implementation

```python
# src/logging/__init__.py

_action_logger_instance: Optional[ActionLogger] = None

def get_action_logger() -> ActionLogger:
    """Get ActionLogger singleton"""
    global _action_logger_instance

    if _action_logger_instance is None:
        from .constants import DEFAULT_LOG_DIR
        _action_logger_instance = ActionLogger(
            log_dir=Path(DEFAULT_LOG_DIR).expanduser()
        )

    return _action_logger_instance
```

---

### 3.3 SessionManager Integration

```python
# src/sessions/manager.py

class SessionManager:
    def __init__(self, persistence_manager, action_logger=None):
        self.persistence = persistence_manager
        self.current_session = None
        self.logger = action_logger or get_action_logger()

    def get_current_session_id(self) -> Optional[str]:
        """Get current session_id"""
        return self.current_session.session_id if self.current_session else None

    def start_session(self, project_name: str) -> Session:
        """Start session"""
        self.current_session = Session(
            session_id=f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}-{datetime.now().microsecond}",
            project_name=project_name,
            start_time=datetime.now()
        )

        # Log event
        self.logger.log(
            action_type=ActionType.SESSION_START,
            session_id=self.current_session.session_id,
            project_name=project_name
        )

        return self.current_session

    async def end_session_async(self) -> None:
        """End session (async version)"""
        if self.current_session:
            self.current_session.end_time = datetime.now()

            # Log event
            self.logger.log(
                action_type=ActionType.SESSION_END,
                session_id=self.current_session.session_id,
                duration_seconds=(
                    self.current_session.end_time -
                    self.current_session.start_time
                ).total_seconds()
            )

            await self.save_session_async()
            self.current_session = None
```

---

### 3.4 Exit Cleanup Logic

```python
# src/commands/builtin.py

class ExitCommand(Command):
    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        print("\n👋 Goodbye!")

        from ..logging import get_action_logger
        from ..logging.constants import DEFAULT_BATCH_TIMEOUT
        import time

        # End session
        if hasattr(context.agent, 'session_manager'):
            session_manager = context.agent.session_manager
            if session_manager.current_session:
                await session_manager.end_session_async()

        # Wait for worker thread to complete batch write
        action_logger = get_action_logger()
        wait_time = DEFAULT_BATCH_TIMEOUT + 0.5
        time.sleep(wait_time)

        # Shutdown logger
        action_logger.shutdown()

        sys.exit(0)
```

---

## 4. E2E Test Scenarios & Execution Plan

> **NEW in v2.0**: E2E tests written BEFORE implementation to expose real-world gaps

### 4.1 Test Scenarios Overview

Link to detailed E2E scenarios document:
**E2E Scenarios**: [docs/features/vX.X.X/pX-xxx-e2e-scenarios.md](./pX-xxx-e2e-scenarios.md)

**Summary**:

| Scenario | Priority | Can Automate? | Expected Result |
|----------|----------|---------------|-----------------|
| [e.g., User cancels LLM with ESC] | P0 | Partial (CLI response only) | Cancelled within 1s |
| [e.g., Missing permissions on startup] | P0 | Yes | Warning displayed, feature disabled |
| [e.g., ESC during input clears text] | P1 | No (manual) | Input cleared, no cancellation |

### 4.2 Automated E2E Tests

**Test File**: `tests/e2e/test_pX_feature_name.py`

**Test Strategy**:
```python
class CLISession:
    """Wrapper for real CLI subprocess"""
    def start(self): ...
    def send_input(self, text): ...
    def read_output(self, timeout): ...
    def terminate(self): ...

@pytest.mark.e2e
class TestFeatureName:
    def test_scenario_1(self):
        """Automated test for Scenario 1"""
        with CLISession() as session:
            session.send_input("trigger feature")
            output = session.read_output(timeout=5)
            assert "expected result" in output
```

**Limitations**:
- ❌ Cannot simulate: [e.g., Real ESC key press, window focus changes]
- ✅ Can test: [e.g., CLI startup, command execution, permission detection]

### 4.3 Manual Test Checklist

For scenarios that cannot be automated:

**Manual Test 1**: [e.g., ESC cancels LLM call]
```
Steps:
1. Start CLI: python -m src.main
2. Send: "Generate large file"
3. Press ESC after 2s
4. Verify: "Cancelled" message appears within 1s
5. Verify: CLI returns to prompt (not crashed)

Expected: ⚠️ Execution cancelled by user (ESC pressed)
```

**Manual Test 2**: [e.g., Window focus detection]
```
Steps:
1. Start CLI
2. Trigger long operation
3. Switch to browser (terminal loses focus)
4. Press ESC
5. Verify: Behavior depends on require_window_focus setting

Expected: ESC ignored if require_window_focus=True
```

### 4.4 Test Execution Order

**Phase 1: E2E Tests (BEFORE Implementation)**
1. Write E2E test scenarios (expect ALL to fail)
2. Commit failing tests to repository
3. Use failures to refine implementation plan

**Phase 2: Unit Tests (DURING Implementation)**
4. Write unit tests for each module
5. Tests pass as implementation progresses

**Phase 3: Integration Tests (AFTER Core Implementation)**
6. Write integration tests for component interaction
7. Tests validate end-to-end workflows

**Phase 4: E2E Validation (COMPLETION Criteria)**
8. Run E2E tests again
9. Fix issues until tests pass
10. Run manual test checklist
11. **Definition of Done**: All automated E2E tests pass, manual checklist verified

### 4.5 Test Environment Requirements

**Automated Tests**:
- Python >= 3.10
- pytest, pytest-asyncio
- Mock LLM server (if needed)
- Temp directory for isolated testing

**Manual Tests**:
- Real terminal (Terminal.app, iTerm2, etc.)
- macOS Accessibility permissions (for keyboard tests)
- API keys (if testing real LLM calls)

---

## 5. Testing Strategy (Unit & Integration)

### 5.1 Unit Tests

#### ActionLogger Tests

**File**: `tests/unit/logging/test_action_logger.py`

**Test Cases**:

```python
class TestActionLogger:
    def test_init(self):
        """Test initialization"""
        logger = ActionLogger(log_dir="/tmp/logs")
        assert logger.enabled == True
        assert logger._queue.qsize() == 0

    def test_log_basic(self):
        """Test basic logging"""
        logger = ActionLogger(log_dir="/tmp/logs")
        logger.log(
            action_type="test_action",
            session_id="test-session",
            data="test data"
        )
        assert logger._queue.qsize() == 1

    def test_log_auto_session_id(self):
        """Test automatic session_id retrieval"""
        mock_session_manager = Mock()
        mock_session_manager.get_current_session_id.return_value = "auto-session"

        logger = ActionLogger(
            log_dir="/tmp/logs",
            session_manager=mock_session_manager
        )
        logger.log(action_type="test_action")

        # Verify session_id was auto-retrieved
        mock_session_manager.get_current_session_id.assert_called_once()

    def test_flush(self):
        """Test flush functionality"""
        logger = ActionLogger(log_dir="/tmp/logs")
        logger.log(action_type="test1", session_id="s1")
        logger.log(action_type="test2", session_id="s2")

        logger.flush()
        assert logger._queue.qsize() == 0

    def test_shutdown(self):
        """Test shutdown functionality"""
        logger = ActionLogger(log_dir="/tmp/logs")
        logger.log(action_type="test", session_id="s1")

        logger.shutdown()
        assert not logger._running
        assert logger._queue.qsize() == 0
```

**Coverage Target**: 80%+ code coverage

---

#### DataMasker Tests

**File**: `tests/unit/logging/test_masking.py`

**Test Cases**:

```python
class TestDataMasker:
    def test_mask_api_key(self):
        """Test API key masking"""
        masker = DataMasker(enabled=True)
        data = {"api_key": "sk-ant-api03-abcdef123456"}
        result = masker.mask(data)
        assert "sk-***[MASKED]***" in result["api_key"]

    def test_mask_email(self):
        """Test email masking"""
        masker = DataMasker(enabled=True)
        data = {"email": "user@example.com"}
        result = masker.mask(data)
        assert result["email"] == "[EMAIL_MASKED]"

    def test_mask_nested_data(self):
        """Test nested data masking"""
        masker = DataMasker(enabled=True)
        data = {
            "user": {
                "password": "secret123",
                "email": "user@example.com"
            }
        }
        result = masker.mask(data)
        assert result["user"]["password"] == "[MASKED]"
        assert result["user"]["email"] == "[EMAIL_MASKED]"
```

**Coverage Target**: All masking patterns

---

### 4.2 Integration Tests

**File**: `tests/integration/test_logging_integration.py`

**Test Scenarios**:

```python
class TestLoggingIntegration:
    def test_full_logging_workflow(self):
        """Test full logging workflow"""
        # 1. Initialize logger
        logger = ActionLogger(log_dir="/tmp/test-logs")

        # 2. Log various types of events
        logger.log(action_type=ActionType.SESSION_START, session_id="test-s1")
        logger.log(action_type=ActionType.USER_INPUT, session_id="test-s1", content="hello")
        logger.log(action_type=ActionType.TOOL_EXECUTION, session_id="test-s1", tool_name="bash")
        logger.log(action_type=ActionType.SESSION_END, session_id="test-s1")

        # 3. Wait for background thread to process
        time.sleep(2)

        # 4. Verify log file exists and contains all records
        log_file = Path("/tmp/test-logs") / f"{date.today().strftime('%Y-%m-%d')}.jsonl"
        assert log_file.exists()

        with open(log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 4

    def test_session_manager_integration(self):
        """Test integration with SessionManager"""
        # Test automatic session_id passing
        pass
```

**Coverage Target**: End-to-end critical workflows

---

### 4.3 Performance Tests

```python
def test_high_throughput():
    """Test high throughput scenario"""
    logger = ActionLogger(log_dir="/tmp/perf-test")

    start = time.time()
    for i in range(10000):
        logger.log(
            action_type="test",
            session_id=f"s-{i}",
            data=f"data-{i}"
        )
    elapsed = time.time() - start

    # Verify: 10000 logs should complete within 1 second (non-blocking)
    assert elapsed < 1.0
```

---

## 6. Dependencies

### 6.1 New Dependencies

#### Python Standard Library (no installation needed)

- `queue` - Queue management
- `threading` - Background threads
- `logging` - Logging framework
- `json` - JSON serialization
- `pathlib` - Path handling
- `datetime` - Timestamps
- `time` - Time-related operations

#### Third-party Libraries (already in project)

- `pydantic` - Data validation
- No new external dependencies needed ✅

### 5.2 Configuration Changes

#### `templates/settings.json`

Add logging configuration section:

```json
{
  "logging": {
    "enabled": true,
    "log_dir": "~/.tiny-claude-code/logs",
    "queue_size": 1000,
    "batch_size": 100,
    "batch_timeout": 1.0,
    "retention_days": 30,
    "max_total_size_mb": 1024,
    "compress_after_days": 7,
    "data_masking": {
      "enabled": true,
      "mask_api_keys": true,
      "mask_passwords": true,
      "mask_emails": true,
      "mask_phones": true,
      "mask_file_paths": true
    }
  }
}
```

---

## 7. Definition of Done

### 7.1 Functional Completion Criteria

- [ ] **Core features functional**

  - [ ] ActionLogger initialization normal
  - [ ] log() method can record all 17 ActionTypes
  - [ ] Automatic session_id retrieval mechanism works
  - [ ] Background worker thread runs normally
  - [ ] Batch write mechanism normal
  - [ ] Data masking works correctly

- [ ] **Exit cleanup normal**

  - [ ] `/exit` command correctly logs session_end
  - [ ] Ctrl+D (EOFError) cleanup works correctly
  - [ ] Abnormal exit can save logs

- [ ] **Query functionality available**
  - [ ] `/logs` command can display logs
  - [ ] `--status` filtering normal
  - [ ] `--keyword` search normal

---

### 7.2 Testing Completion Criteria

- [ ] **Unit tests pass**

  - [ ] ActionLogger: 243 tests, 100% pass
  - [ ] DataMasker: 360 tests, 100% pass
  - [ ] Code coverage ≥ 80%

- [ ] **Integration tests pass**

  - [ ] End-to-end logging workflow test passes
  - [ ] SessionManager integration test passes

- [ ] **Performance tests pass**
  - [ ] 10000 log records < 1s (non-blocking)
  - [ ] Worker thread CPU usage < 5%

---

### 7.3 Code Quality Criteria

- [ ] **Linting passes**

  - [ ] `flake8` no errors
  - [ ] `mypy` type checking passes
  - [ ] Code style consistent

- [ ] **Documentation complete**
  - [ ] All public APIs have docstrings
  - [ ] Complex logic has comments
  - [ ] README updated

---

### 7.4 Documentation Completion Criteria

- [ ] **Implementation documentation**

  - [ ] This implementation plan document complete
  - [ ] Code comments complete

- [ ] **User documentation**

  - [ ] README.md updated (English)
  - [ ] README_zh.md updated (Chinese)
  - [ ] Feature usage examples added

- [ ] **Review documentation**
  - [ ] Review report created: `docs/reports/vX.X.X/pX-feature-name-report.md`
  - [ ] Implementation checklist verified
  - [ ] Deviation analysis complete
  - [ ] Lessons learned summarized

---

## 7. Risks & Mitigation

### 7.1 Technical Risks

| Risk                                        | Impact | Probability | Mitigation                                | Status         |
| ------------------------------------------- | ------ | ----------- | ----------------------------------------- | -------------- |
| Daemon thread killed early causing log loss | High   | High        | Wait batch_timeout + 0.5s before exit     | ✅ Resolved    |
| Queue full causing log drops                | Medium | Low         | Use put_nowait() + warning log            | ✅ Handled     |
| Worker thread crash                         | High   | Low         | Health check + auto-restart (max 3 times) | ✅ Implemented |
| File write failure                          | Medium | Low         | Fallback to stderr                        | ✅ Implemented |

### 7.2 Implementation Risks

| Risk                      | Impact | Probability | Mitigation                       | Status        |
| ------------------------- | ------ | ----------- | -------------------------------- | ------------- |
| Context overflow          | High   | Medium      | MVP first, phased implementation | ✅ Controlled |
| Insufficient testing      | Medium | Low         | Write 800+ test cases            | ✅ Complete   |
| Documentation out of sync | Low    | Medium      | Three-document workflow          | ✅ Following  |

---

## 9. Progress Tracking

### 8.1 Overall Progress

- [x] **Phase 1: Design** (100%)

  - [x] Design document complete
  - [x] Implementation plan complete
  - [x] Design review approved

- [x] **Phase 2: Implementation** (100%)

  - [x] Core modules implemented
  - [x] Integrated into existing system
  - [x] Unit tests written
  - [x] Integration tests written

- [x] **Phase 3: Verification** (100%)

  - [x] Functional tests passed
  - [x] Performance tests passed
  - [x] Bug fixes complete

- [x] **Phase 4: Documentation** (100%)
  - [x] README updated
  - [x] Review report complete
  - [x] Code committed

### 8.2 Problems Encountered

#### Problem 1: Missing session_end logs

- **Symptom**: Only session_start, no session_end
- **Cause**: `/exit` calls `sys.exit(0)` terminating process immediately, daemon thread killed
- **Solution**: Add cleanup logic in ExitCommand, wait for worker to complete batch write
- **Status**: ✅ Resolved

#### Problem 2: response.usage is None causing AttributeError

- **Symptom**: `'NoneType' object has no attribute 'input_tokens'`
- **Cause**: All LLM clients directly access `response.usage.input_tokens`
- **Solution**: Add defensive check `if hasattr(response, 'usage') and response.usage`
- **Status**: ✅ Resolved

#### Problem 3: Duplicate agent_state_change logs

- **Symptom**: Two logs recorded for each state change
- **Cause**: Both enhanced_agent.py and event_listener.py listening to events
- **Solution**: Remove duplicate logging in event_listener.py
- **Status**: ✅ Resolved

---

## 9. Appendix

### 9.1 Complete ActionType List

```python
class ActionType:
    # User interactions
    USER_INPUT = "user_input"
    USER_COMMAND = "user_command"

    # Agent state
    AGENT_THINKING = "agent_thinking"
    AGENT_STATE_CHANGE = "agent_state_change"

    # Tool execution
    TOOL_EXECUTION = "tool_execution"
    TOOL_PERMISSION = "tool_permission"

    # LLM calls
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"

    # Session management
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_PAUSE = "session_pause"
    SESSION_RESUME = "session_resume"

    # System events
    SYSTEM_INIT = "system_init"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"

    # Configuration changes
    CONFIG_CHANGE = "config_change"

    # Permission management
    PERMISSION_CHANGE = "permission_change"
```

### 9.2 Data Masking Patterns

```python
SENSITIVE_PATTERNS = [
    # API keys
    (r"sk-ant-api03-[a-zA-Z0-9\-_]+", r"sk-***[MASKED]***"),
    (r"sk-[a-zA-Z0-9]{48,}", r"sk-***[MASKED]***"),

    # Bearer token
    (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", r"Bearer [MASKED]"),

    # User directory paths
    (r"/Users/[^/\s]+/", r"/Users/[USER]/"),
    (r"/home/[^/\s]+/", r"/home/[USER]/"),

    # Email addresses
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", r"[EMAIL_MASKED]"),

    # Phone numbers
    (r"1[3-9]\d{9}", r"[PHONE_MASKED]"),
]
```

### 9.3 References

- [Design Document](../features/vX.X.X/pX-feature-name.md)
- [Python threading documentation](https://docs.python.org/3/library/threading.html)
- [Python queue documentation](https://docs.python.org/3/library/queue.html)

---

## Change Log

| Date       | Version | Changes              | Author |
| ---------- | ------- | -------------------- | ------ |
| 2025-01-21 | 1.0     | Initial version      | [Name] |
| YYYY-MM-DD | 1.1     | [Change description] | [Name] |
