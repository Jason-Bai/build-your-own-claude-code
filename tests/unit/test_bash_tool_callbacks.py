"""Unit tests for BashTool error handling"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from src.tools.bash import BashTool
from src.tools.base import ToolResult


@pytest.mark.asyncio
async def test_bash_tool_callback_exception_handling():
    """Test that exceptions in on_chunk callback don't interrupt execution"""
    tool = BashTool()

    # Create a callback that raises an exception
    callback_calls = []

    async def failing_callback(chunk: str):
        callback_calls.append(chunk)
        if len(callback_calls) == 1:
            raise ValueError("Simulated callback error")
        # Second call should still work

    # Execute a command with failing callback
    result = await tool.execute(
        command='echo "Line 1" && echo "Line 2"',
        on_chunk=failing_callback
    )

    # Tool should still succeed despite callback error
    assert result.success
    assert "Line 1" in result.output
    assert "Line 2" in result.output

    # Callback should have been called multiple times
    assert len(callback_calls) >= 2


@pytest.mark.asyncio
async def test_bash_tool_callback_no_error_propagation():
    """Test that callback errors are logged but don't affect tool result"""
    tool = BashTool()

    async def always_failing_callback(chunk: str):
        raise RuntimeError("Always fails")

    # Execute command
    result = await tool.execute(
        command='echo "Success"',
        on_chunk=always_failing_callback
    )

    # Tool should still report success
    assert result.success
    assert "Success" in result.output


@pytest.mark.asyncio
async def test_bash_tool_timeout_handling():
    """Test that timeout is properly handled"""
    tool = BashTool()

    chunks_received = []

    async def chunk_callback(chunk: str):
        chunks_received.append(chunk)

    # Command that sleeps longer than timeout
    result = await tool.execute(
        command='sleep 10',
        on_chunk=chunk_callback,
        timeout=100  # 100ms timeout
    )

    # Should fail with timeout error
    assert not result.success
    assert "timed out" in result.error.lower()


@pytest.mark.asyncio
async def test_bash_tool_streaming_with_callback():
    """Test that streaming works correctly with callback"""
    tool = BashTool()

    chunks = []

    async def collect_chunks(chunk: str):
        chunks.append(chunk)

    # Execute a command that produces multiple lines
    result = await tool.execute(
        command='for i in 1 2 3; do echo "Line $i"; done',
        on_chunk=collect_chunks
    )

    # Should succeed
    assert result.success

    # Should have received multiple chunks
    assert len(chunks) >= 3

    # All lines should be in the final output
    assert "Line 1" in result.output
    assert "Line 2" in result.output
    assert "Line 3" in result.output


@pytest.mark.asyncio
async def test_bash_tool_no_callback():
    """Test that tool works without callback"""
    tool = BashTool()

    result = await tool.execute(command='echo "Test"')

    assert result.success
    assert "Test" in result.output
