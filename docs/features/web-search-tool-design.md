# Web Search Tool - Design Document

**Feature:** Web Search Tool for Context Enhancement
**Priority:** High
**Status:** Proposal
**Author:** Development Team
**Date:** 2025-11-17

---

## 1. Executive Summary

### 1.1 Problem Statement

Current built-in tools (7 total):
- ✅ **File Operations**: Read, Write, Edit
- ✅ **Code Search**: Glob, Grep
- ✅ **Execution**: Bash
- ✅ **Task Management**: TodoWrite
- ❌ **Web Search**: Missing

**Gap:** No ability to search the web for:
- Latest API documentation
- Library usage examples
- Error message solutions
- Best practices and tutorials
- Package version information
- Security advisories

**Impact:**
- Agent relies only on training data (knowledge cutoff: January 2025)
- Cannot access real-time information
- Cannot verify latest library versions
- Cannot fetch updated documentation

### 1.2 Solution

Add **WebSearchTool** as an 8th built-in tool with capabilities:
1. **Search Query**: Execute web searches for relevant information
2. **Content Fetch**: Retrieve and parse web page content
3. **Result Filtering**: Extract relevant snippets
4. **Source Attribution**: Track information sources

### 1.3 Value Proposition

**For Users:**
- 🌐 Access to latest documentation
- 📚 Real-time library examples
- 🔍 Error message solutions from Stack Overflow
- ⚡ Faster problem resolution

**For Agent:**
- 📖 Augment context with fresh information
- 🎯 Reduce hallucination on recent APIs
- ✅ Verify information accuracy
- 🔄 Self-correct outdated knowledge

---

## 2. Current State Analysis

### 2.1 Existing Tools

```python
# src/tools/__init__.py
__all__ = [
    "ReadTool",      # File reading
    "WriteTool",     # File writing
    "EditTool",      # File editing
    "BashTool",      # Shell execution
    "GlobTool",      # File pattern search
    "GrepTool",      # Content search
    "TodoWriteTool", # Task management
]
```

**Total: 7 tools**

### 2.2 Tool Permission Levels

```python
class ToolPermissionLevel(Enum):
    SAFE = "safe"          # Auto-approved in AUTO_APPROVE_SAFE mode
    NORMAL = "normal"      # Requires approval
    DANGEROUS = "dangerous" # Always requires approval
```

**Current Distribution:**
- **SAFE**: ReadTool, GlobTool, GrepTool, TodoWriteTool (4 tools)
- **NORMAL**: WriteTool, EditTool (2 tools)
- **DANGEROUS**: BashTool (1 tool)

**Web Search Tool Permission:** `NORMAL` (requires network access)

### 2.3 Architecture Fit

```
┌─────────────────────────────────────────────┐
│ EnhancedAgent                               │
│  ├─ ToolManager                             │
│  │   ├─ Built-in Tools (7)                  │
│  │   │   ├─ File Operations (3)             │
│  │   │   ├─ Search (2)                      │
│  │   │   ├─ Bash (1)                        │
│  │   │   ├─ Todo (1)                        │
│  │   │   └─ Web Search (NEW) ← Add here    │
│  │   └─ MCP Tools (dynamic)                 │
│  └─ Permission Manager                      │
└─────────────────────────────────────────────┘
```

---

## 3. Design Options

### Option 1: Lightweight Wrapper (Recommended)

**Approach:** Use existing Python libraries for web search

**Pros:**
- ✅ Fast implementation (1-2 days)
- ✅ No external service dependencies
- ✅ Works offline with cached results
- ✅ Free to use
- ✅ Full control over implementation

**Cons:**
- ⚠️ Requires HTTP scraping (may be rate-limited)
- ⚠️ Search quality depends on scraping strategy
- ⚠️ May need to handle CAPTCHAs

**Implementation:**
```python
import requests
from bs4 import BeautifulSoup

class WebSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def permission_level(self) -> ToolPermissionLevel:
        return ToolPermissionLevel.NORMAL

    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        # Use DuckDuckGo (no API key required)
        results = await self._search_duckduckgo(query, max_results)
        return ToolResult(
            success=True,
            output=self._format_results(results)
        )
```

**Libraries:**
- `duckduckgo-search` - Simple, no API key
- `beautifulsoup4` - HTML parsing
- `requests` or `httpx` - HTTP client

### Option 2: Search API Integration

**Approach:** Use commercial search APIs

**Options:**
- **Google Custom Search API** (100 queries/day free, then $5/1000 queries)
- **Bing Web Search API** (1000 queries/month free on Azure)
- **Brave Search API** (2000 queries/month free)
- **SerpAPI** (100 queries/month free, then paid)

**Pros:**
- ✅ High-quality search results
- ✅ Structured data (JSON)
- ✅ Reliable and fast
- ✅ No scraping required

**Cons:**
- ❌ Requires API key
- ❌ Usage limits and costs
- ❌ External dependency
- ❌ User configuration needed

**Implementation:**
```python
class WebSearchTool(BaseTool):
    def __init__(self, api_key: str, provider: str = "brave"):
        self.api_key = api_key
        self.provider = provider

    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        if self.provider == "brave":
            results = await self._search_brave(query, max_results)
        elif self.provider == "google":
            results = await self._search_google(query, max_results)
        # ...
```

### Option 3: Hybrid Approach (Best)

**Approach:** Combine both options with fallback

**Flow:**
```
1. Check if API key configured
   ├─ Yes → Use API (high quality)
   └─ No  → Use DuckDuckGo scraping (fallback)
```

**Pros:**
- ✅ Works out of the box (no API key required)
- ✅ Better results when API key provided
- ✅ Flexible configuration
- ✅ Gradual upgrade path

**Cons:**
- ⚠️ More complex implementation
- ⚠️ Need to maintain both paths

---

## 4. Recommended Design

### 4.1 Architecture

**Choice:** Option 3 (Hybrid Approach)

**Rationale:**
1. Zero-configuration for basic usage
2. High-quality results for power users
3. Flexible and future-proof

### 4.2 Tool Definition

```python
# src/tools/web_search.py

from typing import List, Dict, Optional
from .base import BaseTool, ToolResult, ToolPermissionLevel
import httpx
from bs4 import BeautifulSoup
import json

class WebSearchTool(BaseTool):
    """
    Web search tool with hybrid backend:
    - Free: DuckDuckGo HTML scraping
    - Premium: Brave/Google Search API (if API key configured)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "duckduckgo",
        max_results: int = 5,
        timeout: int = 10
    ):
        self.api_key = api_key
        self.provider = provider if api_key else "duckduckgo"
        self.max_results = max_results
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web for information, documentation, examples, "
            "and solutions. Use when you need up-to-date information "
            "beyond your training data."
        )

    @property
    def permission_level(self) -> ToolPermissionLevel:
        return ToolPermissionLevel.NORMAL

    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (1-10)",
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
        max_results: Optional[int] = None
    ) -> ToolResult:
        """Execute web search"""
        try:
            max_results = max_results or self.max_results

            if self.provider == "duckduckgo":
                results = await self._search_duckduckgo(query, max_results)
            elif self.provider == "brave":
                results = await self._search_brave(query, max_results)
            elif self.provider == "google":
                results = await self._search_google(query, max_results)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown provider: {self.provider}"
                )

            formatted = self._format_results(results)

            return ToolResult(
                success=True,
                output=formatted,
                metadata={
                    "provider": self.provider,
                    "result_count": len(results),
                    "query": query
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Search failed: {str(e)}"
            )

    async def _search_duckduckgo(
        self,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """Search using DuckDuckGo HTML scraping"""
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result["title"],
                    "url": result["href"],
                    "snippet": result["body"]
                })

        return results

    async def _search_brave(
        self,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """Search using Brave Search API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": max_results},
                headers={"X-Subscription-Token": self.api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item["title"],
                    "url": item["url"],
                    "snippet": item["description"]
                })

            return results

    async def _search_google(
        self,
        query: str,
        max_results: int
    ) -> List[Dict]:
        """Search using Google Custom Search API"""
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

            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item["title"],
                    "url": item["link"],
                    "snippet": item["snippet"]
                })

            return results

    def _format_results(self, results: List[Dict]) -> str:
        """Format search results for LLM consumption"""
        if not results:
            return "No results found."

        output = []
        for i, result in enumerate(results, 1):
            output.append(f"{i}. {result['title']}")
            output.append(f"   URL: {result['url']}")
            output.append(f"   {result['snippet']}")
            output.append("")

        return "\n".join(output)
```

### 4.3 Configuration

```json
// ~/.tiny-claude-code/settings.json
{
  "web_search": {
    "enabled": true,
    "provider": "duckduckgo",  // "duckduckgo", "brave", "google"
    "api_key": null,            // Optional: for premium providers
    "search_engine_id": null,   // Optional: for Google Custom Search
    "max_results": 5,
    "timeout": 10,
    "rate_limit": {
      "requests_per_minute": 10
    }
  }
}
```

### 4.4 Registration

```python
# src/initialization/setup.py

from ..tools import (
    ReadTool, WriteTool, EditTool,
    BashTool, GlobTool, GrepTool,
    TodoWriteTool, WebSearchTool  # NEW
)

async def initialize_agent(config: dict = None, args=None) -> EnhancedAgent:
    # ...

    # Initialize web search tool
    web_search_config = config.get("web_search", {})
    if web_search_config.get("enabled", True):
        web_search_tool = WebSearchTool(
            api_key=web_search_config.get("api_key"),
            search_engine_id=web_search_config.get("search_engine_id"),
            provider=web_search_config.get("provider", "duckduckgo"),
            max_results=web_search_config.get("max_results", 5),
            timeout=web_search_config.get("timeout", 10)
        )

    agent.tool_manager.register_tools([
        ReadTool(), WriteTool(), EditTool(),
        BashTool(), GlobTool(), GrepTool(),
        TodoWriteTool(agent.todo_manager),
        web_search_tool  # NEW
    ])
```

---

## 5. Use Cases

### 5.1 Documentation Lookup

**Scenario:** User asks about a new API

**Without Web Search:**
```
User: How do I use the new FastAPI dependency injection?
Agent: [Based on training data from 2024, might be outdated]
```

**With Web Search:**
```
User: How do I use the new FastAPI dependency injection?
Agent: Let me search for the latest FastAPI documentation...
      [Uses web_search tool]
      [Retrieves official docs]
      Here's how to use dependency injection in FastAPI 0.115+: ...
```

### 5.2 Error Resolution

**Scenario:** Debugging an error message

**Without Web Search:**
```
User: I'm getting "ModuleNotFoundError: No module named 'pydantic.v1'"
Agent: [Guesses based on training data]
```

**With Web Search:**
```
User: I'm getting "ModuleNotFoundError: No module named 'pydantic.v1'"
Agent: Let me search for this error...
      [Searches Stack Overflow]
      This error occurs in Pydantic v2. Solution: ...
```

### 5.3 Library Version Check

**Scenario:** Check latest package version

**Without Web Search:**
```
User: What's the latest version of pytest?
Agent: As of my training data, pytest 7.4 is recent... [outdated]
```

**With Web Search:**
```
User: What's the latest version of pytest?
Agent: [Searches PyPI or GitHub]
      The latest version is pytest 8.0.2 (released Feb 2024)
```

### 5.4 Best Practices

**Scenario:** Learn current best practices

**Without Web Search:**
```
User: What are the best practices for async Python in 2025?
Agent: [Limited to training data]
```

**With Web Search:**
```
User: What are the best practices for async Python in 2025?
Agent: [Searches recent blog posts and articles]
      According to recent Python community discussions...
```

---

## 6. Implementation Plan

### Phase 1: Basic Implementation (2-3 days)

**Tasks:**
1. ✅ Create `src/tools/web_search.py`
2. ✅ Implement DuckDuckGo backend
3. ✅ Add tool registration
4. ✅ Write unit tests (20+ tests)
5. ✅ Update documentation

**Deliverables:**
- Working WebSearchTool with DuckDuckGo
- Unit tests with 80%+ coverage
- User documentation

### Phase 2: Premium Backends (1-2 days)

**Tasks:**
1. ✅ Implement Brave Search API
2. ✅ Implement Google Custom Search
3. ✅ Add configuration support
4. ✅ Add fallback mechanism
5. ✅ Update tests

**Deliverables:**
- Multi-provider support
- Configuration examples
- Integration tests

### Phase 3: Enhancement (1 day)

**Tasks:**
1. ✅ Add rate limiting
2. ✅ Add result caching
3. ✅ Add content fetching (fetch full page)
4. ✅ Add result filtering
5. ✅ Performance optimization

**Deliverables:**
- Production-ready tool
- Performance benchmarks
- Complete test coverage

### Phase 4: Polish (1 day)

**Tasks:**
1. ✅ Add retry logic
2. ✅ Add error handling
3. ✅ Add usage statistics
4. ✅ Documentation polish
5. ✅ Example usage in README

**Total Estimated Time:** 5-7 days

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/unit/test_web_search.py

class TestWebSearchTool:
    def test_tool_initialization(self):
        tool = WebSearchTool()
        assert tool.name == "web_search"
        assert tool.permission_level == ToolPermissionLevel.NORMAL

    def test_search_duckduckgo(self):
        tool = WebSearchTool(provider="duckduckgo")
        result = await tool.execute(query="Python testing")
        assert result.success
        assert len(result.output) > 0

    def test_search_with_api_key(self):
        tool = WebSearchTool(
            api_key="test-key",
            provider="brave"
        )
        # Mock API response
        result = await tool.execute(query="FastAPI docs")
        assert result.success

    def test_format_results(self):
        tool = WebSearchTool()
        results = [
            {"title": "Test", "url": "http://test.com", "snippet": "Test snippet"}
        ]
        formatted = tool._format_results(results)
        assert "Test" in formatted
        assert "http://test.com" in formatted

    def test_error_handling(self):
        tool = WebSearchTool(provider="invalid")
        result = await tool.execute(query="test")
        assert not result.success
        assert "Unknown provider" in result.error
```

**Coverage Target:** 85%+

### 7.2 Integration Tests

```python
# tests/integration/test_web_search_integration.py

class TestWebSearchIntegration:
    async def test_agent_uses_web_search(self):
        agent = await initialize_agent()

        # Verify tool is registered
        assert agent.tool_manager.has_tool("web_search")

        # Execute search
        response = await agent.run(
            "Search for Python 3.12 new features"
        )

        # Verify search was used
        assert "web_search" in str(response.tool_calls)

    async def test_search_result_in_context(self):
        agent = await initialize_agent()

        response = await agent.run(
            "What's new in FastAPI 0.115?"
        )

        # Agent should use web_search to get latest info
        # Verify response contains recent information
        assert response.success
```

### 7.3 Performance Tests

```python
# tests/test_sessions/test_performance.py (extend)

class TestWebSearchPerformance:
    def test_search_latency(self):
        tool = WebSearchTool()

        start = time.time()
        result = await tool.execute(query="test", max_results=5)
        elapsed = time.time() - start

        # Should complete in under 3 seconds
        assert elapsed < 3.0

    def test_concurrent_searches(self):
        tool = WebSearchTool()

        tasks = [
            tool.execute(query=f"test {i}")
            for i in range(10)
        ]

        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # 10 concurrent searches should complete in <5s
        assert elapsed < 5.0
        assert all(r.success for r in results)
```

---

## 8. Dependencies

### 8.1 Required

```toml
# pyproject.toml or requirements.txt

# Web search (no API key)
duckduckgo-search>=4.0.0

# HTTP client
httpx>=0.25.0

# HTML parsing
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### 8.2 Optional (for premium providers)

```toml
# Brave Search API
# No additional package needed (httpx sufficient)

# Google Custom Search
# No additional package needed (httpx sufficient)
```

**Total Size Impact:** ~5-10 MB

---

## 9. Security Considerations

### 9.1 Risks

1. **SSRF (Server-Side Request Forgery)**
   - Tool could be tricked into fetching internal URLs
   - Mitigation: URL validation, whitelist domains

2. **Rate Limiting**
   - Excessive searches could trigger rate limits
   - Mitigation: Local rate limiter, caching

3. **Malicious Content**
   - Search results could contain malicious links
   - Mitigation: URL sanitization, content filtering

4. **Privacy**
   - Search queries might leak sensitive information
   - Mitigation: Warn users, allow opt-out

5. **API Key Exposure**
   - API keys in config could be leaked
   - Mitigation: Use environment variables, permissions

### 9.2 Mitigations

```python
class WebSearchTool(BaseTool):
    # URL validation
    BLOCKED_DOMAINS = [
        "localhost", "127.0.0.1", "0.0.0.0",
        "*.local", "*.internal"
    ]

    # Rate limiting
    RATE_LIMIT = 10  # requests per minute

    def _validate_url(self, url: str) -> bool:
        """Validate URL is safe to fetch"""
        parsed = urlparse(url)

        # Block internal IPs
        if parsed.hostname in self.BLOCKED_DOMAINS:
            return False

        # Block file:// protocol
        if parsed.scheme not in ["http", "https"]:
            return False

        return True

    async def _rate_limit_check(self):
        """Enforce rate limiting"""
        # Implement token bucket or sliding window
        pass
```

### 9.3 Permission Level

**Recommendation:** `ToolPermissionLevel.NORMAL`

**Rationale:**
- Requires network access (not SAFE)
- Not destructive (not DANGEROUS)
- User should be aware when web searches happen

---

## 10. Documentation Updates

### 10.1 README.md

```markdown
## 🚀 Quick Start

### Core Features

- **Intelligent Input Enhancement** - ...
- **Beautiful Output Enhancement** - ...
- **Complete Tool System** - 8 built-in tools + MCP integration
  - File Operations: Read, Write, Edit
  - Code Search: Glob, Grep
  - Execution: Bash
  - Task Management: TodoWrite
  - **Web Search**: Search the web for docs, examples, solutions (NEW)
- ...

### Tools Available

| Tool | Description | Permission |
|------|-------------|------------|
| ... | ... | ... |
| **web_search** | Search web for information | NORMAL |
```

### 10.2 Development Guide

```markdown
## Adding New Tools

### Example: Web Search Tool

\`\`\`python
from src.tools import WebSearchTool

# Basic usage (DuckDuckGo)
tool = WebSearchTool()
result = await tool.execute(query="Python async best practices")

# With API key (Brave Search)
tool = WebSearchTool(
    api_key="your-brave-api-key",
    provider="brave"
)
result = await tool.execute(query="FastAPI 0.115 features")
\`\`\`
```

---

## 11. Alternatives Considered

### 11.1 MCP Server for Web Search

**Approach:** Implement as external MCP server instead of built-in tool

**Pros:**
- Separation of concerns
- Can be developed independently
- Reusable across different agents

**Cons:**
- Requires MCP setup (more complex for users)
- Not available out of the box
- Adds external dependency

**Decision:** Reject - Web search is fundamental enough to be built-in

### 11.2 Browser Automation (Playwright/Selenium)

**Approach:** Use full browser automation for searches

**Pros:**
- Can handle JavaScript-heavy sites
- More reliable scraping
- Can interact with pages

**Cons:**
- Heavy dependency (100+ MB)
- Slow execution (seconds per search)
- Complex setup
- Resource intensive

**Decision:** Reject - Too heavy for basic search

### 11.3 Custom Search Engine

**Approach:** Build and maintain our own search index

**Pros:**
- Full control
- No rate limits
- Fast

**Cons:**
- Requires infrastructure
- Maintenance burden
- Expensive (crawling, indexing, storage)

**Decision:** Reject - Not feasible for open source project

---

## 12. Success Metrics

### 12.1 Adoption Metrics

- **Tool Usage:** >20% of sessions use web_search
- **User Satisfaction:** >80% positive feedback
- **Error Rate:** <5% search failures

### 12.2 Technical Metrics

- **Search Latency:** <2 seconds (p95)
- **Result Quality:** >3 relevant results per search
- **Test Coverage:** >85%
- **Uptime:** >99% (for DuckDuckGo fallback)

### 12.3 Cost Metrics (if using paid APIs)

- **API Costs:** <$10/month for typical usage
- **Free Tier Usage:** >90% of searches use free tier

---

## 13. Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Rate limiting | Medium | Medium | Local rate limiter, caching |
| API key costs | Low | Medium | Default to free DuckDuckGo |
| Search quality | Medium | High | Hybrid approach, multiple providers |
| Security issues | Low | High | URL validation, content filtering |
| Maintenance | Medium | Low | Simple implementation, good tests |

---

## 14. Open Questions

1. **Should we fetch full page content?**
   - Pro: More context for agent
   - Con: Slower, more bandwidth
   - **Decision:** Phase 3 feature, optional

2. **Should we cache search results?**
   - Pro: Faster, fewer API calls
   - Con: Stale information
   - **Decision:** Yes, with TTL (e.g., 1 hour)

3. **Should we allow custom search providers?**
   - Pro: Flexibility
   - Con: More complexity
   - **Decision:** Yes, plugin architecture

4. **Should we add image search?**
   - Pro: Useful for UI development
   - Con: Increased complexity
   - **Decision:** Future consideration

---

## 15. Conclusion

### 15.1 Recommendation

**✅ APPROVED FOR IMPLEMENTATION**

**Priority:** High
**Estimated Effort:** 5-7 days
**Risk Level:** Low
**Value:** High

### 15.2 Next Steps

1. ✅ Get approval from team
2. 📋 Create implementation task
3. 📋 Assign developer
4. 📋 Set milestone deadline
5. 📋 Begin Phase 1 implementation

### 15.3 Success Criteria

- ✅ Web search tool integrated as 8th built-in tool
- ✅ Works out of the box with DuckDuckGo
- ✅ Supports premium providers (Brave, Google)
- ✅ 85%+ test coverage
- ✅ <2s search latency
- ✅ Documentation updated
- ✅ User feedback positive

---

**Document Status:** Proposal
**Next Review:** After Phase 1 implementation
**Owner:** Development Team
