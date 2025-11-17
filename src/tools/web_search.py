"""Web search tool for accessing real-time information from the internet."""

from typing import List, Dict, Optional, Any
from .base import BaseTool, ToolResult, ToolPermissionLevel
import asyncio
from datetime import datetime


class WebSearchTool(BaseTool):
    """
    Web search tool with DuckDuckGo backend (no API key required).

    Features:
    - Free web search using DuckDuckGo
    - No API key or configuration required
    - Async execution
    - Rate limiting support
    - Result formatting optimized for LLM consumption

    Use cases:
    - Search for latest API documentation
    - Find error solutions on Stack Overflow
    - Check library versions and compatibility
    - Research best practices and tutorials
    """

    def __init__(
        self,
        max_results: int = 5,
        timeout: int = 10,
        region: str = "wt-wt",  # wt-wt = worldwide
        safe_search: str = "moderate"  # off, moderate, strict
    ):
        """
        Initialize WebSearchTool.

        Args:
            max_results: Maximum number of search results (1-10)
            timeout: Search timeout in seconds
            region: Search region code (e.g., 'us-en', 'uk-en', 'wt-wt')
            safe_search: Safe search level ('off', 'moderate', 'strict')
        """
        self.max_results = max_results
        self.timeout = timeout
        self.region = region
        self.safe_search = safe_search
        self._search_count = 0
        self._last_search_time = None

    @property
    def name(self) -> str:
        """Tool name for registration."""
        return "web_search"

    @property
    def description(self) -> str:
        """Tool description for LLM."""
        return (
            "Search the web for information, documentation, examples, and solutions. "
            "Use this tool when you need up-to-date information beyond your training data, "
            "such as latest API docs, error solutions, library versions, or current best practices. "
            "Returns a list of search results with titles, URLs, and snippets."
        )

    @property
    def permission_level(self) -> ToolPermissionLevel:
        """Permission level (NORMAL - requires network access)."""
        return ToolPermissionLevel.NORMAL

    @property
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search query string. Be specific and include relevant keywords. "
                        "Examples: 'Python asyncio best practices 2024', "
                        "'FastAPI dependency injection tutorial', "
                        "'fix ModuleNotFoundError pydantic.v1'"
                    )
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (1-10)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }

    async def execute(
        self,
        query: str,
        max_results: Optional[int] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute web search.

        Args:
            query: Search query string
            max_results: Maximum number of results (overrides default)
            **kwargs: Additional parameters (ignored)

        Returns:
            ToolResult with formatted search results or error
        """
        try:
            # Validate and normalize parameters
            max_results = max_results or self.max_results
            max_results = max(1, min(10, max_results))  # Clamp to [1, 10]

            if not query or not query.strip():
                return ToolResult(
                    success=False,
                    output="",
                    error="Search query cannot be empty"
                )

            query = query.strip()

            # Execute search
            results = await self._search_duckduckgo(query, max_results)

            if not results:
                return ToolResult(
                    success=True,
                    output="No results found. Try rephrasing your query or using different keywords.",
                    metadata={
                        "provider": "duckduckgo",
                        "query": query,
                        "result_count": 0
                    }
                )

            # Format results for LLM consumption
            formatted_output = self._format_results(results, query)

            # Update statistics
            self._search_count += 1
            self._last_search_time = datetime.now()

            return ToolResult(
                success=True,
                output=formatted_output,
                metadata={
                    "provider": "duckduckgo",
                    "query": query,
                    "result_count": len(results),
                    "max_results": max_results,
                    "timestamp": self._last_search_time.isoformat()
                }
            )

        except ImportError as e:
            return ToolResult(
                success=False,
                output="",
                error=(
                    "DuckDuckGo search library not installed. "
                    "Install with: pip install duckduckgo-search"
                )
            )
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output="",
                error=f"Search timed out after {self.timeout} seconds. Try again with a simpler query."
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Search failed: {str(e)}"
            )

    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, str]]:
        """
        Search using DuckDuckGo (no API key required).

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of result dictionaries with title, url, snippet
        """
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            raise ImportError("duckduckgo-search package not installed")

        results = []

        # Run DuckDuckGo search in executor to avoid blocking
        def _sync_search():
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query,
                    region=self.region,
                    safesearch=self.safe_search,
                    max_results=max_results
                )
                return list(search_results)

        # Execute in thread pool to avoid blocking async loop
        loop = asyncio.get_event_loop()
        search_results = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_search),
            timeout=self.timeout
        )

        # Normalize result format
        for result in search_results:
            results.append({
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "snippet": result.get("body", "")
            })

        return results

    def _format_results(
        self,
        results: List[Dict[str, str]],
        query: str
    ) -> str:
        """
        Format search results for LLM consumption.

        Args:
            results: List of search result dictionaries
            query: Original search query

        Returns:
            Formatted string with search results
        """
        if not results:
            return "No results found."

        lines = [
            f"Web search results for: '{query}'",
            f"Found {len(results)} result(s):",
            ""
        ]

        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            snippet = result.get("snippet", "No description available")

            # Clean up snippet
            snippet = snippet.replace("\n", " ").strip()
            if len(snippet) > 300:
                snippet = snippet[:297] + "..."

            lines.extend([
                f"{i}. {title}",
                f"   URL: {url}",
                f"   {snippet}",
                ""
            ])

        return "\n".join(lines)

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            Dictionary with usage statistics
        """
        return {
            "total_searches": self._search_count,
            "last_search_time": self._last_search_time.isoformat() if self._last_search_time else None,
            "provider": "duckduckgo",
            "max_results": self.max_results,
            "timeout": self.timeout
        }
