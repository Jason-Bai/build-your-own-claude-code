# Testing Strategy & Comprehensive Test Plan

## Overview

This document outlines a comprehensive testing strategy for "Build Your Own Claude Code" project. The project has **48 Python files, 6,600+ lines of code** across 9 modules. This plan establishes **80%+ code coverage** while keeping tests maintainable and meaningful.

**Current Status:**
- Existing Tests: 2 files (test_hooks.py, test_hooks_integration.py)
- Existing Test Cases: ~40
- Current Coverage: Unknown (untracked)

**Target:**
- Total Tests: ~140 test cases
- Coverage: 80%+ overall, 85%+ for critical modules
- Execution Time: ~40-50 seconds

---

## Module Analysis & Test Strategy

### 1. Agent System (`src/agents/`) - 1,171 lines | Priority: P0

**Files:**
- `enhanced_agent.py` (507 lines) - Main orchestrator
- `state.py` (106 lines) - FSM implementation
- `context_manager.py` (139 lines) - Message/context handling
- `tool_manager.py` (114 lines) - Tool registration & execution
- `permission_manager.py` (171 lines) - 3-tier permission system
- `feedback.py` (116 lines) - User feedback collection
- `__init__.py` (18 lines)

**Test Coverage Target: 85%**

#### Test Strategy

**Unit Tests (~35-40 tests)**

| File | Test Class | Test Cases | Focus |
|------|-----------|-----------|-------|
| state.py | TestAgentState | 6-8 | FSM transitions, state validation, statistics |
| context_manager.py | TestContextManager | 8-10 | Token counting, compression, summarization |
| tool_manager.py | TestToolManager | 6-8 | Tool registration, execution, retry logic |
| permission_manager.py | TestPermissionManager | 8-10 | 3-tier permission checks, approval flow |
| feedback.py | TestFeedback | 4-5 | Feedback collection, formatting |
| enhanced_agent.py | TestEnhancedAgent | 8-10 | Main workflow, state transitions, error handling |

**Integration Tests (~8-12 tests)**

| Test Scenario | Test Name | Focus |
|---------------|-----------|-------|
| Full workflow | test_agent_complete_workflow | User input → Agent thinking → Tool execution → Response |
| State machine | test_agent_state_transitions | All valid/invalid state transitions |
| Error recovery | test_agent_error_handling | Tool failure recovery, state rollback |
| Token management | test_agent_token_overflow | Context compression when reaching limit |
| Permission denial | test_agent_permission_denied_flow | Tool execution with permission denial |

**Key Test Points:**
- ✓ FSM state transitions (all 5 states)
- ✓ Token calculation accuracy
- ✓ Context compression trigger (at 80% of limit)
- ✓ Tool retry with exponential backoff
- ✓ Error isolation (one tool failure doesn't break workflow)
- ✓ Permission system (SAFE/NORMAL/DANGEROUS)

**Test Data Fixtures:**
```python
# conftest.py
@pytest.fixture
def sample_agent_state():
    return AgentState(model="claude-sonnet-4.5")

@pytest.fixture
def sample_messages():
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]

@pytest.fixture
def mock_tool():
    tool = Mock(spec=BaseTool)
    tool.name = "test_tool"
    tool.permission_level = PermissionLevel.NORMAL
    return tool
```

---

### 2. LLM Clients (`src/clients/`) - 770 lines | Priority: P0

**Files:**
- `base.py` (190 lines) - Abstract interface
- `anthropic.py` (108 lines) - Anthropic implementation
- `openai.py` (187 lines) - OpenAI implementation
- `google.py` (177 lines) - Google implementation
- `factory.py` (73 lines) - Client factory
- `__init__.py` (35 lines)

**Test Coverage Target: 80%**

#### Test Strategy

**Unit Tests (~25-30 tests)**

| File | Test Class | Test Cases | Focus |
|------|-----------|-----------|-------|
| base.py | TestBaseClient | 4-5 | Interface validation, abstract method enforcement |
| anthropic.py | TestAnthropicClient | 8-10 | API call formatting, response parsing, error handling |
| openai.py | TestOpenAIClient | 8-10 | API compatibility, model detection |
| google.py | TestGoogleClient | 6-8 | Gemini API compatibility |
| factory.py | TestClientFactory | 4-5 | Client selection, auto-detection |

**Integration Tests (~6-8 tests)**

| Test Scenario | Focus |
|---------------|-------|
| Mock API calls | Verify correct request formatting |
| Response parsing | Correct message extraction |
| Error handling | Graceful failure, retry logic |
| Provider switching | Multiple providers in same session |
| Token estimation | Token count accuracy per provider |

**Key Test Points:**
- ✓ All 3 providers (Anthropic, OpenAI, Google) work independently
- ✓ API request format matches each provider's spec
- ✓ Error responses handled gracefully
- ✓ Token estimation accurate (±5%)
- ✓ Provider factory auto-detection works
- ✓ Stream vs. non-stream responses both supported

**Mock Strategy:**
```python
# Mock API responses for all providers
@pytest.fixture
def mock_anthropic_response():
    return {
        "id": "msg-123",
        "content": [{"type": "text", "text": "Response text"}],
        "stop_reason": "end_turn"
    }

# No actual API calls in unit tests
# Use responses library or unittest.mock
```

---

### 3. Tool System (`src/tools/`) - 871 lines | Priority: P0

**Files:**
- `file_ops.py` (279 lines) - Read/Write/Edit
- `bash.py` (115 lines) - Shell execution
- `search.py` (216 lines) - Glob/Grep
- `todo.py` (130 lines) - Task tracking
- `executor.py` (57 lines) - Retry logic
- `base.py` (51 lines) - Base class
- `__init__.py` (23 lines)

**Test Coverage Target: 85%**

#### Test Strategy

**Unit Tests (~40-45 tests)**

| File | Test Class | Test Cases | Focus |
|------|-----------|-----------|-------|
| base.py | TestBaseTool | 3-4 | Interface contract |
| file_ops.py | TestFileOps | 12-15 | Read/write/edit, permissions, encoding |
| bash.py | TestBashTool | 8-10 | Command execution, timeout, error codes |
| search.py | TestSearchTools | 10-12 | Glob patterns, Grep regex, performance |
| todo.py | TestTodoTool | 6-8 | Task CRUD, status updates, serialization |
| executor.py | TestToolExecutor | 3-4 | Retry logic, exponential backoff |

**Integration Tests (~10-12 tests)**

| Test Scenario | Focus |
|---------------|-------|
| File operations | Create → Read → Edit → Delete full cycle |
| Bash commands | Complex command chains, timeout handling |
| Search across codebase | Find patterns in multiple files |
| Todo persistence | Save/load across sessions |
| Permission enforcement | SAFE/NORMAL/DANGEROUS checks |
| Error handling | Graceful failure of one tool doesn't affect others |

**Key Test Points:**
- ✓ File operations (Read/Write/Edit) all work
- ✓ File permissions respected
- ✓ Bash commands execute correctly
- ✓ Timeout enforcement works (default 30s)
- ✓ Glob patterns match expected files
- ✓ Grep finds all matches in large files
- ✓ Todo state persists correctly
- ✓ Retry logic with exponential backoff (1s, 2s, 4s, 8s)

**Test Data:**
```python
# Use temporary files for file operation tests
@pytest.fixture
def temp_dir(tmp_path):
    yield tmp_path

@pytest.fixture
def sample_codebase(temp_dir):
    # Create sample files for search tests
    (temp_dir / "test.py").write_text("def hello(): pass")
    return temp_dir
```

---

### 4. Hook System (`src/hooks/`) - 1,122 lines | Priority: P1

**Files:**
- `manager.py` (207 lines) - Hook registration & triggering
- `validator.py` (230 lines) - Hook validation
- `secure_loader.py` (222 lines) - Secure code loading
- `config_loader.py` (211 lines) - Load from config files
- `builder.py` (129 lines) - Hook builder
- `types.py` (99 lines) - Hook types
- `__init__.py` (24 lines)

**Test Coverage Target: 85%**

**Status: Already have ~40 tests from test_hooks.py and test_hooks_integration.py**

#### Additional Tests Needed (~15-20)

| Test Area | Test Cases | Focus |
|-----------|-----------|-------|
| Validator | 4-5 | Schema validation, code safety checks |
| SecureLoader | 4-5 | Python code sandbox, import restrictions |
| ConfigLoader | 4-5 | Load hooks from JSON, validation |
| Builder | 3-4 | Hook creation, parameter validation |
| Integration | 4-6 | Real hooks loading and triggering |

**Key Test Points:**
- ✓ All hook event types trigger correctly
- ✓ Handler priority execution order
- ✓ Error in one handler doesn't affect others
- ✓ Hooks load from config files safely
- ✓ Python code in hooks runs in sandbox
- ✓ Dangerous imports are blocked

---

### 5. Event System (`src/events/`) - 193 lines | Priority: P1

**Files:**
- `event_bus.py` (188 lines) - Event pub-sub
- `types.py` (Not found, likely in event_bus.py)
- `__init__.py` (5 lines)

**Test Coverage Target: 80%**

#### Unit Tests (~12-15 tests)

| Test Class | Test Cases | Focus |
|-----------|-----------|-------|
| TestEventBus | 8-10 | Subscribe, publish, unsubscribe, priority |
| TestEventTypes | 3-4 | Event enum validation |
| Integration | 3-4 | Real event flow scenarios |

**Key Test Points:**
- ✓ Event subscription works
- ✓ Event publishing triggers all subscribers
- ✓ Subscriber removal works
- ✓ Event priority ordering
- ✓ Multiple subscribers per event
- ✓ Async event handlers

---

### 6. Commands (`src/commands/`) - 725 lines | Priority: P1

**Files:**
- `builtin.py` (170 lines)
- `workspace_commands.py` (181 lines)
- `persistence_commands.py` (156 lines)
- `base.py` (116 lines)
- `output_commands.py` (48 lines)
- `__init__.py` (54 lines)

**Test Coverage Target: 75%**

#### Unit Tests (~20-25 tests)

| Test Area | Test Cases | Focus |
|-----------|-----------|-------|
| Base | 3-4 | Command interface, argument parsing |
| Builtin | 6-8 | /help, /status, /exit |
| Workspace | 6-8 | /save, /load, /clear |
| Persistence | 4-5 | Conversation management |
| Output | 3-4 | /quiet, output formatting |

**Key Test Points:**
- ✓ All commands parse arguments correctly
- ✓ Commands execute without errors
- ✓ Output formatting is correct
- ✓ File operations (save/load) work
- ✓ Conversation state preserved

---

### 7. Utils (`src/utils/`) - 593 lines | Priority: P2

**Files:**
- `input.py` (320 lines) - Prompt-Toolkit input
- `output.py` (261 lines) - Rich output
- `formatting.py` (12 lines)

**Test Coverage Target: 70%**

#### Unit Tests (~15-18 tests)

| Test Area | Test Cases | Focus |
|-----------|-----------|-------|
| Input (input.py) | 6-8 | History, autocomplete, async input |
| Output (output.py) | 6-8 | Markdown detection, syntax highlighting |
| Formatting | 2-3 | Text formatting utilities |

**Key Test Points:**
- ✓ Input history persists
- ✓ Autocomplete suggestions work
- ✓ Markdown is detected and rendered
- ✓ Code blocks highlighted correctly
- ✓ Output colors applied

---

### 8. MCP Integration (`src/mcps/`) - 153 lines | Priority: P2

**Files:**
- `client.py` (121 lines)
- `config.py` (22 lines)

**Test Coverage Target: 70%**

#### Unit Tests (~6-8 tests)

| Test Area | Test Cases | Focus |
|-----------|-----------|-------|
| MCP Client | 4-5 | Server connection, tool listing |
| MCP Config | 2-3 | Configuration loading |

---

### 9. Prompts (`src/prompts/`) - 306 lines | Priority: P2

**Files:**
- `system.py` (129 lines)
- `roles.py` (82 lines)
- `summarization.py` (57 lines)

**Test Coverage Target: 65%**

#### Unit Tests (~8-10 tests)

| Test Area | Test Cases | Focus |
|-----------|-----------|-------|
| System prompts | 3-4 | Prompt generation, variable substitution |
| Roles | 2-3 | Role prompt formatting |
| Summarization | 2-3 | Summary generation logic |

---

## Testing Infrastructure

### Test File Organization

```
tests/
├── conftest.py                 # Shared fixtures, configuration
├── pytest.ini                  # Pytest configuration
├── fixtures/                   # Test data
│   ├── sample_config.json
│   ├── sample_messages.json
│   └── sample_code/
├── unit/
│   ├── test_agent_state.py            # 8 tests
│   ├── test_agent_context.py          # 10 tests
│   ├── test_agent_tools.py            # 8 tests
│   ├── test_agent_permission.py       # 10 tests
│   ├── test_agent_feedback.py         # 5 tests
│   ├── test_clients_base.py           # 5 tests
│   ├── test_clients_anthropic.py      # 10 tests
│   ├── test_clients_openai.py         # 10 tests
│   ├── test_clients_google.py         # 8 tests
│   ├── test_clients_factory.py        # 5 tests
│   ├── test_tools_file_ops.py         # 15 tests
│   ├── test_tools_bash.py             # 10 tests
│   ├── test_tools_search.py           # 12 tests
│   ├── test_tools_todo.py             # 8 tests
│   ├── test_tools_executor.py         # 4 tests
│   ├── test_events_bus.py             # 10 tests
│   ├── test_commands.py               # 20 tests
│   ├── test_utils_input.py            # 8 tests
│   ├── test_utils_output.py           # 8 tests
│   ├── test_mcps.py                   # 8 tests
│   └── test_prompts.py                # 10 tests
├── integration/
│   ├── test_agent_workflow.py         # 8 tests
│   ├── test_tool_execution.py         # 6 tests
│   ├── test_client_switching.py       # 4 tests
│   ├── test_command_flow.py           # 4 tests
│   ├── test_hook_system.py            # 6 tests (plus existing)
│   ├── test_event_flow.py             # 4 tests
│   └── test_permission_flow.py        # 4 tests
└── e2e/
    ├── test_complete_conversation.py  # 5 tests
    ├── test_tool_chain.py             # 3 tests
    └── test_error_recovery.py         # 2 tests
```

### Pytest Configuration (pytest.ini)

```ini
[pytest]
# Async support
asyncio_mode = auto

# Coverage
addopts = --cov=src --cov-report=html --cov-report=term-missing

# Markers
markers =
    asyncio: marks tests as async
    integration: marks tests as integration tests
    slow: marks tests as slow running

# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Timeout
timeout = 30

# Logging
log_cli = false
log_level = INFO
```

### Fixtures (conftest.py)

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.agents import AgentState
from src.tools.base import BaseTool

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    # Implementation

@pytest.fixture
async def mock_llm_client():
    """Mock LLM client"""
    # Implementation

@pytest.fixture
def temp_test_dir(tmp_path):
    """Temporary test directory"""
    yield tmp_path

@pytest.fixture
def sample_messages():
    """Sample conversation messages"""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"}
    ]

@pytest.fixture
def mock_tool():
    """Mock tool for testing"""
    tool = Mock(spec=BaseTool)
    tool.name = "test_tool"
    return tool
```

---

## Testing Commands

### Run all tests
```bash
pytest tests/
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html tests/
```

### Run specific category
```bash
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest tests/e2e/            # E2E tests only
```

### Run specific module
```bash
pytest tests/unit/test_agent_state.py
pytest tests/integration/test_agent_workflow.py
```

### Run with verbose output
```bash
pytest -v tests/
```

### Run and stop on first failure
```bash
pytest -x tests/
```

---

## Coverage Goals & Metrics

### Target by Module

| Module | Target | Priority | Current |
|--------|--------|----------|---------|
| agents/ | 85% | P0 | 0% |
| clients/ | 80% | P0 | 0% |
| tools/ | 85% | P0 | 0% |
| hooks/ | 85% | P1 | ~60% |
| events/ | 80% | P1 | 0% |
| commands/ | 75% | P1 | 0% |
| utils/ | 70% | P2 | 0% |
| mcps/ | 70% | P2 | 0% |
| prompts/ | 65% | P2 | 0% |
| **Overall** | **80%** | **-** | **~5%** |

### Success Criteria

- [ ] 140+ test cases across all modules
- [ ] 80%+ overall code coverage
- [ ] 85%+ coverage for P0 modules (agents, clients, tools)
- [ ] All tests pass consistently
- [ ] Test execution < 60 seconds
- [ ] Zero known bugs in core modules

---

## Implementation Roadmap

### Week 1: Infrastructure & Unit Tests
- [ ] Set up conftest.py with fixtures
- [ ] Create pytest.ini configuration
- [ ] Write ~40 unit tests for agents/ module

### Week 2: Continue Unit Tests
- [ ] ~30 tests for clients/ module
- [ ] ~45 tests for tools/ module
- [ ] ~20 tests for events/ module

### Week 3: Integration & Commands
- [ ] ~20 tests for hooks/ integration
- [ ] ~25 tests for commands/
- [ ] ~20 tests for utils/

### Week 4: E2E & Polish
- [ ] ~10 E2E test scenarios
- [ ] Fix coverage gaps
- [ ] Documentation and CI/CD setup

---

## Continuous Integration

### GitHub Actions Setup
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt pytest pytest-cov pytest-asyncio
      - run: pytest --cov=src --cov-report=xml tests/
      - uses: codecov/codecov-action@v2
```

---

## Benefits of This Testing Strategy

1. **Comprehensive Coverage** (80%+)
   - Catches bugs early
   - Prevents regressions
   - Builds confidence in quality

2. **Organized & Maintainable**
   - Clear test structure
   - Easy to add new tests
   - Simple to debug failures

3. **Fast Feedback Loop**
   - Tests run in ~45 seconds
   - Developers get quick feedback
   - Easy to run before commits

4. **Documentation**
   - Tests serve as usage examples
   - Show expected behavior
   - Help onboard new contributors

5. **Trust & Adoption**
   - Users see 80%+ coverage
   - Confidence in stability
   - More likely to use/contribute

---

**Last Updated:** 2025-01-13
**Total Estimated Test Cases:** ~140
**Estimated Coverage:** 80%+
**Estimated Execution Time:** ~45 seconds
