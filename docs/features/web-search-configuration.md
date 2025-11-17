# Web Search Tool - Configuration Guide

## Overview

The Web Search Tool supports three search providers:
1. **DuckDuckGo** (default, free, no API key required)
2. **Brave Search API** (premium, requires API key)
3. **Google Custom Search API** (premium, requires API key and search engine ID)

## Quick Start

### Option 1: DuckDuckGo (Default - No Configuration Required)

Works out of the box with zero configuration:

```python
from src.tools.web_search import WebSearchTool

tool = WebSearchTool()
result = await tool.execute(query="Python async best practices")
```

### Option 2: Brave Search API

Sign up for Brave Search API at: https://brave.com/search/api/

**Configuration:**

```python
from src.tools.web_search import WebSearchTool

tool = WebSearchTool(
    provider="brave",
    api_key="your-brave-api-key",
    max_results=5,
    timeout=10
)

result = await tool.execute(query="FastAPI tutorial")
```

**Free Tier:** 2,000 queries/month

### Option 3: Google Custom Search API

1. Get API key from: https://console.cloud.google.com/apis/credentials
2. Create custom search engine at: https://cse.google.com/cse/
3. Get your Search Engine ID (cx parameter)

**Configuration:**

```python
from src.tools.web_search import WebSearchTool

tool = WebSearchTool(
    provider="google",
    api_key="your-google-api-key",
    search_engine_id="your-search-engine-id",
    max_results=5,
    timeout=10
)

result = await tool.execute(query="React hooks tutorial")
```

**Free Tier:** 100 queries/day

## Configuration via settings.json

Add to `~/.tiny-claude-code/settings.json`:

```json
{
  "web_search": {
    "enabled": true,
    "provider": "duckduckgo",
    "api_key": null,
    "search_engine_id": null,
    "max_results": 5,
    "timeout": 10,
    "region": "wt-wt",
    "safe_search": "moderate"
  }
}
```

### Example Configurations

**Using DuckDuckGo (default):**
```json
{
  "web_search": {
    "enabled": true,
    "provider": "duckduckgo"
  }
}
```

**Using Brave Search:**
```json
{
  "web_search": {
    "enabled": true,
    "provider": "brave",
    "api_key": "your-brave-api-key"
  }
}
```

**Using Google Custom Search:**
```json
{
  "web_search": {
    "enabled": true,
    "provider": "google",
    "api_key": "your-google-api-key",
    "search_engine_id": "your-cx-id"
  }
}
```

## Environment Variables

Set API keys via environment variables for better security:

```bash
# For Brave Search
export BRAVE_SEARCH_API_KEY="your-brave-api-key"

# For Google Custom Search
export GOOGLE_SEARCH_API_KEY="your-google-api-key"
export GOOGLE_SEARCH_ENGINE_ID="your-cx-id"
```

Then reference in settings:

```json
{
  "web_search": {
    "provider": "brave",
    "api_key": "${BRAVE_SEARCH_API_KEY}"
  }
}
```

## Automatic Fallback

If a premium provider fails or is misconfigured, the tool automatically falls back to DuckDuckGo:

```python
# If Brave API fails, automatically uses DuckDuckGo
tool = WebSearchTool(provider="brave", api_key="invalid-key")
result = await tool.execute(query="test")
# Result will show: provider = "duckduckgo (fallback)"
```

## Parameters

### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | str | "duckduckgo" | Search provider ("duckduckgo", "brave", "google") |
| `api_key` | str | None | API key for premium providers |
| `search_engine_id` | str | None | Google Custom Search engine ID |
| `max_results` | int | 5 | Maximum results to return (1-10) |
| `timeout` | int | 10 | Request timeout in seconds |
| `region` | str | "wt-wt" | Search region (e.g., "us-en", "uk-en") |
| `safe_search` | str | "moderate" | Safe search level ("off", "moderate", "strict") |

### Provider-Specific Parameters

**DuckDuckGo:**
- `region`: Search region code
- `safe_search`: Content filtering level

**Brave Search:**
- `api_key`: Required for Brave Search API

**Google Custom Search:**
- `api_key`: Required for Google API
- `search_engine_id`: Required custom search engine ID

## Usage Examples

### Basic Search

```python
tool = WebSearchTool()
result = await tool.execute(query="Python asyncio tutorial")

if result.success:
    print(result.output)
    print(f"Provider: {result.metadata['provider']}")
    print(f"Results: {result.metadata['result_count']}")
```

### Limiting Results

```python
tool = WebSearchTool(max_results=3)
result = await tool.execute(query="FastAPI docs", max_results=5)  # Override default
```

### Regional Search

```python
tool = WebSearchTool(region="us-en")  # US English
result = await tool.execute(query="local news")
```

### Safe Search

```python
tool = WebSearchTool(safe_search="strict")  # Filter adult content
result = await tool.execute(query="educational content")
```

## Integration with Agent

Update `src/initialization/setup.py`:

```python
from src.tools import WebSearchTool

# In initialize_agent function:
web_search_config = config.get("web_search", {})
if web_search_config.get("enabled", True):
    web_search_tool = WebSearchTool(
        provider=web_search_config.get("provider", "duckduckgo"),
        api_key=web_search_config.get("api_key"),
        search_engine_id=web_search_config.get("search_engine_id"),
        max_results=web_search_config.get("max_results", 5),
        timeout=web_search_config.get("timeout", 10)
    )
    agent.tool_manager.register_tool(web_search_tool)
```

## Troubleshooting

### Issue: "httpx package not installed"

**Solution:**
```bash
pip install httpx
```

### Issue: "Brave Search API key not configured"

**Solution:**
1. Get API key from https://brave.com/search/api/
2. Add to settings.json or set environment variable
3. Ensure `provider="brave"` and `api_key` is set

### Issue: "Search timed out"

**Solution:**
- Increase timeout: `WebSearchTool(timeout=30)`
- Try simpler query
- Check internet connection

### Issue: Premium provider always fails

**Solution:**
- Verify API key is correct
- Check API quota/rate limits
- The tool will automatically fallback to DuckDuckGo

## Cost Comparison

| Provider | Free Tier | Paid Plans | Quality |
|----------|-----------|------------|---------|
| **DuckDuckGo** | Unlimited | N/A | Good |
| **Brave Search** | 2,000/month | $5/1,000 queries | Very Good |
| **Google Custom** | 100/day | $5/1,000 queries | Excellent |

## Best Practices

1. **Start with DuckDuckGo** - Test without configuration
2. **Use premium for production** - Better quality and reliability
3. **Set appropriate timeouts** - Balance speed vs reliability
4. **Monitor usage** - Track with `tool.get_usage_stats()`
5. **Use fallback** - Let the tool handle errors gracefully
6. **Secure API keys** - Use environment variables
7. **Limit results** - More results = slower + higher cost

## Performance

Typical search latency:
- **DuckDuckGo**: 1-3 seconds
- **Brave Search**: 0.5-2 seconds
- **Google Custom**: 0.3-1 seconds

## API Rate Limits

### DuckDuckGo
- No official limit
- Aggressive use may trigger temporary blocks
- Recommended: <10 requests/minute

### Brave Search
- Free tier: 1 request/second
- Paid tier: 10 requests/second

### Google Custom Search
- Free tier: 100 queries/day
- Paid tier: No limit (but costs apply)

## Security Considerations

1. **API Key Storage**
   - Use environment variables
   - Never commit to version control
   - Rotate keys regularly

2. **Rate Limiting**
   - Implement client-side rate limiting
   - Monitor usage to avoid quota exhaustion

3. **Input Validation**
   - Query sanitization is handled automatically
   - Max query length: 2048 characters

4. **Network Security**
   - All requests use HTTPS
   - Timeouts prevent hanging requests
