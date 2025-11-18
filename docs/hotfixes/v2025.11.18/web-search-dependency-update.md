# Hotfix: Web Search Dependency Update

**Date:** 2025-11-18
**Status:** In Progress

---

## 1. Issue Summary

The `web_search` tool currently uses the `duckduckgo_search` library, which has been deprecated and renamed to `ddgs`.

When the tool is used, it produces the following `RuntimeWarning`:

```
RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
```

Continuing to use a deprecated package is a security and maintenance risk.

## 2. Resolution

The fix involves migrating from the deprecated `duckduckgo_search` package to the new `ddgs` package.

**Changes:**
1.  Update the project's dependencies in `requirements.txt`.
2.  Update the import statement in `src/tools/web_search.py`.
3.  Update the associated error messages for clarity.

## 3. Implementation Steps

1.  **Uninstall `duckduckgo_search`**: `pip uninstall duckduckgo_search -y`
2.  **Install `ddgs`**: `pip install ddgs`
3.  **Update `requirements.txt`**: Replace `duckduckgo-search` with `ddgs`.
4.  **Update `src/tools/web_search.py`**: Modify the import from `duckduckgo_search` to `ddgs`.

## 4. Verification

- **Unit Tests:** All unit tests must pass after the changes.
- **Manual Test:** A manual run using the DuckDuckGo provider must execute successfully without any warnings.
