# Development Guide

This document contains all information for contributing code to the Build Your Own Claude Code project.

## Table of Contents

- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Extending the Project](#extending-the-project)
- [Testing](#testing)
- [Contribution Process](#contribution-process)

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Create a new branch for feature development
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/your-bugfix-name
```

### 2. Development and Testing

```bash
# Install development dependencies in a virtual environment
pip install -r requirements.txt
pip install -e .

# Run the application
python -m src.main

# Run tests
pytest tests/
```

### 3. Code Review and Commit

- Ensure code has complete type hints and docstrings
- Add corresponding tests
- Update relevant documentation
- Create a Pull Request

---

## Code Style Guidelines

### File Organization

- **One class per file** - Main components (managers, clients) should each be in separate files
- **Manager suffix** - Management classes use the Manager suffix (StateManager, ToolManager)
- **Base prefix** - Abstract classes use the Base prefix (BaseClient, BaseTool)
- **Private methods** - Use underscore prefix (`_internal_method`)
- **Constants** - Use uppercase (`UPPER_CASE`)

### Type Hints

All functions should have complete type hints:

```python
from typing import Optional, List, Dict

async def process_message(
    message: str,
    options: Optional[Dict[str, str]] = None
) -> bool:
    """Process a message.

    Args:
        message: Input message
        options: Optional processing options

    Returns:
        Whether the message was processed successfully
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_tokens(text: str, model: str = "claude-3-sonnet") -> int:
    """Calculate the number of tokens in text.

    Uses the tokenizer for the specified model to calculate the number of tokens.
    Supports multiple Claude models.

    Args:
        text: Input text
        model: Model name to use, defaults to claude-3-sonnet

    Returns:
        The calculated number of tokens

    Raises:
        ValueError: If the model is not supported
        RuntimeError: If tokenizer initialization fails

    Example:
        >>> tokens = calculate_tokens("Hello world")
        >>> print(tokens)
        3
    """
    pass
```

### Error Handling

Use meaningful error messages:

```python
try:
    result = await client.create_message(messages)
except ValueError as e:
    logger.error(f"Invalid message format: {e}")
    raise
except RuntimeError as e:
    logger.error(f"API call failed: {e}")
    raise
```

---

## Extending the Project

### Adding a New Tool

1. **Create a new tool class**:

```python
# src/tools/my_tool.py
from src.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    """Description of the custom tool.

    Explains what this tool does and why it is needed.
    """

    @property
    def name(self) -> str:
        """Tool name"""
        return "my_tool"

    @property
    def description(self) -> str:
        """Tool description"""
        return "Brief description of what this tool does"

    @property
    def schema(self) -> dict:
        """Parameter schema for the tool"""
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter 1"
                }
            },
            "required": ["param1"]
        }

    async def execute(self, **params) -> ToolResult:
        """Execute the tool.

        Args:
            **params: Parameters defined according to the schema

        Returns:
            ToolResult containing the execution result
        """
        try:
            # Implement tool logic
            result = await self._do_something(params)
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _do_something(self, params: dict) -> str:
        """Concrete implementation"""
        pass
```

2. **Register the tool**:

Register the new tool in the tool manager in `src/tools/`.

### Adding a New LLM Provider

1. **Create a client class**:

```python
# src/clients/my_provider.py
from src.clients.base import BaseClient, Message

class MyProviderClient(BaseClient):
    """MyProvider LLM client implementation."""

    def __init__(self, api_key: str, model: str = "default-model"):
        """Initialize the client."""
        self.api_key = api_key
        self.model = model

    async def create_message(
        self,
        messages: List[Message],
        tools: Optional[List[dict]] = None,
        **kwargs
    ) -> str:
        """Create a message and get a response.

        Args:
            messages: Message history
            tools: Available tool definitions
            **kwargs: Additional parameters

        Returns:
            The model's response text
        """
        # Implement API call
        pass
```

2. **Register in the factory**:

Register the new client in `src/clients/factory.py`.

### Adding a New Command

1. **Create a command class**:

```python
# src/commands/my_command.py
from src.commands.base import Command

class MyCommand(Command):
    """Description of the custom command."""

    @property
    def name(self) -> str:
        return "mycommand"

    @property
    def description(self) -> str:
        return "Brief description of this command"

    @property
    def help(self) -> str:
        return """Usage: /mycommand [args]

Options:
    --option1    Description
    --option2    Description
"""

    async def execute(self, args: str, context) -> str:
        """Execute the command.

        Args:
            args: Command arguments
            context: Application context

        Returns:
            Command output
        """
        # Implement command logic
        return "Command output"
```

2. **Register the command**:

Register the new command in the command registry.

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_hooks.py

# Run a specific test function
pytest tests/test_hooks.py::test_hook_execution

# Run with coverage report
pytest --cov=src tests/

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/
```

### Writing Tests

```python
# tests/test_my_feature.py
import pytest
from src.my_module import MyClass

@pytest.fixture
def my_instance():
    """Create a test instance"""
    return MyClass()

def test_basic_functionality(my_instance):
    """Test basic functionality"""
    result = my_instance.do_something()
    assert result == expected_value

@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality"""
    result = await async_function()
    assert result is not None
```

---

## Contribution Process

### 1. Fork the Project

Click the "Fork" button on GitHub.

### 2. Clone Your Fork

```bash
git clone https://github.com/your-username/build-your-own-claude-code.git
cd build-your-own-claude-code
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Implement the Feature

- Write code
- Add type hints and docstrings
- Add tests

### 5. Commit Changes

```bash
git add .
git commit -m "Add: brief description of changes"
```

Follow the commit message format below:

- `Add:` - New feature
- `Fix:` - Bug fix
- `Refactor:` - Code refactoring
- `Docs:` - Documentation update
- `Test:` - Add/modify tests

### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 7. Create a Pull Request

Create a Pull Request on GitHub with a description of:

- What changes were made
- Why this change is needed
- How to test the changes

### 8. Await Review

Maintainers will review your code and may request some improvements.

---

## Common Development Tasks

### Running the Application in Various Modes

```bash
# Basic run
python -m src.main

# Verbose mode (show tool details and thinking process)
python -m src.main --verbose

# Quiet mode (show only errors and agent responses)
python -m src.main --quiet

# Custom configuration file
python -m src.main --config my-~/.tiny-claude-code/settings.json

# Skip permission checks (dangerous! for development only)
python -m src.main --dangerously-skip-permissions
```

### Building and Packaging

```bash
# Install in development mode
pip install -e .

# Build distribution packages
python setup.py sdist bdist_wheel

# Install from built package
pip install dist/build-your-own-claude-code-0.1.0.tar.gz
```

### MCP Integration Development

Configure MCP servers in `~/.tiny-claude-code/settings.json`:

```json
{
  "mcp_servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "enabled": true
    }
  ]
}
```

### Hook System Development

Define hooks in `~/.tiny-claude/settings.json` or `.tiny-claude/settings.json` in the project directory:

```json
{
  "hooks": [
    {
      "event": "on_tool_execute",
      "type": "command",
      "command": "echo 'Tool executed: {tool_name}'",
      "priority": 10
    }
  ]
}
```

---

## Troubleshooting

### No API Provider Configured

**Symptoms**: Runtime error "No API provider configured"

**Solution**:
1. Set environment variable: `export ANTHROPIC_API_KEY="your-key"`
2. Or configure in `.env` file
3. Or configure in `~/.tiny-claude-code/settings.json`
4. Ensure provider package is installed: `pip install anthropic`

### MCP Servers Cannot Load

**Symptoms**: MCP server list is empty or loading fails

**Solution**:
1. Verify MCP package is installed: `pip install mcp`
2. Check the MCP server command and parameters in `~/.tiny-claude-code/settings.json`
3. Ensure Node.js is installed (if using npx)
4. Run `python -m src.main --verbose` to see detailed errors

### Context Window Exceeded

**Symptoms**: Runtime error "Context window exceeded"

**Solution**:
1. Use `/clear` command to clear conversation history
2. Adjust `max_context_tokens` configuration in `~/.tiny-claude-code/settings.json`
3. Use `/save` to save the current conversation, then `/clear` to start a new one

### Tool Execution Fails

**Symptoms**: Tool execution errors, typically from file operations or command execution

**Solution**:
1. Check file permissions
2. Verify tool parameters match the schema
3. Use `--verbose` flag to see detailed error messages
4. Check `/status` command to view the tool list

### Asyncio-Related Errors

**Symptoms**: "asyncio.run() cannot be called from a running event loop"

**Solution**:
1. Ensure you use `async_get_input()` instead of the synchronous `get_input()`
2. See [hotfixes/v2025.01.13/1-fix-asyncio-loop.md](./hotfixes/v2025.01.13/1-fix-asyncio-loop.md)

### Command Autocomplete Not Working

**Symptoms**: Tab completion is unresponsive or autocompletes incorrectly

**Solution**:
1. Ensure commands start with "/"
2. See [hotfixes/v2025.01.13/2-fix-tab-autocomplete.md](./hotfixes/v2025.01.13/2-fix-tab-autocomplete.md)
3. Restart the application

---

**Last Updated**: 2025-01-13
**Contributors**: All contributions are welcome!