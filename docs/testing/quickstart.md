# Testing Quick Start Guide

Get started with testing in under 5 minutes.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov pytest-timeout
```

### 2. Run All Tests

```bash
pytest tests/unit/ -v
```

Expected output: **359 passed** ✅

### 3. View Coverage Report

```bash
pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html  # macOS
```

---

## 📋 Common Commands

| Command                                  | Description                |
| ---------------------------------------- | -------------------------- |
| `pytest tests/unit/`                     | Run all unit tests         |
| `pytest tests/unit/ -v`                  | Verbose output             |
| `pytest tests/unit/ -x`                  | Stop on first failure      |
| `pytest tests/unit/ --cov=src`           | Show coverage              |
| `pytest tests/unit/test_hook_manager.py` | Run specific file          |
| `pytest -k "test_agent"`                 | Run tests matching pattern |

---

## ✍️ Writing Your First Test

### Step 1: Create Test File

Create `tests/unit/test_my_module.py`:

```python
import pytest
from src.my_module import MyClass

@pytest.mark.unit
class TestMyClass:
    """Tests for MyClass"""

    def test_initialization(self):
        """Test MyClass initialization"""
        obj = MyClass(param="value")
        assert obj.param == "value"

    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async method"""
        obj = MyClass()
        result = await obj.async_method()
        assert result is not None
```

### Step 2: Run Your Test

```bash
pytest tests/unit/test_my_module.py -v
```

---

## 🔧 Using Fixtures

Over 30+ reusable fixtures available in `tests/conftest.py`:

```python
@pytest.mark.unit
class TestWithFixtures:
    """Example using fixtures"""

    def test_with_mock_agent(self, mock_agent_state):
        """Use pre-configured mock agent"""
        assert mock_agent_state.status == "IDLE"

    def test_with_sample_data(self, sample_messages):
        """Use sample conversation data"""
        assert len(sample_messages) == 3

    def test_with_temp_dir(self, temp_test_dir):
        """Use temporary directory"""
        test_file = temp_test_dir / "test.txt"
        test_file.write_text("content")
        assert test_file.exists()
```

### Available Fixtures

**Mock Objects:**

- `mock_agent_state` - Agent state machine
- `mock_context_manager` - Context manager
- `mock_tool_manager` - Tool manager
- `mock_llm_client` - LLM client

**Sample Data:**

- `sample_messages` - Conversation messages
- `sample_agent_config` - Agent configuration
- `sample_tools` - Tool collections

**File Operations:**

- `temp_test_dir` - Temporary directory
- `sample_python_file` - Python file example

See `tests/conftest.py` for complete list.

---

## 🐛 Debugging Tests

### Show Print Output

```bash
pytest -s tests/unit/test_my.py
```

### Verbose Failures

```bash
pytest -vv tests/unit/test_my.py
```

### Use Debugger

```python
def test_with_debugger():
    x = 10
    import pdb; pdb.set_trace()  # Pause here
    assert x == 10
```

### Skip Tests

```python
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.xfail
def test_known_bug():
    # Expected to fail
    pass
```

---

## 📊 Test Organization

Current test structure:

```
tests/
├── conftest.py           # Shared fixtures (30+)
├── pytest.ini            # Pytest configuration
└── unit/                 # 359 unit tests
    ├── test_agent_state.py              (53 tests)
    ├── test_agent_context.py            (63 tests)
    ├── test_agent_tool_manager.py       (38 tests)
    ├── test_agent_permission_manager.py (39 tests)
    ├── test_llm_clients.py              (42 tests)
    ├── test_tool_system.py              (47 tests)
    ├── test_hooks_types.py              (24 tests)
    └── test_hook_manager.py             (39 tests)
```

---

## 💡 Best Practices

### 1. Test Structure

```python
class TestMyFeature:
    """Group related tests"""

    def test_successful_case(self):
        """Test the happy path"""
        pass

    def test_error_handling(self):
        """Test error scenarios"""
        pass

    def test_edge_cases(self):
        """Test boundary conditions"""
        pass
```

### 2. Descriptive Names

```python
# Good
def test_agent_transitions_from_idle_to_thinking():
    pass

# Bad
def test_agent():
    pass
```

### 3. Clear Assertions

```python
# Good
assert result.status == "COMPLETED"
assert len(results) == 5

# Bad
assert result
assert results
```

### 4. Use Markers

```python
@pytest.mark.unit          # Unit test
@pytest.mark.asyncio       # Async test
@pytest.mark.slow          # Slow running test
```

---

## 🎯 Coverage Goals

Target coverage by module:

- **High Coverage (>80%)**: agents, clients, tools, hooks
- **Good Coverage (60-80%)**: events, commands
- **Basic Coverage (>50%)**: utils, prompts

Current overall coverage: **34%**

---

## 📚 Next Steps

1. **Explore existing tests** - Read `tests/unit/test_hook_manager.py` for examples
2. **Check coverage** - Run `pytest --cov=src --cov-report=html`
3. **Write tests for new features** - Follow TDD approach
4. **Read full summary** - See [summary.md](./summary.md)

---

## ❓ Common Issues

**Q: Tests fail with "import error"**

```bash
# Make sure you're in project root
cd /path/to/build-your-own-claude-code
pytest tests/unit/
```

**Q: Async tests don't work**

```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

**Q: How to run only fast tests?**

```bash
pytest -m "not slow" tests/unit/
```

**Q: How to see which tests are slow?**

```bash
pytest --durations=10 tests/unit/
```

---

**Last Updated**: 2025-01-14
**Status**: 359 passing tests, 34% coverage ✅
