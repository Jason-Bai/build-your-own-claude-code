"""Unit tests for WebSearchTool - All Phases Combined"""

import pytest
import asyncio
import time
import httpx
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.tools.web_search import WebSearchTool
from src.tools.base import ToolPermissionLevel, ToolResult


# ============================================================================
# Phase 1: Basic Implementation - DuckDuckGo Backend
# ============================================================================
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

        with patch('src.tools.web_search.DDGS', None):
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


# ============================================================================
# Phase 2: Premium Backends
# ============================================================================
class TestWebSearchToolProviders:
    """Test provider selection and initialization"""

    def test_provider_default_duckduckgo(self):
        """Test default provider is DuckDuckGo"""
        tool = WebSearchTool()
        assert tool.provider == "duckduckgo"

    def test_provider_brave_with_api_key(self):
        """Test Brave provider with API key"""
        tool = WebSearchTool(provider="brave", api_key="test-key")
        assert tool.provider == "brave"
        assert tool.api_key == "test-key"

    def test_provider_google_with_api_key(self):
        """Test Google provider with API key and search engine ID"""
        tool = WebSearchTool(
            provider="google",
            api_key="test-key",
            search_engine_id="test-cx"
        )
        assert tool.provider == "google"
        assert tool.api_key == "test-key"
        assert tool.search_engine_id == "test-cx"

    def test_provider_fallback_no_api_key(self):
        """Test automatic fallback to DuckDuckGo when no API key provided"""
        tool = WebSearchTool(provider="brave")
        assert tool.provider == "duckduckgo"

        tool = WebSearchTool(provider="google")
        assert tool.provider == "duckduckgo"

    def test_provider_case_insensitive(self):
        """Test provider name is case insensitive"""
        tool = WebSearchTool(provider="BRAVE", api_key="test-key")
        assert tool.provider == "brave"

        tool = WebSearchTool(provider="Google", api_key="test-key", search_engine_id="test-cx")
        assert tool.provider == "google"


class TestBraveSearchBackend:
    """Test Brave Search API backend"""

    @pytest.mark.asyncio
    async def test_brave_search_success(self):
        """Test successful Brave search"""
        tool = WebSearchTool(provider="brave", api_key="test-brave-key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Brave Result 1",
                        "url": "https://brave.com/1",
                        "description": "Brave snippet 1"
                    },
                    {
                        "title": "Brave Result 2",
                        "url": "https://brave.com/2",
                        "description": "Brave snippet 2"
                    }
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            results = await tool._search_brave("test query", 2)

            assert len(results) == 2
            assert results[0]["title"] == "Brave Result 1"
            assert results[0]["url"] == "https://brave.com/1"
            assert results[0]["snippet"] == "Brave snippet 1"

    @pytest.mark.asyncio
    async def test_brave_search_no_api_key(self):
        """Test Brave search without API key raises error"""
        tool = WebSearchTool(provider="duckduckgo")  # No API key
        tool.api_key = None

        with pytest.raises(ValueError, match="Brave Search API key not configured"):
            await tool._search_brave("test", 5)

    @pytest.mark.asyncio
    async def test_brave_search_httpx_not_available(self):
        """Test Brave search when httpx not installed"""
        tool = WebSearchTool(provider="brave", api_key="test-key")

        with patch('src.tools.web_search.HTTPX_AVAILABLE', False):
            with patch('src.tools.web_search.httpx', None):
                with pytest.raises(ImportError, match="httpx package not installed"):
                    await tool._search_brave("test", 5)

    @pytest.mark.asyncio
    async def test_brave_search_api_error(self):
        """Test Brave search with API error"""
        tool = WebSearchTool(provider="brave", api_key="invalid-key")

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=Mock(),
            response=Mock(status_code=401)
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with pytest.raises(httpx.HTTPStatusError):
                await tool._search_brave("test", 5)


class TestGoogleSearchBackend:
    """Test Google Custom Search API backend"""

    @pytest.mark.asyncio
    async def test_google_search_success(self):
        """Test successful Google search"""
        tool = WebSearchTool(
            provider="google",
            api_key="test-google-key",
            search_engine_id="test-cx"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "title": "Google Result 1",
                    "link": "https://google.com/1",
                    "snippet": "Google snippet 1"
                },
                {
                    "title": "Google Result 2",
                    "link": "https://google.com/2",
                    "snippet": "Google snippet 2"
                }
            ]
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            results = await tool._search_google("test query", 2)

            assert len(results) == 2
            assert results[0]["title"] == "Google Result 1"
            assert results[0]["url"] == "https://google.com/1"
            assert results[0]["snippet"] == "Google snippet 1"

    @pytest.mark.asyncio
    async def test_google_search_no_api_key(self):
        """Test Google search without API key raises error"""
        tool = WebSearchTool(provider="duckduckgo")
        tool.api_key = None

        with pytest.raises(ValueError, match="Google Custom Search API key not configured"):
            await tool._search_google("test", 5)

    @pytest.mark.asyncio
    async def test_google_search_no_search_engine_id(self):
        """Test Google search without search engine ID raises error"""
        tool = WebSearchTool(provider="google", api_key="test-key")
        tool.search_engine_id = None

        with pytest.raises(ValueError, match="Google Custom Search engine ID not configured"):
            await tool._search_google("test", 5)

    @pytest.mark.asyncio
    async def test_google_search_httpx_not_available(self):
        """Test Google search when httpx not installed"""
        tool = WebSearchTool(
            provider="google",
            api_key="test-key",
            search_engine_id="test-cx"
        )

        with patch('src.tools.web_search.HTTPX_AVAILABLE', False):
            with patch('src.tools.web_search.httpx', None):
                with pytest.raises(ImportError, match="httpx package not installed"):
                    await tool._search_google("test", 5)


class TestProviderFallback:
    """Test provider fallback mechanism"""

    @pytest.mark.asyncio
    async def test_brave_fallback_to_duckduckgo(self):
        """Test fallback from Brave to DuckDuckGo on error"""
        tool = WebSearchTool(provider="brave", api_key="invalid-key")

        # Mock Brave to fail
        with patch.object(tool, '_search_brave', side_effect=Exception("API Error")):
            # Mock DuckDuckGo to succeed
            with patch.object(tool, '_search_duckduckgo', return_value=[
                {"title": "DDG Result", "url": "https://ddg.com", "snippet": "DDG snippet"}
            ]):
                result = await tool.execute(query="test query")

                assert result.success
                assert "duckduckgo (fallback)" in result.metadata["provider"]
                assert "DDG Result" in result.output

    @pytest.mark.asyncio
    async def test_google_fallback_to_duckduckgo(self):
        """Test fallback from Google to DuckDuckGo on error"""
        tool = WebSearchTool(
            provider="google",
            api_key="invalid-key",
            search_engine_id="test-cx"
        )

        # Mock Google to fail
        with patch.object(tool, '_search_google', side_effect=Exception("API Error")):
            # Mock DuckDuckGo to succeed
            with patch.object(tool, '_search_duckduckgo', return_value=[
                {"title": "DDG Result", "url": "https://ddg.com", "snippet": "DDG snippet"}
            ]):
                result = await tool.execute(query="test query")

                assert result.success
                assert "duckduckgo (fallback)" in result.metadata["provider"]

    @pytest.mark.asyncio
    async def test_duckduckgo_no_fallback(self):
        """Test DuckDuckGo doesn't fallback (it's the fallback)"""
        tool = WebSearchTool(provider="duckduckgo")

        with patch.object(tool, '_search_duckduckgo', side_effect=Exception("DDG Error")):
            result = await tool.execute(query="test query")

            assert not result.success
            assert "DDG Error" in result.error

    @pytest.mark.asyncio
    async def test_both_providers_fail(self):
        """Test when both primary and fallback fail"""
        tool = WebSearchTool(provider="brave", api_key="test-key")

        with patch.object(tool, '_search_brave', side_effect=Exception("Brave Error")):
            with patch.object(tool, '_search_duckduckgo', side_effect=Exception("DDG Error")):
                result = await tool.execute(query="test query")

                assert not result.success
                assert "Primary provider failed" in result.error
                assert "Fallback failed" in result.error


class TestProviderIntegration:
    """Integration tests for different providers"""

    @pytest.mark.asyncio
    async def test_brave_execute_success(self):
        """Test full execution with Brave provider"""
        tool = WebSearchTool(provider="brave", api_key="test-brave-key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "web": {"results": [
                {"title": "Result 1", "url": "https://example.com/1", "description": "Snippet 1"}
            ]}
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await tool.execute(query="test query")

            assert result.success
            assert result.metadata["provider"] == "brave"
            assert "Result 1" in result.output

    @pytest.mark.asyncio
    async def test_google_execute_success(self):
        """Test full execution with Google provider"""
        tool = WebSearchTool(
            provider="google",
            api_key="test-google-key",
            search_engine_id="test-cx"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {"title": "Result 1", "link": "https://example.com/1", "snippet": "Snippet 1"}
            ]
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await tool.execute(query="test query")

            assert result.success
            assert result.metadata["provider"] == "google"
            assert "Result 1" in result.output


class TestUsageStatsWithProviders:
    """Test usage statistics with different providers"""

    def test_stats_reflect_brave_provider(self):
        """Test usage stats show Brave provider"""
        tool = WebSearchTool(provider="brave", api_key="test-key")
        stats = tool.get_usage_stats()

        assert stats["provider"] == "brave"

    def test_stats_reflect_google_provider(self):
        """Test usage stats show Google provider"""
        tool = WebSearchTool(provider="google", api_key="test-key", search_engine_id="test-cx")
        stats = tool.get_usage_stats()

        assert stats["provider"] == "google"

    def test_stats_reflect_duckduckgo_provider(self):
        """Test usage stats show DuckDuckGo provider"""
        tool = WebSearchTool(provider="duckduckgo")
        stats = tool.get_usage_stats()

        assert stats["provider"] == "duckduckgo"


# ============================================================================
# Phase 3: Enhancements
# ============================================================================
class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limit_not_exceeded(self):
        """Test requests within rate limit succeed"""
        tool = WebSearchTool(rate_limit=5)

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            # Make 5 requests (within limit)
            for i in range(5):
                result = await tool.execute(query=f"test query {i}")
                assert result.success

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit enforcement"""
        tool = WebSearchTool(rate_limit=2)

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            # Make 2 requests (at limit)
            await tool.execute(query="test 1")
            await tool.execute(query="test 2")

            # Third request should fail
            result = await tool.execute(query="test 3")
            assert not result.success
            assert "rate limit exceeded" in result.error.lower()

    @pytest.mark.asyncio
    async def test_rate_limit_disabled(self):
        """Test rate limiting can be disabled"""
        tool = WebSearchTool(rate_limit=0)  # Disabled

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            # Make many requests
            for i in range(100):
                result = await tool.execute(query=f"test {i}")
                assert result.success

    @pytest.mark.asyncio
    async def test_rate_limit_sliding_window(self):
        """Test rate limit uses sliding window"""
        tool = WebSearchTool(rate_limit=2)

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            # Make 2 requests
            await tool.execute(query="test 1")
            await tool.execute(query="test 2")

            # Mock time to advance 61 seconds
            with patch('time.time', return_value=time.time() + 61):
                # Should succeed after window expires
                result = await tool.execute(query="test 3")
                assert result.success


class TestCaching:
    """Test caching functionality"""

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cached results are returned"""
        tool = WebSearchTool(enable_cache=True, cache_ttl=3600)

        mock_results = [
            {"title": "Result 1", "url": "https://example.com/1", "snippet": "Snippet 1"}
        ]

        with patch.object(tool, '_search_duckduckgo', return_value=mock_results) as mock_search:
            # First request - cache miss
            result1 = await tool.execute(query="test query")
            assert result1.success
            assert mock_search.call_count == 1
            assert result1.metadata["cached"] == False

            # Second request - cache hit
            result2 = await tool.execute(query="test query")
            assert result2.success
            assert mock_search.call_count == 1  # Not called again
            assert result2.metadata["cached"] == True
            assert "(cached)" in result2.metadata["provider"]

    @pytest.mark.asyncio
    async def test_cache_different_queries(self):
        """Test different queries don't hit same cache"""
        tool = WebSearchTool(enable_cache=True)

        with patch.object(tool, '_search_duckduckgo', return_value=[]) as mock_search:
            await tool.execute(query="query 1")
            await tool.execute(query="query 2")

            assert mock_search.call_count == 2  # Both called search

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test caching can be disabled"""
        tool = WebSearchTool(enable_cache=False)

        with patch.object(tool, '_search_duckduckgo', return_value=[]) as mock_search:
            await tool.execute(query="test query")
            await tool.execute(query="test query")

            assert mock_search.call_count == 2  # Both called search

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """Test cache entries expire after TTL"""
        tool = WebSearchTool(enable_cache=True, cache_ttl=1)  # 1 second TTL

        with patch.object(tool, '_search_duckduckgo', return_value=[]) as mock_search:
            # First request
            await tool.execute(query="test query")
            assert mock_search.call_count == 1

            # Wait for cache to expire
            await asyncio.sleep(1.1)

            # Second request after expiration
            await tool.execute(query="test query")
            assert mock_search.call_count == 2  # Called again

    @pytest.mark.asyncio
    async def test_cache_key_includes_max_results(self):
        """Test cache key differentiates max_results"""
        tool = WebSearchTool(enable_cache=True)

        with patch.object(tool, '_search_duckduckgo', return_value=[]) as mock_search:
            await tool.execute(query="test", max_results=5)
            await tool.execute(query="test", max_results=10)

            assert mock_search.call_count == 2  # Different cache keys

    def test_clear_cache(self):
        """Test cache can be cleared"""
        tool = WebSearchTool(enable_cache=True)

        # Manually add to cache
        tool._cache["test_key"] = (time.time(), [])
        assert len(tool._cache) == 1

        # Clear cache
        cleared = tool.clear_cache()
        assert cleared == 1
        assert len(tool._cache) == 0

    def test_cache_stats(self):
        """Test cache statistics"""
        tool = WebSearchTool(enable_cache=True)

        stats = tool.get_cache_stats()
        assert stats["cache_size"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_cache_stats_after_usage(self):
        """Test cache statistics track hits and misses"""
        tool = WebSearchTool(enable_cache=True)

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            # Cache miss
            await tool.execute(query="test 1")
            # Cache hit
            await tool.execute(query="test 1")
            # Cache miss
            await tool.execute(query="test 2")

        stats = tool.get_cache_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 2
        # Hit rate should be approximately 1/3 (1 hit out of 3 total accesses)
        assert 0.3 <= stats["hit_rate"] <= 0.4


class TestCacheKeyGeneration:
    """Test cache key generation"""

    def test_cache_key_same_query(self):
        """Test same query generates same key"""
        tool = WebSearchTool()

        key1 = tool._generate_cache_key("test query", 5)
        key2 = tool._generate_cache_key("test query", 5)

        assert key1 == key2

    def test_cache_key_case_insensitive(self):
        """Test cache key is case insensitive"""
        tool = WebSearchTool()

        key1 = tool._generate_cache_key("Test Query", 5)
        key2 = tool._generate_cache_key("test query", 5)

        assert key1 == key2

    def test_cache_key_different_queries(self):
        """Test different queries generate different keys"""
        tool = WebSearchTool()

        key1 = tool._generate_cache_key("query 1", 5)
        key2 = tool._generate_cache_key("query 2", 5)

        assert key1 != key2

    def test_cache_key_different_providers(self):
        """Test different providers generate different keys"""
        tool1 = WebSearchTool(provider="duckduckgo")
        tool2 = WebSearchTool(provider="brave", api_key="test")

        key1 = tool1._generate_cache_key("test", 5)
        key2 = tool2._generate_cache_key("test", 5)

        assert key1 != key2


class TestUsageStatsEnhanced:
    """Test enhanced usage statistics"""

    def test_stats_include_rate_limit(self):
        """Test stats include rate limit configuration"""
        tool = WebSearchTool(rate_limit=10)
        stats = tool.get_usage_stats()

        assert stats["rate_limit"] == 10

    def test_stats_include_cache_config(self):
        """Test stats include cache configuration"""
        tool = WebSearchTool(enable_cache=True, cache_ttl=3600)
        stats = tool.get_usage_stats()

        assert stats["cache_enabled"] == True
        assert stats["cache_ttl"] == 3600

    @pytest.mark.asyncio
    async def test_stats_include_cache_performance(self):
        """Test stats include cache performance metrics"""
        tool = WebSearchTool(enable_cache=True)

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            await tool.execute(query="test")
            await tool.execute(query="test")  # Cache hit

        stats = tool.get_usage_stats()
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate" in stats


class TestInitializationPhase3:
    """Test initialization with Phase 3 parameters"""

    def test_init_with_rate_limit(self):
        """Test initialization with custom rate limit"""
        tool = WebSearchTool(rate_limit=20)
        assert tool.rate_limit == 20

    def test_init_with_cache_config(self):
        """Test initialization with cache configuration"""
        tool = WebSearchTool(enable_cache=True, cache_ttl=7200)
        assert tool.enable_cache == True
        assert tool.cache_ttl == 7200

    def test_init_cache_disabled(self):
        """Test initialization with cache disabled"""
        tool = WebSearchTool(enable_cache=False)
        assert tool.enable_cache == False

    def test_init_default_values(self):
        """Test default values for Phase 3 parameters"""
        tool = WebSearchTool()
        assert tool.rate_limit == 10
        assert tool.cache_ttl == 3600
        assert tool.enable_cache == True


class TestIntegrationPhase3:
    """Integration tests for Phase 3 features"""

    @pytest.mark.asyncio
    async def test_rate_limit_and_cache_together(self):
        """Test rate limiting and caching work together"""
        tool = WebSearchTool(rate_limit=3, enable_cache=True)

        with patch.object(tool, '_search_duckduckgo', return_value=[]):
            # First request - cache miss, uses rate limit slot 1
            result1 = await tool.execute(query="test")
            assert result1.success
            assert result1.metadata["cached"] == False

            # Second request same query - cache hit, doesn't use rate limit
            result2 = await tool.execute(query="test")
            assert result2.success
            assert result2.metadata["cached"] == True

            # Third different query - cache miss, uses rate limit slot 2
            result3 = await tool.execute(query="different1")
            assert result3.success

            # Fourth different query - cache miss, uses rate limit slot 3
            result4 = await tool.execute(query="different2")
            assert result4.success

            # Fifth different query - hits rate limit
            result5 = await tool.execute(query="different3")
            assert not result5.success
            assert "rate limit" in result5.error.lower()

    @pytest.mark.asyncio
    async def test_cache_persists_across_providers(self):
        """Test cache works with provider fallback"""
        tool = WebSearchTool(provider="brave", api_key="test", enable_cache=True)

        mock_results = [{"title": "Result", "url": "https://example.com", "snippet": "Snippet"}]

        # First request fails on Brave, falls back to DuckDuckGo
        with patch.object(tool, '_search_brave', side_effect=Exception("API Error")):
            with patch.object(tool, '_search_duckduckgo', return_value=mock_results) as mock_ddg:
                result1 = await tool.execute(query="test")
                assert result1.success
                assert "fallback" in result1.metadata["provider"]

                # Second request uses cache (doesn't call either provider again)
                result2 = await tool.execute(query="test")
                assert result2.success
                assert result2.metadata["cached"] == True
                assert mock_ddg.call_count == 1  # Only called once

    @pytest.mark.asyncio
    async def test_performance_with_cache(self):
        """Test caching improves performance"""
        tool = WebSearchTool(enable_cache=True)

        async def slow_search(*args):
            await asyncio.sleep(0.01)  # 10ms delay
            return []

        with patch.object(tool, '_search_duckduckgo', side_effect=slow_search):
            # First request (cache miss) - should be slow
            start1 = time.time()
            await tool.execute(query="test")
            time1 = time.time() - start1

            # Second request (cache hit) - should be fast
            start2 = time.time()
            await tool.execute(query="test")
            time2 = time.time() - start2

            # Cache hit should be at least 5x faster (10ms vs <2ms)
            assert time2 < 0.005  # Less than 5ms
            assert time1 > 0.009  # More than 9ms


# ============================================================================
# Phase 4: Polish & Retry Logic
# ============================================================================
class TestRetryLogic:
    """Test retry logic with exponential backoff"""

    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt"""
        tool = WebSearchTool(max_retries=3)

        async def successful_search(*args):
            return [{"title": "Result", "url": "https://example.com", "snippet": "Test"}]

        result = await tool._retry_with_backoff(successful_search, "test", 5)
        assert len(result) == 1
        assert tool._retry_count == 0  # No retries needed

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test successful execution after some failures"""
        tool = WebSearchTool(max_retries=3, retry_delay=0.01)

        call_count = 0

        async def flaky_search(*args):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return [{"title": "Result", "url": "https://example.com", "snippet": "Test"}]

        result = await tool._retry_with_backoff(flaky_search, "test", 5)
        assert len(result) == 1
        assert call_count == 3
        assert tool._retry_count == 2  # 2 retries before success

    @pytest.mark.asyncio
    async def test_retry_all_attempts_fail(self):
        """Test when all retry attempts fail"""
        tool = WebSearchTool(max_retries=2, retry_delay=0.01)

        async def always_fails(*args):
            raise ConnectionError("Persistent failure")

        with pytest.raises(ConnectionError, match="Persistent failure"):
            await tool._retry_with_backoff(always_fails, "test", 5)

        assert tool._retry_count == 2
        assert tool._failed_requests == 1

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test exponential backoff timing"""
        tool = WebSearchTool(max_retries=3, retry_delay=0.1)

        call_times = []

        async def failing_search(*args):
            call_times.append(time.time())
            raise TimeoutError("Timeout")

        try:
            await tool._retry_with_backoff(failing_search, "test", 5)
        except TimeoutError:
            pass

        # Check that delays are exponentially increasing
        # First retry: ~0.1s, Second retry: ~0.2s
        assert len(call_times) == 3
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        # Use generous bounds to account for system timing variations
        assert 0.05 < delay1 < 0.3  # ~0.1s with jitter
        assert 0.15 < delay2 < 0.5  # ~0.2s with jitter
        assert delay2 > delay1  # Second delay should be longer

    @pytest.mark.asyncio
    async def test_retry_disabled(self):
        """Test retry can be disabled"""
        tool = WebSearchTool(max_retries=1)

        call_count = 0

        async def failing_search(*args):
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Failure")

        with pytest.raises(ConnectionError):
            await tool._retry_with_backoff(failing_search, "test", 5)

        assert call_count == 1  # Only one attempt


class TestIntegrationWithRetry:
    """Test retry integration with search execution"""

    @pytest.mark.asyncio
    async def test_search_with_retry_success(self):
        """Test search execution with retry succeeding"""
        tool = WebSearchTool(max_retries=3, retry_delay=0.01)

        call_count = 0

        async def flaky_ddg_search(*args):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return [{"title": "Result", "url": "https://example.com", "snippet": "Test"}]

        with patch.object(tool, '_search_duckduckgo', side_effect=flaky_ddg_search):
            result = await tool.execute(query="test query")

            assert result.success
            assert call_count == 2  # Failed once, succeeded on retry
            assert tool._retry_count == 1

    @pytest.mark.asyncio
    async def test_search_with_fallback_and_retry(self):
        """Test fallback provider also uses retry logic"""
        tool = WebSearchTool(provider="brave", api_key="test", max_retries=2, retry_delay=0.01)

        brave_calls = 0
        ddg_calls = 0

        async def failing_brave(*args):
            nonlocal brave_calls
            brave_calls += 1
            raise Exception("Brave API error")

        async def flaky_ddg(*args):
            nonlocal ddg_calls
            ddg_calls += 1
            if ddg_calls < 2:
                raise ConnectionError("DDG temporary error")
            return [{"title": "Result", "url": "https://example.com", "snippet": "Test"}]

        with patch.object(tool, '_search_brave', side_effect=failing_brave):
            with patch.object(tool, '_search_duckduckgo', side_effect=flaky_ddg):
                result = await tool.execute(query="test")

                assert result.success
                assert "fallback" in result.metadata["provider"]
                assert brave_calls == 2  # Brave tried with retry
                assert ddg_calls == 2  # DDG tried with retry


class TestRetryStatistics:
    """Test retry statistics tracking"""

    @pytest.mark.asyncio
    async def test_stats_track_retry_count(self):
        """Test statistics track total retries"""
        tool = WebSearchTool(max_retries=3, retry_delay=0.01)

        # Track calls per query separately
        query_calls = {}

        async def flaky_search(query, *args):
            if query not in query_calls:
                query_calls[query] = 0
            query_calls[query] += 1
            if query_calls[query] < 3:
                raise ConnectionError("Failure")
            return []

        with patch.object(tool, '_search_duckduckgo', side_effect=flaky_search):
            await tool.execute(query="test 1")
            await tool.execute(query="test 2")

        stats = tool.get_usage_stats()
        assert stats["retry_count"] == 4  # 2 retries per request (3 attempts each)
        assert stats["failed_requests"] == 0  # All eventually succeeded

    @pytest.mark.asyncio
    async def test_stats_track_failed_requests(self):
        """Test statistics track failed requests"""
        tool = WebSearchTool(max_retries=2, retry_delay=0.01)

        async def always_fails(*args):
            raise ConnectionError("Persistent failure")

        with patch.object(tool, '_search_duckduckgo', side_effect=always_fails):
            result1 = await tool.execute(query="test 1")
            result2 = await tool.execute(query="test 2")

        assert not result1.success
        assert not result2.success

        stats = tool.get_usage_stats()
        assert stats["failed_requests"] == 2
        assert stats["retry_count"] == 4  # 2 retries per request

    def test_stats_include_max_retries(self):
        """Test statistics include max_retries configuration"""
        tool = WebSearchTool(max_retries=5)
        stats = tool.get_usage_stats()
        assert stats["max_retries"] == 5


class TestInitializationPhase4:
    """Test initialization with Phase 4 parameters"""

    def test_init_with_retry_config(self):
        """Test initialization with retry configuration"""
        tool = WebSearchTool(max_retries=5, retry_delay=2.0)
        assert tool.max_retries == 5
        assert tool.retry_delay == 2.0

    def test_init_default_retry_values(self):
        """Test default retry values"""
        tool = WebSearchTool()
        assert tool.max_retries == 3
        assert tool.retry_delay == 1.0

    def test_init_retry_statistics(self):
        """Test retry statistics are initialized"""
        tool = WebSearchTool()
        assert tool._retry_count == 0
        assert tool._failed_requests == 0


class TestErrorHandling:
    """Test improved error handling"""

    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test connection errors are properly handled"""
        tool = WebSearchTool(max_retries=1, retry_delay=0.01)

        async def connection_error(*args):
            raise ConnectionError("Network unreachable")

        with patch.object(tool, '_search_duckduckgo', side_effect=connection_error):
            result = await tool.execute(query="test")

            assert not result.success
            assert "failed" in result.error.lower()
            assert "unreachable" in result.error.lower()

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """Test timeout errors are properly handled"""
        tool = WebSearchTool(max_retries=1, retry_delay=0.01)

        with patch.object(tool, '_search_duckduckgo', side_effect=asyncio.TimeoutError()):
            result = await tool.execute(query="test")

            assert not result.success
            assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_api_error_details_preserved(self):
        """Test API error details are preserved in error message"""
        tool = WebSearchTool(provider="brave", api_key="invalid", max_retries=1, retry_delay=0.01)

        async def api_error(*args):
            raise ValueError("Invalid API key: authentication failed")

        with patch.object(tool, '_search_brave', side_effect=api_error):
            with patch.object(tool, '_search_duckduckgo', return_value=[]):
                result = await tool.execute(query="test")

                # Should fallback to DDG
                assert result.success
                assert "fallback" in result.metadata["provider"]


class TestReliability:
    """Test overall reliability improvements"""

    @pytest.mark.asyncio
    async def test_transient_failures_recovered(self):
        """Test system recovers from transient failures"""
        tool = WebSearchTool(max_retries=3, retry_delay=0.01, enable_cache=True)

        # Simulate intermittent failures
        call_count = 0

        async def intermittent_failure(*args):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:  # Fail on odd attempts
                raise ConnectionError("Intermittent failure")
            return [{"title": "Result", "url": "https://example.com", "snippet": "Test"}]

        with patch.object(tool, '_search_duckduckgo', side_effect=intermittent_failure):
            # Multiple requests - should eventually succeed
            results = []
            for i in range(3):
                result = await tool.execute(query=f"test {i}")
                results.append(result)

            # All should succeed (with retries)
            assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_cache_prevents_unnecessary_retries(self):
        """Test cached results don't trigger retries"""
        tool = WebSearchTool(max_retries=3, retry_delay=0.01, enable_cache=True)

        call_count = 0

        async def counting_search(*args):
            nonlocal call_count
            call_count += 1
            return [{"title": "Result", "url": "https://example.com", "snippet": "Test"}]

        with patch.object(tool, '_search_duckduckgo', side_effect=counting_search):
            # First request - will call search
            result1 = await tool.execute(query="test")
            assert call_count == 1

            # Second request - should use cache, no search call
            result2 = await tool.execute(query="test")
            assert call_count == 1  # Still 1
            assert result2.metadata["cached"] == True
