# Hotfixes Documentation

This folder contains the project's online issue fix history and documentation.

Organized chronologically in reverse order for easy lookup and tracking of the latest fixes.

---

## 📋 Fixed Issues Overview

### 2025-01-13 (Latest)

#### [v2025.01.13.5 - Google Gemini API Response Handling](./v2025.01.13/5-fix-gemini-response.md)

- **Issue**: Google API returns invalid finish_reason causing application crash
- **Symptoms**: API edge case where response.text is inaccessible or finish_reason value is invalid
- **Impact Range**: Google Gemini client
- **Severity**: Medium (API edge case)
- **Status**: ✅ Fixed
- **Related Commit**: 4fecdea

#### [v2025.01.13.4 - Optional Client Import Error](./v2025.01.13/4-fix-optional-imports.md)

- **Issue**: Application fails to start when openai or google-generativeai package is missing
- **Symptoms**: ImportError - error occurs even when optional clients are not used
- **Impact Range**: Application initialization, client loading
- **Severity**: Medium (startup failure)
- **Status**: ✅ Fixed
- **Related Commit**: bbf4956

#### [v2025.01.13.3 - Application Startup Errors and asyncio Compatibility](./v2025.01.13/3-fix-application-startup.md)

- **Issue**: Three critical startup-time errors
  - load_dotenv() API changes
  - asyncio.run() conflicts
  - StatusCommand attribute reference error
- **Impact Range**: Application startup, Hook system, Status command
- **Severity**: High (application cannot start)
- **Status**: ✅ Fixed
- **Related Commit**: 0d3476f

#### [v2025.01.13.2 - Tab Autocomplete "/" Prefix Issue](./v2025.01.13/2-fix-tab-autocomplete.md)

- **Issue**: NestedCompleter removes "/" prefix, causing command autocomplete failure
- **Symptoms**: Typing `/h<TAB>` completes to `help` instead of `/help`
- **Impact Range**: Phase 1 command autocomplete feature
- **Severity**: Medium (feature malfunction)
- **Status**: ✅ Fixed
- **Related Commit**: 2c8e340

#### [v2025.01.13.1 - asyncio Event Loop Conflict](./v2025.01.13/1-fix-asyncio-loop.md)

- **Issue**: `asyncio.run() cannot be called from a running event loop`
- **Impact Range**: Phase 1 input enhancement feature
- **Severity**: High (fatal error)
- **Status**: ✅ Fixed
- **Related Commit**: 0370ab7

---

## 🔍 Find Fixes by Type

### Input-Related

- [v2025.01.13/2-fix-tab-autocomplete.md](./v2025.01.13/2-fix-tab-autocomplete.md) - Tab autocomplete fix

### Asyncio-Related

- [v2025.01.13/1-fix-asyncio-loop.md](./v2025.01.13/1-fix-asyncio-loop.md) - asyncio event loop fix
- [v2025.01.13/3-fix-application-startup.md](./v2025.01.13/3-fix-application-startup.md) - Startup asyncio conflict fix

### Startup-Related

- [v2025.01.13/3-fix-application-startup.md](./v2025.01.13/3-fix-application-startup.md) - Application startup error fix
- [v2025.01.13/4-fix-optional-imports.md](./v2025.01.13/4-fix-optional-imports.md) - Import error fix

### Client-Related

- [v2025.01.13/4-fix-optional-imports.md](./v2025.01.13/4-fix-optional-imports.md) - Optional client imports
- [v2025.01.13/5-fix-gemini-response.md](./v2025.01.13/5-fix-gemini-response.md) - Google Gemini API handling

---

## 🎯 Hotfix File Naming Convention

Format: `v{year}.{month}.{day}/{sequence}-fix-{issue-name}.md`

**Examples**:

- `v2025.01.13/1-fix-asyncio-loop.md` - 1st fix on January 13, 2025
- `v2025.01.13/2-fix-tab-autocomplete.md` - 2nd fix on January 13, 2025
- `v2025.01.15/1-fix-something.md` - Fix on January 15, 2025

---

## 📝 Hotfix Documentation Template

New hotfix documents should include the following content:

```markdown
# Fix: [Issue Title]

**Date**: YYYY-MM-DD
**Related Commit**: [commit hash]
**Impact Range**: [which features or components are affected]
**Severity**: [Low/Medium/High]

## Issue Description

### Symptoms

[what users observe]

### Root Cause Analysis

[what is the root cause]

## Solution

### Implementation Details

[how to fix it, including code examples]

### File Modifications

- **File**: [path]
- **Class**: [class name]
- **New Methods**: [method name]

## Testing Verification

[how to verify the fix works]

## Impact Range

[other impacts of this fix]

## Related Links

- Source Code: [file path]
- Commit: [commit hash]
- Related Documentation: [link]
```

---

## 📊 Statistics

| Month   | Fixes | Most Severe | Status      |
| ------- | ----- | ----------- | ----------- |
| 2025-01 | 5     | High        | ✅ Fixed    |
| 2025-02 | 0     | -           | To Add      |

---

## 🔗 Related Documentation

- **Changelog** → [../CHANGELOG.md](../CHANGELOG.md)
- **Troubleshooting** → [../troubleshooting_guide.md](../troubleshooting_guide.md)
- **Feature Documentation** → [../features/](../features/)
- **Development Guide** → [../development_guide.md](../development_guide.md)

---

**Last Updated**: 2025-01-13
