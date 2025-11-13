"""
Shared pytest configuration and fixtures for all tests

This file provides:
- Async event loop setup
- Mock clients and services
- Sample test data fixtures
- Common utilities for testing
"""

import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, MagicMock
import tempfile
import json

# ============================================================================
# Event Loop & Async Support
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Temporary Directories & Files
# ============================================================================

@pytest.fixture
def temp_test_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_python_file(temp_test_dir: Path) -> Path:
    """Create a sample Python file for testing"""
    test_file = temp_test_dir / "sample.py"
    test_file.write_text("""
def hello(name: str) -> str:
    '''Greet someone'''
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    '''Add two numbers'''
    return a + b

class Calculator:
    def multiply(self, a: int, b: int) -> int:
        return a * b
""")
    return test_file


@pytest.fixture
def sample_markdown_file(temp_test_dir: Path) -> Path:
    """Create a sample Markdown file for testing"""
    md_file = temp_test_dir / "README.md"
    md_file.write_text("""
# Test Project

## Overview
This is a test project.

## Features
- Feature 1
- Feature 2

## Code Example
\`\`\`python
def test():
    pass
\`\`\`
""")
    return md_file


@pytest.fixture
def sample_json_config(temp_test_dir: Path) -> Path:
    """Create a sample JSON config file for testing"""
    config_file = temp_test_dir / "config.json"
    config_data = {
        "model": {
            "provider": "anthropic",
            "ANTHROPIC_MODEL": "claude-sonnet-4.5"
        },
        "ui": {
            "output_level": "normal"
        }
    }
    config_file.write_text(json.dumps(config_data, indent=2))
    return config_file


# ============================================================================
# Mock Data: Messages & Conversations
# ============================================================================

@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing"""
    return [
        {
            "role": "user",
            "content": "Hello, what can you do?"
        },
        {
            "role": "assistant",
            "content": "I can help you with coding tasks, writing, analysis, and more."
        },
        {
            "role": "user",
            "content": "Can you write a Python function?"
        }
    ]


@pytest.fixture
def sample_tool_use_message():
    """Sample message with tool use"""
    return {
        "role": "assistant",
        "content": "I'll help you read that file.",
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "read_file",
                    "arguments": '{"path": "/tmp/test.py"}'
                }
            }
        ]
    }


# ============================================================================
# Mock LLM Clients
# ============================================================================

@pytest.fixture
def mock_anthropic_response():
    """Mock response from Anthropic API"""
    return {
        "id": "msg-123",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "This is a test response from Claude."
            }
        ],
        "model": "claude-sonnet-4.5",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50
        }
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    client = AsyncMock()
    client.create_message = AsyncMock(return_value="Mock response from LLM")
    client.get_model_info = Mock(return_value={
        "model": "claude-sonnet-4.5",
        "provider": "anthropic",
        "max_tokens": 200000
    })
    client.estimate_tokens = Mock(return_value=100)
    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    client = AsyncMock()
    client.create_message = AsyncMock(
        return_value="Mock response from OpenAI"
    )
    client.get_model_info = Mock(return_value={
        "model": "gpt-4",
        "provider": "openai",
        "max_tokens": 128000
    })
    return client


@pytest.fixture
def mock_google_client():
    """Mock Google Gemini client for testing"""
    client = AsyncMock()
    client.create_message = AsyncMock(
        return_value="Mock response from Google"
    )
    client.get_model_info = Mock(return_value={
        "model": "gemini-pro",
        "provider": "google",
        "max_tokens": 32000
    })
    return client


# ============================================================================
# Mock Tools
# ============================================================================

@pytest.fixture
def mock_read_tool():
    """Mock Read tool for testing"""
    tool = AsyncMock()
    tool.name = "read"
    tool.description = "Read file contents"
    tool.permission_level = "SAFE"
    tool.execute = AsyncMock(return_value={
        "success": True,
        "output": "File contents here"
    })
    return tool


@pytest.fixture
def mock_bash_tool():
    """Mock Bash tool for testing"""
    tool = AsyncMock()
    tool.name = "bash"
    tool.description = "Execute bash commands"
    tool.permission_level = "NORMAL"
    tool.execute = AsyncMock(return_value={
        "success": True,
        "output": "Command output",
        "exit_code": 0
    })
    return tool


@pytest.fixture
def mock_grep_tool():
    """Mock Grep tool for testing"""
    tool = AsyncMock()
    tool.name = "grep"
    tool.description = "Search file contents"
    tool.permission_level = "SAFE"
    tool.execute = AsyncMock(return_value={
        "success": True,
        "output": ["file.py:10: matching line"]
    })
    return tool


@pytest.fixture
def sample_tools(mock_read_tool, mock_bash_tool, mock_grep_tool):
    """Sample set of tools for testing"""
    return {
        "read": mock_read_tool,
        "bash": mock_bash_tool,
        "grep": mock_grep_tool
    }


# ============================================================================
# Mock Agent State & Context
# ============================================================================

@pytest.fixture
def mock_agent_state():
    """Mock agent state for testing"""
    state = Mock()
    state.model = "claude-sonnet-4.5"
    state.status = "IDLE"
    state.current_tool = None
    state.token_count = 0
    state.total_tokens_used = 0
    state.tool_calls_count = 0
    state.errors_count = 0
    return state


@pytest.fixture
def mock_context_manager():
    """Mock context manager for testing"""
    manager = AsyncMock()
    manager.messages = []
    manager.add_message = AsyncMock()
    manager.get_token_count = Mock(return_value=1000)
    manager.is_context_overflow = Mock(return_value=False)
    manager.compress_context = AsyncMock()
    manager.to_messages = Mock(return_value=[])
    return manager


@pytest.fixture
def mock_tool_manager():
    """Mock tool manager for testing"""
    manager = Mock()
    manager.tools = {}
    manager.register_tool = Mock()
    manager.unregister_tool = Mock()
    manager.get_tool = Mock()
    manager.get_tools_list = Mock(return_value=[])
    manager.execute_tool = AsyncMock()
    return manager


@pytest.fixture
def mock_permission_manager():
    """Mock permission manager for testing"""
    manager = Mock()
    manager.check_permission = Mock(return_value=True)
    manager.set_permission_level = Mock()
    manager.get_permission_level = Mock(return_value="NORMAL")
    return manager


# ============================================================================
# Mock Hook System
# ============================================================================

@pytest.fixture
def mock_hook_manager():
    """Mock hook manager for testing"""
    manager = AsyncMock()
    manager.register = Mock(return_value=lambda: None)  # Returns unregister function
    manager.trigger = AsyncMock()
    manager.unregister = Mock(return_value=True)
    manager.get_handlers_count = Mock(return_value=0)
    manager.clear_handlers = Mock()
    manager.get_stats = Mock(return_value={})
    return manager


@pytest.fixture
def mock_hook_context():
    """Mock hook context for testing"""
    context = Mock()
    context.event = "on_user_input"
    context.timestamp = 1234567890.0
    context.data = {"input": "test"}
    context.request_id = "req-123"
    context.agent_id = "agent-456"
    context.user_id = "user-789"
    context.metadata = {}
    context.to_dict = Mock(return_value={
        "event": "on_user_input",
        "timestamp": 1234567890.0,
        "data": {"input": "test"}
    })
    return context


# ============================================================================
# Mock Event Bus
# ============================================================================

@pytest.fixture
def mock_event_bus():
    """Mock event bus for testing"""
    bus = AsyncMock()
    bus.subscribe = Mock(return_value=lambda: None)  # Returns unsubscribe function
    bus.publish = AsyncMock()
    bus.unsubscribe = Mock()
    bus.get_subscribers_count = Mock(return_value=0)
    return bus


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def sample_agent_config():
    """Sample agent configuration"""
    return {
        "model": {
            "provider": "anthropic",
            "ANTHROPIC_API_KEY": "test-key",
            "ANTHROPIC_MODEL": "claude-sonnet-4.5"
        },
        "permissions": {
            "default": "NORMAL",
            "auto_approve_safe": True
        },
        "ui": {
            "output_level": "normal"
        }
    }


@pytest.fixture
def sample_hook_config():
    """Sample hook configuration"""
    return {
        "hooks": [
            {
                "event": "on_user_input",
                "type": "command",
                "command": "echo 'User input received'",
                "priority": 10
            },
            {
                "event": "on_tool_execute",
                "type": "command",
                "command": "echo 'Tool executed: {tool_name}'",
                "priority": 5
            }
        ]
    }


# ============================================================================
# Utility Functions for Testing
# ============================================================================

@pytest.fixture
def assert_valid_json():
    """Fixture providing JSON validation helper"""
    def _validate(text: str) -> dict:
        """Validate and parse JSON"""
        return json.loads(text)
    return _validate


@pytest.fixture
def capture_logs():
    """Fixture for capturing log output during tests"""
    import logging
    from io import StringIO

    def _capture(logger_name: str = None):
        logger = logging.getLogger(logger_name)
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger.addHandler(handler)
        return log_stream

    return _capture


# ============================================================================
# Cleanup & Teardown
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically clean up after each test"""
    yield
    # Add any global cleanup here if needed


# ============================================================================
# Markers for Test Organization
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "skip_ci: mark test to skip in CI"
    )


# ============================================================================
# Helper Functions
# ============================================================================

async def wait_for_condition(
    condition_func,
    timeout: int = 5,
    check_interval: float = 0.1
) -> bool:
    """
    Wait for a condition to be true, useful for async tests.

    Args:
        condition_func: A callable that returns True/False
        timeout: Maximum time to wait in seconds
        check_interval: How often to check the condition

    Returns:
        True if condition became true, False if timeout
    """
    elapsed = 0
    while elapsed < timeout:
        if condition_func():
            return True
        await asyncio.sleep(check_interval)
        elapsed += check_interval
    return False


def create_mock_message(role: str, content: str) -> dict:
    """Create a mock message"""
    return {
        "role": role,
        "content": content
    }
