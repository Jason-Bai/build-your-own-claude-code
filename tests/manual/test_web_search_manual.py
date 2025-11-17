"""Manual test script for Web Search Tool with DuckDuckGo

Run this script to test real-world search scenarios based on the design document.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tools.web_search import WebSearchTool


async def test_documentation_lookup():
    """Test Case 1: Documentation Lookup (Use Case 5.1)"""
    print("\n" + "="*80)
    print("TEST 1: Documentation Lookup")
    print("="*80)
    print("Scenario: User asks about FastAPI dependency injection")
    print("-"*80)

    tool = WebSearchTool(provider="duckduckgo", max_results=3)

    query = "FastAPI dependency injection tutorial"
    print(f"\nSearching for: '{query}'")

    result = await tool.execute(query=query)

    if result.success:
        print(f"\n✅ Search succeeded!")
        print(f"Provider: {result.metadata['provider']}")
        print(f"Results found: {result.metadata['result_count']}")
        print(f"\n{result.output}")
    else:
        print(f"\n❌ Search failed: {result.error}")

    return result.success


async def test_error_resolution():
    """Test Case 2: Error Resolution (Use Case 5.2)"""
    print("\n" + "="*80)
    print("TEST 2: Error Resolution")
    print("="*80)
    print("Scenario: Debugging an error message")
    print("-"*80)

    tool = WebSearchTool(provider="duckduckgo", max_results=3)

    query = "ModuleNotFoundError pydantic.v1 solution"
    print(f"\nSearching for: '{query}'")

    result = await tool.execute(query=query)

    if result.success:
        print(f"\n✅ Search succeeded!")
        print(f"Provider: {result.metadata['provider']}")
        print(f"Results found: {result.metadata['result_count']}")
        print(f"\n{result.output}")
    else:
        print(f"\n❌ Search failed: {result.error}")

    return result.success


async def test_version_check():
    """Test Case 3: Library Version Check (Use Case 5.3)"""
    print("\n" + "="*80)
    print("TEST 3: Library Version Check")
    print("="*80)
    print("Scenario: Check latest package version")
    print("-"*80)

    tool = WebSearchTool(provider="duckduckgo", max_results=3)

    query = "pytest latest version 2025"
    print(f"\nSearching for: '{query}'")

    result = await tool.execute(query=query)

    if result.success:
        print(f"\n✅ Search succeeded!")
        print(f"Provider: {result.metadata['provider']}")
        print(f"Results found: {result.metadata['result_count']}")
        print(f"\n{result.output}")
    else:
        print(f"\n❌ Search failed: {result.error}")

    return result.success


async def test_best_practices():
    """Test Case 4: Best Practices (Use Case 5.4)"""
    print("\n" + "="*80)
    print("TEST 4: Best Practices")
    print("="*80)
    print("Scenario: Learn current best practices")
    print("-"*80)

    tool = WebSearchTool(provider="duckduckgo", max_results=3)

    query = "Python async best practices 2025"
    print(f"\nSearching for: '{query}'")

    result = await tool.execute(query=query)

    if result.success:
        print(f"\n✅ Search succeeded!")
        print(f"Provider: {result.metadata['provider']}")
        print(f"Results found: {result.metadata['result_count']}")
        print(f"\n{result.output}")
    else:
        print(f"\n❌ Search failed: {result.error}")

    return result.success


async def test_caching():
    """Test Case 5: Cache Performance"""
    print("\n" + "="*80)
    print("TEST 5: Cache Performance")
    print("="*80)
    print("Scenario: Test cache hit performance")
    print("-"*80)

    tool = WebSearchTool(provider="duckduckgo", enable_cache=True, cache_ttl=300)

    query = "Python testing frameworks comparison"

    # First search (cache miss)
    print(f"\nFirst search (cache miss): '{query}'")
    import time
    start = time.time()
    result1 = await tool.execute(query=query, max_results=3)
    time1 = time.time() - start

    if result1.success:
        print(f"✅ Time: {time1:.2f}s")
        print(f"Cached: {result1.metadata.get('cached', False)}")

    # Second search (cache hit)
    print(f"\nSecond search (cache hit): '{query}'")
    start = time.time()
    result2 = await tool.execute(query=query, max_results=3)
    time2 = time.time() - start

    if result2.success:
        print(f"✅ Time: {time2:.2f}s")
        print(f"Cached: {result2.metadata.get('cached', False)}")
        print(f"Speedup: {time1/time2:.1f}x faster")

    # Show cache stats
    stats = tool.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Cache hits: {stats['cache_hits']}")
    print(f"  Cache misses: {stats['cache_misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")

    return result1.success and result2.success


async def test_rate_limiting():
    """Test Case 6: Rate Limiting"""
    print("\n" + "="*80)
    print("TEST 6: Rate Limiting")
    print("="*80)
    print("Scenario: Test rate limit enforcement")
    print("-"*80)

    tool = WebSearchTool(provider="duckduckgo", rate_limit=3, max_results=2)

    queries = [
        "Python async tutorial",
        "FastAPI documentation",
        "pytest examples",
        "This should be rate limited"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\nSearch {i}: '{query}'")
        result = await tool.execute(query=query)

        if result.success:
            print(f"✅ Search succeeded")
        else:
            print(f"❌ Search failed: {result.error}")
            if "rate limit" in result.error.lower():
                print("   (Expected - rate limit hit)")

    stats = tool.get_usage_stats()
    print(f"\nRate Limit Statistics:")
    print(f"  Total searches attempted: {len(queries)}")
    print(f"  Successful searches: {stats['total_searches']}")
    print(f"  Rate limit: {stats['rate_limit']} req/min")

    return True


async def test_retry_logic():
    """Test Case 7: Retry Logic"""
    print("\n" + "="*80)
    print("TEST 7: Retry Logic")
    print("="*80)
    print("Scenario: Test retry on transient failures")
    print("-"*80)

    tool = WebSearchTool(
        provider="duckduckgo",
        max_retries=3,
        retry_delay=0.5,
        max_results=2
    )

    query = "Python web scraping tutorial"
    print(f"\nSearching for: '{query}'")

    result = await tool.execute(query=query)

    if result.success:
        print(f"\n✅ Search succeeded!")
        print(f"Results found: {result.metadata['result_count']}")
    else:
        print(f"\n❌ Search failed: {result.error}")

    stats = tool.get_usage_stats()
    print(f"\nRetry Statistics:")
    print(f"  Total retries: {stats['retry_count']}")
    print(f"  Failed requests: {stats['failed_requests']}")
    print(f"  Max retries configured: {stats['max_retries']}")

    return result.success


async def test_comprehensive_stats():
    """Test Case 8: Comprehensive Statistics"""
    print("\n" + "="*80)
    print("TEST 8: Comprehensive Statistics")
    print("="*80)
    print("Scenario: View all tool statistics")
    print("-"*80)

    tool = WebSearchTool(
        provider="duckduckgo",
        max_results=3,
        enable_cache=True,
        cache_ttl=300,
        rate_limit=10,
        max_retries=3
    )

    # Perform some searches
    queries = [
        "Python type hints guide",
        "Python type hints guide",  # Same query for cache hit
        "asyncio tutorial Python"
    ]

    for query in queries:
        await tool.execute(query=query)

    # Get comprehensive stats
    stats = tool.get_usage_stats()

    print("\n📊 Tool Statistics:")
    print(f"\n  General:")
    print(f"    Provider: {stats['provider']}")
    print(f"    Total searches: {stats['total_searches']}")
    print(f"    Max results per search: {stats['max_results']}")
    print(f"    Timeout: {stats['timeout']}s")

    print(f"\n  Cache:")
    print(f"    Enabled: {stats['cache_enabled']}")
    print(f"    TTL: {stats['cache_ttl']}s")
    print(f"    Cache size: {stats['cache_size']} entries")
    print(f"    Cache hits: {stats['cache_hits']}")
    print(f"    Cache misses: {stats['cache_misses']}")
    print(f"    Hit rate: {stats['hit_rate']:.1%}")

    print(f"\n  Rate Limiting:")
    print(f"    Limit: {stats['rate_limit']} req/min")

    print(f"\n  Reliability:")
    print(f"    Max retries: {stats['max_retries']}")
    print(f"    Retry count: {stats['retry_count']}")
    print(f"    Failed requests: {stats['failed_requests']}")

    if stats['total_searches'] > 0:
        success_rate = (stats['total_searches'] - stats['failed_requests']) / stats['total_searches']
        print(f"    Success rate: {success_rate:.1%}")

    return True


async def main():
    """Run all manual tests"""
    print("\n" + "="*80)
    print(" WEB SEARCH TOOL - MANUAL TEST SUITE")
    print(" Testing DuckDuckGo Provider (Real Searches)")
    print("="*80)

    tests = [
        ("Documentation Lookup", test_documentation_lookup),
        ("Error Resolution", test_error_resolution),
        ("Version Check", test_version_check),
        ("Best Practices", test_best_practices),
        ("Cache Performance", test_caching),
        ("Rate Limiting", test_rate_limiting),
        ("Retry Logic", test_retry_logic),
        ("Comprehensive Stats", test_comprehensive_stats),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*80)
    print(" TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("-"*80)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
