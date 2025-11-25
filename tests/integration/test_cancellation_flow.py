"""Integration tests for Global ESC Monitor cancellation flow"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.utils.cancellation import CancellationToken
from src.sessions.manager import SessionManager
from src.agents.tool_manager import AgentToolManager
from src.tools.base import BaseTool, ToolResult


class SlowTool(BaseTool):
    """Mock tool that runs for a long time"""

    @property
    def name(self) -> str:
        return "slow_tool"

    @property
    def description(self) -> str:
        return "A tool that takes a long time"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "duration": {"type": "number", "description": "Sleep duration"}
            },
            "required": ["duration"]
        }

    async def execute(self, duration: float = 5.0, **kwargs) -> ToolResult:
        """Sleep for specified duration"""
        await asyncio.sleep(duration)
        return ToolResult(success=True, output=f"Slept for {duration}s")


@pytest.mark.asyncio
async def test_tool_execution_cancellation():
    """Test that tool execution can be cancelled"""
    mock_persistence = Mock()
    session_manager = SessionManager(mock_persistence)
    tool_manager = AgentToolManager()
    tool_manager.register_tool(SlowTool())

    # Start new execution
    session_manager.start_new_execution()
    cancellation_token = session_manager.cancellation_token

    # Start tool execution
    task = asyncio.create_task(
        tool_manager.execute_tool(
            "slow_tool",
            {"duration": 5.0},
            cancellation_token=cancellation_token
        )
    )

    # Wait a bit, then cancel
    await asyncio.sleep(0.2)
    session_manager.cancel_all("Test cancellation")

    # Tool should raise CancelledError
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_multiple_tools_cancellation():
    """Test that multiple tool calls can be cancelled"""
    mock_persistence = Mock()
    session_manager = SessionManager(mock_persistence)
    tool_manager = AgentToolManager()
    tool_manager.register_tool(SlowTool())

    # Start new execution
    session_manager.start_new_execution()
    cancellation_token = session_manager.cancellation_token

    # Start multiple tool executions
    task1 = asyncio.create_task(
        tool_manager.execute_tool(
            "slow_tool",
            {"duration": 5.0},
            cancellation_token=cancellation_token
        )
    )
    task2 = asyncio.create_task(
        tool_manager.execute_tool(
            "slow_tool",
            {"duration": 5.0},
            cancellation_token=cancellation_token
        )
    )

    # Wait a bit, then cancel
    await asyncio.sleep(0.2)
    session_manager.cancel_all("Test multi-tool cancellation")

    # Both should raise CancelledError
    with pytest.raises(asyncio.CancelledError):
        await task1

    with pytest.raises(asyncio.CancelledError):
        await task2


@pytest.mark.asyncio
async def test_tool_completes_before_cancellation():
    """Test that fast tools complete before cancellation"""
    mock_persistence = Mock()
    session_manager = SessionManager(mock_persistence)
    tool_manager = AgentToolManager()
    tool_manager.register_tool(SlowTool())

    # Start new execution
    session_manager.start_new_execution()
    cancellation_token = session_manager.cancellation_token

    # Start fast tool execution
    task = asyncio.create_task(
        tool_manager.execute_tool(
            "slow_tool",
            {"duration": 0.1},
            cancellation_token=cancellation_token
        )
    )

    # Wait for tool to complete
    result = await task

    # Cancel after completion (should have no effect)
    session_manager.cancel_all("Late cancellation")

    # Result should be successful
    assert result.success
    assert "Slept for 0.1s" in result.output


@pytest.mark.asyncio
async def test_cancellation_token_isolation_between_executions():
    """Test that cancelling one execution doesn't affect the next"""
    mock_persistence = Mock()
    session_manager = SessionManager(mock_persistence)
    tool_manager = AgentToolManager()
    tool_manager.register_tool(SlowTool())

    # First execution - cancel it
    session_manager.start_new_execution()
    token1 = session_manager.cancellation_token

    task1 = asyncio.create_task(
        tool_manager.execute_tool(
            "slow_tool",
            {"duration": 5.0},
            cancellation_token=token1
        )
    )

    await asyncio.sleep(0.1)
    session_manager.cancel_all("First execution cancelled")

    with pytest.raises(asyncio.CancelledError):
        await task1

    # Second execution - should work fine
    session_manager.start_new_execution()
    token2 = session_manager.cancellation_token

    # Verify new token is not cancelled
    assert not token2.is_cancelled()
    assert token2 is not token1

    task2 = asyncio.create_task(
        tool_manager.execute_tool(
            "slow_tool",
            {"duration": 0.1},
            cancellation_token=token2
        )
    )

    result = await task2
    assert result.success


@pytest.mark.asyncio
async def test_cancellation_during_llm_call():
    """Test that LLM calls can be cancelled (mock test)"""
    from src.clients.base import BaseClient, ModelResponse

    class MockClient(BaseClient):
        async def create_message(self, system, messages, tools, max_tokens=8000, temperature=1.0, stream=False, **kwargs):
            await asyncio.sleep(5.0)  # Simulate slow LLM call
            return ModelResponse(
                content=[{"type": "text", "text": "Response"}],
                stop_reason="end_turn",
                usage={"input_tokens": 10, "output_tokens": 10},
                model="mock"
            )

        async def generate_summary(self, prompt: str) -> str:
            return "Summary"

        @property
        def model_name(self) -> str:
            return "mock"

        @property
        def context_window(self) -> int:
            return 8000

        @property
        def provider_name(self) -> str:
            return "mock"

    client = MockClient()
    mock_persistence = Mock()
    session_manager = SessionManager(mock_persistence)

    # Start execution
    session_manager.start_new_execution()
    token = session_manager.cancellation_token

    # Start LLM call
    task = asyncio.create_task(
        client.create_message_with_cancellation(
            system="Test",
            messages=[],
            tools=[],
            cancellation_token=token
        )
    )

    # Cancel it
    await asyncio.sleep(0.2)
    session_manager.cancel_all("LLM call cancelled")

    # Should raise CancelledError
    with pytest.raises(asyncio.CancelledError):
        await task
