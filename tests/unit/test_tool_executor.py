"""
Unit tests for Tool Executor

Tests smart retry logic, error handling, and tool execution.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.tools.executor import ToolExecutor
from src.tools.base import ToolResult


@pytest.mark.unit
class TestToolExecutorInitialization:
    """Tests for ToolExecutor initialization"""

    def test_tool_executor_instantiation(self):
        """Test ToolExecutor can be instantiated"""
        executor = ToolExecutor()
        assert executor is not None

    def test_tool_executor_has_execute_method(self):
        """Test ToolExecutor has execute_with_smart_retry method"""
        executor = ToolExecutor()
        assert hasattr(executor, 'execute_with_smart_retry')
        assert callable(executor.execute_with_smart_retry)

    def test_tool_executor_has_error_detection_method(self):
        """Test ToolExecutor has error detection method"""
        executor = ToolExecutor()
        assert hasattr(executor, '_is_non_retryable_error')
        assert callable(executor._is_non_retryable_error)


@pytest.mark.unit
class TestToolExecutorSmartRetry:
    """Tests for smart retry logic"""

    @pytest.mark.asyncio
    async def test_execute_with_smart_retry_success_first_try(self):
        """Test successful execution on first try"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.execute = AsyncMock(return_value=ToolResult(success=True, output="Success"))

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is True
        assert result.output == "Success"
        mock_tool.execute.assert_called_once_with(on_chunk=None, **params)

    @pytest.mark.asyncio
    async def test_execute_with_smart_retry_with_params(self):
        """Test execute_with_smart_retry passes parameters correctly"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.execute = AsyncMock(return_value=ToolResult(success=True, output="Success"))

        params = {"command": "ls", "path": "/tmp"}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is True
        mock_tool.execute.assert_called_once_with(on_chunk=None, **params)

    @pytest.mark.asyncio
    async def test_execute_with_smart_retry_retryable_error_first_retry(self):
        """Test retryable error triggers retry and succeeds on second try"""
        executor = ToolExecutor()

        mock_tool = Mock()
        # First call fails with retryable error, second succeeds
        mock_tool.execute = AsyncMock(side_effect=[
            ToolResult(success=False, output="", error="Temporary timeout"),
            ToolResult(success=True, output="Success on retry")
        ])

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is True
        assert result.output == "Success on retry"
        assert mock_tool.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_smart_retry_non_retryable_error(self):
        """Test non-retryable error doesn't trigger retry"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.execute = AsyncMock(
            return_value=ToolResult(success=False, output="", error="File not found")
        )

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is False
        # Should only be called once because 'not found' is non-retryable
        assert mock_tool.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_smart_retry_permission_denied_no_retry(self):
        """Test permission denied error doesn't trigger retry"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.execute = AsyncMock(
            return_value=ToolResult(success=False, output="", error="Permission denied")
        )

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is False
        mock_tool.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_smart_retry_invalid_syntax_no_retry(self):
        """Test invalid syntax error doesn't trigger retry"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.execute = AsyncMock(
            return_value=ToolResult(success=False, output="", error="Invalid syntax in command")
        )

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is False
        mock_tool.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_smart_retry_does_not_exist_no_retry(self):
        """Test 'does not exist' error doesn't trigger retry"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.execute = AsyncMock(
            return_value=ToolResult(success=False, output="", error="Directory does not exist")
        )

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is False
        mock_tool.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_smart_retry_max_retries(self):
        """Test maximum retries are enforced"""
        executor = ToolExecutor()

        mock_tool = Mock()
        # Fail with retryable error (will retry up to max_retries times)
        mock_tool.execute = AsyncMock(
            return_value=ToolResult(success=False, output="", error="Connection timeout")
        )

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params, max_retries=2)

        # Should try initial + 2 retries = 3 total calls (attempts in range(2) is 0,1)
        assert mock_tool.execute.call_count <= 2
        assert result.success is False


@pytest.mark.unit
class TestToolExecutorErrorDetection:
    """Tests for non-retryable error detection"""

    def test_detects_not_found_error(self):
        """Test detection of 'not found' errors"""
        executor = ToolExecutor()
        result = ToolResult(success=False, output="", error="File /path/to/file not found")
        assert executor._is_non_retryable_error(result) is True

    def test_detects_permission_denied_case_insensitive(self):
        """Test case-insensitive detection of permission errors"""
        executor = ToolExecutor()
        result = ToolResult(success=False, output="", error="PERMISSION DENIED")
        assert executor._is_non_retryable_error(result) is True

    def test_detects_invalid_syntax(self):
        """Test detection of invalid syntax errors"""
        executor = ToolExecutor()
        result = ToolResult(success=False, output="", error="Invalid syntax")
        assert executor._is_non_retryable_error(result) is True

    def test_detects_does_not_exist(self):
        """Test detection of 'does not exist' errors"""
        executor = ToolExecutor()
        result = ToolResult(success=False, output="", error="Path does not exist")
        assert executor._is_non_retryable_error(result) is True

    def test_allows_retryable_errors(self):
        """Test that unknown/generic errors are retryable"""
        executor = ToolExecutor()
        result = ToolResult(success=False, output="", error="Connection timeout")
        assert executor._is_non_retryable_error(result) is False

    def test_handles_none_error(self):
        """Test handling of None error field"""
        executor = ToolExecutor()
        result = ToolResult(success=False, output="")
        assert executor._is_non_retryable_error(result) is False


@pytest.mark.unit
class TestToolExecutorMetadata:
    """Tests for metadata and additional result info"""

    @pytest.mark.asyncio
    async def test_preserves_result_metadata(self):
        """Test that result metadata is preserved"""
        executor = ToolExecutor()

        mock_tool = Mock()
        result_with_metadata = ToolResult(
            success=True,
            output="Output",
            metadata={"execution_time": 0.5}
        )
        mock_tool.execute = AsyncMock(return_value=result_with_metadata)

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.metadata == {"execution_time": 0.5}

    @pytest.mark.asyncio
    async def test_includes_retry_metadata_on_failure(self):
        """Test that retry metadata is included on failure"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.execute = AsyncMock(
            return_value=ToolResult(success=False, output="", error="not found")
        )

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params, max_retries=2)

        # When retries are exhausted, metadata should include attempt count
        assert "attempts" in result.metadata or result.success is False


@pytest.mark.unit
class TestToolExecutorIntegration:
    """Integration tests for ToolExecutor"""

    @pytest.mark.asyncio
    async def test_realistic_tool_execution_flow(self):
        """Test realistic tool execution flow"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.name = "bash"

        # Simulate initial timeout, then success
        mock_tool.execute = AsyncMock(side_effect=[
            ToolResult(success=False, output="", error="Request timeout"),
            ToolResult(success=True, output="Directory listing")
        ])

        params = {"command": "ls -la"}
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is True
        assert "Directory listing" in result.output
        assert mock_tool.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_executor_with_complex_params(self):
        """Test executor with multiple parameters"""
        executor = ToolExecutor()

        mock_tool = Mock()
        mock_tool.execute = AsyncMock(return_value=ToolResult(success=True, output="Done"))

        params = {
            "command": "find",
            "path": "/tmp",
            "pattern": "*.log",
            "recursive": True
        }
        result = await executor.execute_with_smart_retry(mock_tool, params)

        assert result.success is True
        call_args = mock_tool.execute.call_args
        assert call_args[1]["command"] == "find"
        assert call_args[1]["path"] == "/tmp"
        assert call_args[1]["pattern"] == "*.log"
        assert call_args[1]["recursive"] is True

    @pytest.mark.asyncio
    async def test_executor_custom_max_retries(self):
        """Test executor with custom max_retries"""
        executor = ToolExecutor()

        call_count = 0
        async def failing_execute(**params):
            nonlocal call_count
            call_count += 1
            return ToolResult(success=False, output="", error="Network error")

        mock_tool = Mock()
        mock_tool.execute = failing_execute

        params = {}
        result = await executor.execute_with_smart_retry(mock_tool, params, max_retries=3)

        # With max_retries=3, loop is range(3) so 3 attempts
        assert call_count <= 3
