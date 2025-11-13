# Testing Requirements

Testing dependencies for running the test suite.

## Installation

Install testing dependencies:

```bash
pip install pytest>=7.0.0
pip install pytest-asyncio>=0.21.0
pip install pytest-cov>=4.0.0
pip install pytest-timeout>=2.1.0
```

Or install all at once:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-timeout
```

## Verification

Verify the test setup:

```bash
# Check pytest installation
pytest --version

# Run the example test
pytest tests/unit/test_agent_state_example.py -v

# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html
```

## Test Structure

After setup, you should have:

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── pytest.ini                     # Pytest settings
├── __init__.py
├── unit/                          # Unit tests (to be added)
│   ├── __init__.py
│   └── test_agent_state_example.py  # Example test file
├── integration/                   # Integration tests (to be added)
│   └── __init__.py
├── e2e/                          # E2E tests (to be added)
│   └── __init__.py
├── fixtures/                      # Test data (to be added)
│   └── __init__.py
├── test_hooks.py                 # Existing test
└── test_hooks_integration.py      # Existing test
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with coverage report
```bash
pytest --cov=src --cov-report=html tests/
```

### Run specific test file
```bash
pytest tests/unit/test_agent_state_example.py
```

### Run only unit tests
```bash
pytest tests/unit/ -m unit
```

### Run only integration tests
```bash
pytest tests/integration/ -m integration
```

### Run with verbose output
```bash
pytest -v tests/
```

### Run and stop on first failure
```bash
pytest -x tests/
```

### Run async tests only
```bash
pytest -m asyncio tests/
```

## Available Fixtures

The `conftest.py` provides these fixtures:

### Temporary Files
- `temp_test_dir` - Temporary directory for test files
- `sample_python_file` - Sample Python file
- `sample_markdown_file` - Sample Markdown file
- `sample_json_config` - Sample JSON config

### Mock Data
- `sample_messages` - Conversation messages
- `sample_tool_use_message` - Message with tool use
- `sample_agent_config` - Agent configuration
- `sample_hook_config` - Hook configuration

### Mock Clients
- `mock_llm_client` - Mock LLM client
- `mock_anthropic_client` - Mock Anthropic client
- `mock_openai_client` - Mock OpenAI client
- `mock_google_client` - Mock Google Gemini client

### Mock Tools
- `mock_read_tool` - Mock Read tool
- `mock_bash_tool` - Mock Bash tool
- `mock_grep_tool` - Mock Grep tool
- `sample_tools` - Collection of mock tools

### Mock Components
- `mock_agent_state` - Mock agent state
- `mock_context_manager` - Mock context manager
- `mock_tool_manager` - Mock tool manager
- `mock_permission_manager` - Mock permission manager
- `mock_hook_manager` - Mock hook manager
- `mock_hook_context` - Mock hook context
- `mock_event_bus` - Mock event bus

### Utilities
- `assert_valid_json` - JSON validation helper
- `capture_logs` - Log capturing utility

## Example Usage

### Using fixtures in tests

```python
@pytest.mark.unit
def test_with_fixtures(mock_agent_state, sample_messages):
    """Example test using fixtures"""
    assert mock_agent_state.model == "claude-sonnet-4.5"
    assert len(sample_messages) == 3
```

### Testing async code

```python
@pytest.mark.asyncio
async def test_async_function():
    """Example async test"""
    result = await some_async_function()
    assert result is not None
```

### Testing with temporary files

```python
def test_with_temp_files(temp_test_dir):
    """Example test using temporary directory"""
    test_file = temp_test_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.read_text() == "test content"
```

## Next Steps

1. Install test dependencies (see above)
2. Run example test: `pytest tests/unit/test_agent_state_example.py`
3. Read through `conftest.py` to understand available fixtures
4. Start writing tests following the patterns in `test_agent_state_example.py`

## Coverage Reports

After running tests with coverage:

```bash
# View HTML coverage report
open htmlcov/index.html
```

The report shows:
- Overall coverage percentage
- File-by-file coverage
- Line-by-line coverage details
- Missing coverage highlighted

## CI/CD Integration

To set up automatic testing on git commits:

```bash
# Install pre-commit hook
pip install pre-commit

# Create .pre-commit-config.yaml with pytest hook
# Then run: pre-commit install
```

See docs/testing_strategy.md for GitHub Actions setup.
