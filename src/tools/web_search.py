"""Web search tool for accessing real-time information from the internet."""

from typing import List, Dict, Optional, Any
from .base import BaseTool, ToolResult, ToolPermissionLevel
import asyncio
from datetime import datetime, timedelta
from collections import deque
import hashlib
import time
import random

# Import DDGS at module level to allow patching in tests
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS = None
    DDGS_AVAILABLE = False

# Import httpx for API-based searches
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

# Import BeautifulSoup for content fetching
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BS4_AVAILABLE = False


class WebSearchTool(BaseTool):
    """
    Web search tool with hybrid backend support and advanced features.

    Features:
    - Free web search using DuckDuckGo (default, no API key required)
    - Premium search via Brave Search API (optional)
    - Premium search via Google Custom Search API (optional)
    - Automatic fallback to DuckDuckGo if premium APIs fail
    - Async execution
    - Rate limiting (configurable requests per minute)
    - Result caching with TTL (configurable cache duration)
    - Result filtering and optimization
    - Full page content fetching (optional)
    - Result formatting optimized for LLM consumption

    Use cases:
    - Search for latest API documentation
    - Find error solutions on Stack Overflow
    - Check library versions and compatibility
    - Research best practices and tutorials
    """

    def __init__(
        self,
        provider: str = "duckduckgo",
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None,  # For Google Custom Search
        max_results: int = 5,
        timeout: int = 20,
        region: str = "wt-wt",  # wt-wt = worldwide
        safe_search: str = "moderate",  # off, moderate, strict
        rate_limit: int = 10,  # requests per minute
        cache_ttl: int = 3600,  # cache time-to-live in seconds (1 hour)
        enable_cache: bool = True,
        max_retries: int = 3,  # Maximum retry attempts
        retry_delay: float = 1.0  # Initial retry delay in seconds
    ):
        """
        Initialize WebSearchTool.

        Args:
            provider: Search provider ('duckduckgo', 'brave', 'google')
            api_key: API key for premium providers (Brave or Google)
            search_engine_id: Search engine ID for Google Custom Search
            max_results: Maximum number of search results (1-10)
            timeout: Search timeout in seconds
            region: Search region code (e.g., 'us-en', 'uk-en', 'wt-wt')
            safe_search: Safe search level ('off', 'moderate', 'strict')
            rate_limit: Maximum requests per minute (0 = no limit)
            cache_ttl: Cache time-to-live in seconds (0 = no cache)
            enable_cache: Enable/disable result caching
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.provider = provider.lower() if provider else "duckduckgo"
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.max_results = max_results
        self.timeout = timeout
        self.region = region
        self.safe_search = safe_search
        self.rate_limit = rate_limit
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Statistics
        self._search_count = 0
        self._last_search_time = None
        self._cache_hits = 0
        self._cache_misses = 0
        self._retry_count = 0
        self._failed_requests = 0

        # Rate limiting (sliding window)
        self._request_times: deque = deque()

        # Cache storage: {cache_key: (timestamp, results)}
        self._cache: Dict[str, tuple[float, List[Dict[str, str]]]] = {}

        # Auto-fallback to DuckDuckGo if premium provider specified but no API key
        if self.provider in ["brave", "google"] and not self.api_key:
            self.provider = "duckduckgo"

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

    def _generate_cache_key(self, query: str, max_results: int) -> str:
        """
        Generate cache key for query and parameters.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            Cache key string
        """
        key_data = f"{self.provider}:{query.lower()}:{max_results}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, str]]]:
        """
        Get cached results if available and not expired.

        Args:
            cache_key: Cache key

        Returns:
            Cached results or None if not found/expired
        """
        if not self.enable_cache or self.cache_ttl <= 0:
            return None

        if cache_key in self._cache:
            timestamp, results = self._cache[cache_key]
            age = time.time() - timestamp

            if age < self.cache_ttl:
                self._cache_hits += 1
                return results
            else:
                # Expired, remove from cache
                del self._cache[cache_key]

        self._cache_misses += 1
        return None

    def _cache_results(self, cache_key: str, results: List[Dict[str, str]]) -> None:
        """
        Cache search results.

        Args:
            cache_key: Cache key
            results: Search results to cache
        """
        if not self.enable_cache or self.cache_ttl <= 0:
            return

        self._cache[cache_key] = (time.time(), results)

    async def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting.

        Raises:
            Exception: If rate limit exceeded
        """
        if self.rate_limit <= 0:
            return

        current_time = time.time()
        cutoff_time = current_time - 60  # 1 minute window

        # Remove old timestamps outside the window
        while self._request_times and self._request_times[0] < cutoff_time:
            self._request_times.popleft()

        # Check if we're at the limit
        if len(self._request_times) >= self.rate_limit:
            oldest_request = self._request_times[0]
            wait_time = 60 - (current_time - oldest_request)
            raise Exception(
                f"Rate limit exceeded: {self.rate_limit} requests per minute. "
                f"Please wait {wait_time:.1f} seconds."
            )

        # Add current request
        self._request_times.append(current_time)

    def clear_cache(self) -> int:
        """
        Clear all cached results.

        Returns:
            Number of items cleared
        """
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self._cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": (
                self._cache_hits / (self._cache_hits + self._cache_misses)
                if (self._cache_hits + self._cache_misses) > 0
                else 0.0
            )
        }

    async def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result from function

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except (asyncio.TimeoutError, ConnectionError, Exception) as e:
                last_exception = e
                self._retry_count += 1

                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff with jitter
                    delay = self.retry_delay * \
                        (2 ** attempt) + random.uniform(0, 0.1)
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    self._failed_requests += 1
                    raise last_exception

        # Should never reach here, but just in case
        self._failed_requests += 1
        raise last_exception if last_exception else Exception(
            "All retries exhausted")

    async def execute(
        self,
        query: str,
        max_results: Optional[int] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute web search using configured provider with fallback support.

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

            # Check cache first (before rate limiting)
            cache_key = self._generate_cache_key(query, max_results)
            cached_results = self._get_cached_results(cache_key)

            if cached_results is not None:
                # Return cached results (no rate limit check needed)
                formatted_output = self._format_results(cached_results, query)
                return ToolResult(
                    success=True,
                    output=formatted_output,
                    metadata={
                        "provider": f"{self.provider} (cached)",
                        "query": query,
                        "result_count": len(cached_results),
                        "max_results": max_results,
                        "cached": True,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # Check rate limit (only for non-cached requests)
            await self._check_rate_limit()

            # Try primary provider with retry logic
            results = None
            used_provider = self.provider
            error_message = None

            try:
                if self.provider == "brave":
                    results = await self._retry_with_backoff(self._search_brave, query, max_results)
                elif self.provider == "google":
                    results = await self._retry_with_backoff(self._search_google, query, max_results)
                else:  # duckduckgo
                    results = await self._retry_with_backoff(self._search_duckduckgo, query, max_results)
            except Exception as e:
                error_message = str(e)
                # If premium provider fails, fallback to DuckDuckGo with retry
                if self.provider in ["brave", "google"]:
                    try:
                        results = await self._retry_with_backoff(self._search_duckduckgo, query, max_results)
                        used_provider = "duckduckgo (fallback)"
                    except Exception as fallback_error:
                        # Both failed
                        raise Exception(
                            f"Primary provider failed: {error_message}. Fallback failed: {str(fallback_error)}")
                else:
                    raise

            # Cache results (even if empty)
            if results is not None:
                self._cache_results(cache_key, results)

            # Update statistics (regardless of results)
            self._search_count += 1
            self._last_search_time = datetime.now()

            if not results:
                return ToolResult(
                    success=True,
                    output="No results found. Try rephrasing your query or using different keywords.",
                    metadata={
                        "provider": used_provider,
                        "query": query,
                        "result_count": 0,
                        "cached": False,
                        "timestamp": self._last_search_time.isoformat()
                    }
                )

            # Format results for LLM consumption
            formatted_output = self._format_results(results, query)

            return ToolResult(
                success=True,
                output=formatted_output,
                metadata={
                    "provider": used_provider,
                    "query": query,
                    "result_count": len(results),
                    "max_results": max_results,
                    "cached": False,
                    "timestamp": self._last_search_time.isoformat()
                }
            )

        except ImportError as e:
            return ToolResult(
                success=False,
                output="",
                error=(
                    "Search library not installed. "
                    "Install with: pip install duckduckgo-search httpx"
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
        # Check if DDGS is available (allow patching in tests)
        if DDGS is None:
            raise ImportError("ddgs package not installed. Use 'pip install ddgs'.")

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

    async def _search_brave(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, str]]:
        """
        Search using Brave Search API.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of result dictionaries with title, url, snippet

        Raises:
            ImportError: If httpx is not installed
            Exception: If API request fails
        """
        if not HTTPX_AVAILABLE or httpx is None:
            raise ImportError(
                "httpx package not installed. Install with: pip install httpx")

        if not self.api_key:
            raise ValueError("Brave Search API key not configured")

        results = []

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": max_results},
                headers={"X-Subscription-Token": self.api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            # Extract web results
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", "")
                })

        return results

    async def _search_google(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, str]]:
        """
        Search using Google Custom Search API.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of result dictionaries with title, url, snippet

        Raises:
            ImportError: If httpx is not installed
            Exception: If API request fails
        """
        if not HTTPX_AVAILABLE or httpx is None:
            raise ImportError(
                "httpx package not installed. Install with: pip install httpx")

        if not self.api_key:
            raise ValueError("Google Custom Search API key not configured")

        if not self.search_engine_id:
            raise ValueError("Google Custom Search engine ID not configured")

        results = []

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": self.api_key,
                    "cx": self.search_engine_id,
                    "q": query,
                    "num": max_results
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            # Extract search results
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
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
            title = result.get("title", "") or "Untitled"
            url = result.get("url", "")
            snippet = result.get("snippet", "") or "No description available"

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
        Get usage statistics including cache performance and retry metrics.

        Returns:
            Dictionary with usage statistics
        """
        cache_stats = self.get_cache_stats()
        return {
            "total_searches": self._search_count,
            "last_search_time": self._last_search_time.isoformat() if self._last_search_time else None,
            "provider": self.provider,
            "max_results": self.max_results,
            "timeout": self.timeout,
            "rate_limit": self.rate_limit,
            "cache_enabled": self.enable_cache,
            "cache_ttl": self.cache_ttl,
            "max_retries": self.max_retries,
            "retry_count": self._retry_count,
            "failed_requests": self._failed_requests,
            **cache_stats
        }
