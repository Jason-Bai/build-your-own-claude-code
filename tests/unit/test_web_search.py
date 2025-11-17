"""Unit tests for WebSearchTool"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.tools.web_search import WebSearchTool
from src.tools.base import ToolPermissionLevel, ToolResult


class TestWebSearchToolInitialization:
    """Test WebSearchTool initialization"""

    def test_init_default_parameters(self):
        """Test initialization with default parameters"""
        tool = WebSearchTool()

        assert tool.max_results == 5
        assert tool.timeout == 10
        assert tool.region == "wt-wt"
        assert tool.safe_search == "moderate"
        assert tool._search_count == 0
        assert tool._last_search_time is None

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters"""
        tool = WebSearchTool(
            max_results=8,
            timeout=15,
            region="us-en",
            safe_search="strict"
        )

        assert tool.max_results == 8
        assert tool.timeout == 15
        assert tool.region == "us-en"
        assert tool.safe_search == "strict"


class TestWebSearchToolProperties:
    """Test WebSearchTool properties"""

    def test_name_property(self):
        """Test tool name property"""
        tool = WebSearchTool()
        assert tool.name == "web_search"

    def test_description_property(self):
        """Test tool description property"""
        tool = WebSearchTool()
        description = tool.description

        assert isinstance(description, str)
        assert len(description) > 50
        assert "web" in description.lower()
        assert "search" in description.lower()

    def test_permission_level(self):
        """Test tool permission level"""
        tool = WebSearchTool()
        assert tool.permission_level == ToolPermissionLevel.NORMAL

    def test_input_schema(self):
        """Test tool input schema"""
        tool = WebSearchTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]
        assert "query" in schema["required"]

        # Check query parameter
        query_param = schema["properties"]["query"]
        assert query_param["type"] == "string"
        assert "description" in query_param

        # Check max_results parameter
        max_results_param = schema["properties"]["max_results"]
        assert max_results_param["type"] == "integer"
        assert max_results_param["minimum"] == 1
        assert max_results_param["maximum"] == 10
        assert max_results_param["default"] == 5


class TestWebSearchToolExecution:
    """Test WebSearchTool execute method"""

    @pytest.mark.asyncio
    async def test_execute_empty_query(self):
        """Test execution with empty query"""
        tool = WebSearchTool()
        result = await tool.execute(query="")

        assert not result.success
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_whitespace_query(self):
        """Test execution with whitespace-only query"""
        tool = WebSearchTool()
        result = await tool.execute(query="   ")

        assert not result.success
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_max_results_clamping(self):
        """Test max_results is clamped to valid range [1, 10]"""
        tool = WebSearchTool()

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            # Test below minimum
            result = await tool.execute(query="test", max_results=0)
            assert result.success

            # Test above maximum
            result = await tool.execute(query="test", max_results=20)
            assert result.success

            # Test negative
            result = await tool.execute(query="test", max_results=-5)
            assert result.success

    @pytest.mark.asyncio
    async def test_execute_import_error(self):
        """Test execution when duckduckgo-search not installed"""
        tool = WebSearchTool()

        with patch.object(tool, '_search_duckduckgo', side_effect=ImportError("No module")):
            result = await tool.execute(query="test query")

            assert not result.success
            assert "not installed" in result.error.lower()
            assert "pip install" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_timeout_error(self):
        """Test execution timeout"""
        tool = WebSearchTool(timeout=1)

        async def slow_search(*args):
            await asyncio.sleep(2)
            return []

        with patch.object(tool, '_search_duckduckgo', side_effect=asyncio.TimeoutError()):
            result = await tool.execute(query="test query")

            assert not result.success
            assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_general_exception(self):
        """Test execution with general exception"""
        tool = WebSearchTool()

        with patch.object(tool, '_search_duckduckgo', side_effect=Exception("Network error")):
            result = await tool.execute(query="test query")

            assert not result.success
            assert "failed" in result.error.lower()
            assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_execute_no_results(self):
        """Test execution when no results found"""
        tool = WebSearchTool()

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            result = await tool.execute(query="test query")

            assert result.success
            assert "no results found" in result.output.lower()
            assert result.metadata["result_count"] == 0
            assert result.metadata["provider"] == "duckduckgo"

    @pytest.mark.asyncio
    async def test_execute_with_results(self):
        """Test execution with successful results"""
        tool = WebSearchTool()

        mock_results = [
            {
                "title": "Test Result 1",
                "url": "https://example.com/1",
                "snippet": "This is test snippet 1"
            },
            {
                "title": "Test Result 2",
                "url": "https://example.com/2",
                "snippet": "This is test snippet 2"
            }
        ]

        with patch.object(tool, '_search_duckduckgo', return_value=mock_results):
            result = await tool.execute(query="test query", max_results=2)

            assert result.success
            assert "test query" in result.output.lower()
            assert "Test Result 1" in result.output
            assert "https://example.com/1" in result.output
            assert "test snippet 1" in result.output.lower()
            assert result.metadata["result_count"] == 2
            assert result.metadata["query"] == "test query"
            assert result.metadata["provider"] == "duckduckgo"
            assert "timestamp" in result.metadata

    @pytest.mark.asyncio
    async def test_execute_updates_statistics(self):
        """Test that execution updates usage statistics"""
        tool = WebSearchTool()

        assert tool._search_count == 0
        assert tool._last_search_time is None

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            await tool.execute(query="test query 1")

            assert tool._search_count == 1
            assert tool._last_search_time is not None

            await tool.execute(query="test query 2")

            assert tool._search_count == 2


class TestWebSearchToolFormatting:
    """Test result formatting"""

    def test_format_empty_results(self):
        """Test formatting empty results"""
        tool = WebSearchTool()
        formatted = tool._format_results([], "test query")

        assert formatted == "No results found."

    def test_format_single_result(self):
        """Test formatting single result"""
        tool = WebSearchTool()

        results = [
            {
                "title": "Test Title",
                "url": "https://example.com",
                "snippet": "Test snippet"
            }
        ]

        formatted = tool._format_results(results, "test query")

        assert "test query" in formatted.lower()
        assert "Found 1 result" in formatted
        assert "1. Test Title" in formatted
        assert "URL: https://example.com" in formatted
        assert "Test snippet" in formatted

    def test_format_multiple_results(self):
        """Test formatting multiple results"""
        tool = WebSearchTool()

        results = [
            {"title": f"Title {i}", "url": f"https://example.com/{i}", "snippet": f"Snippet {i}"}
            for i in range(1, 4)
        ]

        formatted = tool._format_results(results, "multiple results")

        assert "Found 3 result" in formatted
        assert "1. Title 1" in formatted
        assert "2. Title 2" in formatted
        assert "3. Title 3" in formatted
        assert all(f"https://example.com/{i}" in formatted for i in range(1, 4))

    def test_format_long_snippet_truncation(self):
        """Test that long snippets are truncated"""
        tool = WebSearchTool()

        long_snippet = "A" * 500  # 500 characters

        results = [
            {
                "title": "Long Snippet",
                "url": "https://example.com",
                "snippet": long_snippet
            }
        ]

        formatted = tool._format_results(results, "test")

        # Check snippet is truncated to ~300 chars with ellipsis
        assert "..." in formatted
        assert len(formatted) < len(long_snippet) + 200  # Much shorter than original

    def test_format_snippet_with_newlines(self):
        """Test that newlines in snippets are replaced"""
        tool = WebSearchTool()

        results = [
            {
                "title": "Multiline Snippet",
                "url": "https://example.com",
                "snippet": "Line 1\nLine 2\nLine 3"
            }
        ]

        formatted = tool._format_results(results, "test")

        # Newlines should be replaced with spaces
        assert "\nLine 1\nLine 2" not in formatted  # Original newlines removed
        assert "Line 1 Line 2 Line 3" in formatted

    def test_format_missing_fields(self):
        """Test formatting with missing fields"""
        tool = WebSearchTool()

        results = [
            {"title": "", "url": "", "snippet": ""}
        ]

        formatted = tool._format_results(results, "test")

        assert "Untitled" in formatted
        assert "URL:" in formatted
        assert "No description available" in formatted


class TestWebSearchToolUsageStats:
    """Test usage statistics"""

    def test_get_usage_stats_initial(self):
        """Test initial usage statistics"""
        tool = WebSearchTool()
        stats = tool.get_usage_stats()

        assert stats["total_searches"] == 0
        assert stats["last_search_time"] is None
        assert stats["provider"] == "duckduckgo"
        assert stats["max_results"] == 5
        assert stats["timeout"] == 10

    @pytest.mark.asyncio
    async def test_get_usage_stats_after_searches(self):
        """Test usage statistics after searches"""
        tool = WebSearchTool()

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            await tool.execute(query="test 1")
            await tool.execute(query="test 2")

        stats = tool.get_usage_stats()

        assert stats["total_searches"] == 2
        assert stats["last_search_time"] is not None
        assert isinstance(stats["last_search_time"], str)  # ISO format


class TestWebSearchToolDuckDuckGo:
    """Test DuckDuckGo search backend"""

    @pytest.mark.asyncio
    async def test_search_duckduckgo_import_error(self):
        """Test DuckDuckGo search when package not installed"""
        tool = WebSearchTool()

        with patch('src.tools.web_search.DDGS', side_effect=ImportError()):
            with pytest.raises(ImportError, match="duckduckgo-search package not installed"):
                await tool._search_duckduckgo("test", 5)

    @pytest.mark.asyncio
    async def test_search_duckduckgo_success(self):
        """Test successful DuckDuckGo search"""
        tool = WebSearchTool()

        mock_ddgs_results = [
            {
                "title": "Result 1",
                "href": "https://example.com/1",
                "body": "Snippet 1"
            },
            {
                "title": "Result 2",
                "href": "https://example.com/2",
                "body": "Snippet 2"
            }
        ]

        # Mock DDGS
        mock_ddgs_instance = Mock()
        mock_ddgs_instance.text = Mock(return_value=mock_ddgs_results)
        mock_ddgs_context = Mock()
        mock_ddgs_context.__enter__ = Mock(return_value=mock_ddgs_instance)
        mock_ddgs_context.__exit__ = Mock(return_value=False)

        with patch('src.tools.web_search.DDGS', return_value=mock_ddgs_context):
            results = await tool._search_duckduckgo("test query", 2)

            assert len(results) == 2
            assert results[0]["title"] == "Result 1"
            assert results[0]["url"] == "https://example.com/1"
            assert results[0]["snippet"] == "Snippet 1"
            assert results[1]["title"] == "Result 2"

    @pytest.mark.asyncio
    async def test_search_duckduckgo_timeout(self):
        """Test DuckDuckGo search timeout"""
        tool = WebSearchTool(timeout=0.1)

        def slow_search(*args, **kwargs):
            import time
            time.sleep(1)
            return []

        mock_ddgs_instance = Mock()
        mock_ddgs_instance.text = slow_search
        mock_ddgs_context = Mock()
        mock_ddgs_context.__enter__ = Mock(return_value=mock_ddgs_instance)
        mock_ddgs_context.__exit__ = Mock(return_value=False)

        with patch('src.tools.web_search.DDGS', return_value=mock_ddgs_context):
            with pytest.raises(asyncio.TimeoutError):
                await tool._search_duckduckgo("test", 5)


class TestWebSearchToolIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete search workflow"""
        tool = WebSearchTool(max_results=3)

        mock_results = [
            {"title": f"Result {i}", "href": f"https://example.com/{i}", "body": f"Description {i}"}
            for i in range(1, 4)
        ]

        mock_ddgs_instance = Mock()
        mock_ddgs_instance.text = Mock(return_value=mock_results)
        mock_ddgs_context = Mock()
        mock_ddgs_context.__enter__ = Mock(return_value=mock_ddgs_instance)
        mock_ddgs_context.__exit__ = Mock(return_value=False)

        with patch('src.tools.web_search.DDGS', return_value=mock_ddgs_context):
            result = await tool.execute(query="Python async tutorial")

            # Verify result
            assert result.success
            assert "Python async tutorial" in result.output
            assert "Result 1" in result.output
            assert "Result 2" in result.output
            assert "Result 3" in result.output
            assert result.metadata["result_count"] == 3

            # Verify stats updated
            stats = tool.get_usage_stats()
            assert stats["total_searches"] == 1

    @pytest.mark.asyncio
    async def test_multiple_searches(self):
        """Test multiple sequential searches"""
        tool = WebSearchTool()

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            result1 = await tool.execute(query="query 1")
            result2 = await tool.execute(query="query 2")
            result3 = await tool.execute(query="query 3")

            assert all([result1.success, result2.success, result3.success])
            assert tool._search_count == 3

    @pytest.mark.asyncio
    async def test_parameter_override(self):
        """Test that execute parameters override defaults"""
        tool = WebSearchTool(max_results=5)

        with patch.object(tool, '_search_duckduckgo', return_value=[]) as mock_search:
            await tool.execute(query="test", max_results=3)

            # Verify called with overridden max_results
            mock_search.assert_called_once()
            assert mock_search.call_args[0][1] == 3  # max_results argument
