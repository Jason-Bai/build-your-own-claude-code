# Build Your Own Claude Code - Project Context

## Project Overview

A production-ready AI coding assistant implementation inspired by Anthropic's Claude Code. Demonstrates modern Agent architecture with state management, context handling, multi-provider LLM support, MCP integration, and an extensible plugin system.

**Type:** Python CLI + AI Agent Framework

---

## Architecture at a Glance

### Core Components

- **Agent System** (`src/agents/`) - FSM-based state machine (IDLE → THINKING → USING_TOOL → COMPLETED)
- **LLM Clients** (`src/clients/`) - Multi-provider support (Anthropic, OpenAI, Kimi)
- **Tool System** (`src/tools/`) - 7 built-in tools + MCP integration
- **Hook System** (`src/hooks/`) - Event-driven extensibility
- **CLI Enhancement** - Prompt-Toolkit (input) + Rich (output)

### Key Featuresg

- **Intelligent Input**: Command autocomplete, history, keyboard shortcuts
- **Beautiful Output**: Markdown rendering, syntax highlighting, colored styles
- **Permission System**: Three-tier access control (SAFE/NORMAL/DANGEROUS)
- **Event Bus**: Real-time feedback and state tracking
- **Persistence**: Save/load conversations, auto-save support

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configure API Key

```bash
# For Anthropic Claude
export ANTHROPIC_API_KEY="your-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # Optional

# For OpenAI
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o"  # Optional

# For Moonshot Kimi
export KIMI_API_KEY="your-key"
export KIMI_MODEL="kimi-k2-thinking"  # Optional
```

### Run

```bash
python -m src.main                    # Basic run
python -m src.main --verbose          # Show tool details
python -m src.main --quiet            # Minimal output
```

---

## Available Commands

- `/help` - Show all commands
- `/status` - System status (tools, tokens, todos)
- `/todos` - Task list
- `/save [id]` / `/load <id>` - Conversation management
- `/clear` - Clear history
- `/quiet on|off` - Toggle output level
- `/exit` - Exit

---

## Configuration

### ~/.tiny-claude-code/settings.json

```json
{
  "model": {
    "provider": "kimi",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "providers": {
    "anthropic": {
      "api_key": "your-anthropic-key",
      "model_name": "claude-sonnet-4.5"
    },
    "openai": {
      "api_key": "your-openai-key",
      "model_name": "gpt-4o"
    },
    "kimi": {
      "api_key": "your-kimi-key",
      "model_name": "kimi-k2-thinking"
    }
  },
  "mcp_servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "enabled": true
    }
  ]
}
```

### Hooks

Define in `~/.tiny-claude/settings.json`:

```json
{
  "hooks": [
    {
      "event": "on_tool_execute",
      "type": "command",
      "command": "echo 'Tool: {tool_name}'",
      "priority": 10
    }
  ]
}
```

---

## Documentation and Code Standards

### Language Requirements

✅ **Must be in English:**

- README.md - Main entry point
- All docs/ - Developer documentation
- Code comments & docstrings - All Python code
- Commit messages - For searchability

📝 **Exceptions:**

- CLAUDE.md can remain bilingual (internal context)
- Internal config files can have Chinese comments

### Three-Document Workflow

🔄 **For every feature or hotfix, follow this workflow:**

#### Workflow Overview

**New Features (Recommended Flow - Test-First Approach):**

```
1. Design Doc (Simplified) → 2. E2E Test Scenarios (Write first, expect to fail)
   ↓                              ↓
3. Implementation Plan → 4. Implementation → 5. E2E Tests Pass ✅
   ↓                                              ↓
6. Integration/Unit Tests → 7. Review Doc (with real issues documented)
```

**Existing Features (Selective Remediation):**

```
Risk Assessment → High Risk? → Add E2E Tests → Fix Issues
                    ↓ Low Risk
                    Keep Current Tests
```

**Key Principles:**

- ✅ **Test-Driven for New Work**: Write E2E test scenarios BEFORE implementation
- ✅ **Reality Check**: E2E tests expose documentation-reality gaps early
- ✅ **Selective Coverage**: Not all features need E2E tests (cost vs benefit)
- ✅ **Mixed Strategy**: E2E (scenarios) + Integration (components) + Unit (edge cases)

#### Phase 1: Design Document

**Naming Convention**: `pX-feature-name-design-document.md`

- `p` = phase number (lowercase)
- `X` = phase number (digit)
- `feature-name` = descriptive kebab-case name
- Examples:
  - ✅ `p1-input-enhancement-design-document.md`
  - ✅ `p8-session-manager-design-document.md`
  - ✅ `p10-web-search-tool-design-document.md`
  - ❌ `P1-input.md` (uppercase P)
  - ❌ `phase1-input.md` (wrong prefix)
  - ❌ `input-enhancement.md` (missing pX prefix)

**Location**: `docs/features/vX.X.X/pX-feature-name-design-document.md`

- `v0.0.1/` - Initial release features
- `v0.1.0/` - Minor version features
- `v1.0.0/` - Major version features

**Purpose**: Define the problem, requirements, technical solution, and MVP scope

**Key Sections**:

- Problem Statement (background, pain points, goals)
- Requirements Analysis (functional, non-functional, boundaries)
- Technical Solution (architecture, modules, data structures)
- MVP Definition (must-have vs should-have vs nice-to-have)
- **User Scenarios** (concrete examples of user interactions - NEW)
- Risk Assessment (technical, resource, dependency risks)
- Acceptance Criteria

**Template**: [`templates/docs/design-document-template.md`](../templates/docs/design-document-template.md)

**When**: Before starting any implementation work

---

#### Phase 1.5: E2E Test Scenarios (NEW - Test-First Approach)

**Naming Convention**: `pX-feature-name-e2e-scenarios.md` or directly in code

**Location**:
- Documentation: `docs/features/vX.X.X/pX-feature-name-e2e-scenarios.md`
- Code: `tests/e2e/test_pX_feature_name.py`

**Purpose**: Write executable test scenarios that describe real user behavior BEFORE implementation

**Key Requirements**:

- **Write tests that WILL FAIL initially** (since feature not implemented yet)
- Describe concrete user interactions (input → expected behavior)
- Cover critical paths and edge cases from design doc
- Include environment prerequisites (permissions, config, etc.)

**Example Structure**:

```python
# tests/e2e/test_p12_esc_monitor.py

@pytest.mark.e2e
class TestGlobalESCMonitor:
    """P12: Real user scenarios for ESC cancellation"""

    def test_startup_permission_check(self):
        """Scenario: User starts CLI without accessibility permissions"""
        # Expected: Warning message displayed
        # Expected: CLI continues without ESC monitoring

    def test_esc_cancels_llm_call(self):
        """Scenario: User presses ESC during long LLM operation"""
        # Given: LLM call in progress
        # When: User presses ESC
        # Then: Operation cancelled within 1 second
        # Then: "Cancelled" message displayed

    def test_esc_during_input_ignored(self):
        """Scenario: User presses ESC while typing input"""
        # Given: User in input prompt
        # When: User presses ESC
        # Then: Input cleared (normal terminal behavior)
        # Then: Execution NOT cancelled
```

**When**:
- After Phase 1 (Design Doc) is approved
- BEFORE Phase 2 (Implementation Plan) starts
- Tests should be committed in "expected to fail" state

**Benefits**:
- ✅ Forces thinking about real-world usage early
- ✅ Exposes missing requirements (e.g., permission handling)
- ✅ Provides clear "Definition of Done" (tests pass)
- ✅ Prevents documentation-reality gaps

---

#### Phase 2: Implementation Plan

**Naming Convention**: `pX-feature-name-implement-plan.md`

- `p` = phase number (lowercase)
- `X` = phase number (digit)
- `feature-name` = descriptive kebab-case name (same as design doc)
- Examples:
  - ✅ `p1-input-enhancement-implement-plan.md`
  - ✅ `p8-session-manager-implement-plan.md`
  - ✅ `p10-web-search-tool-implement-plan.md`

**Location**: `docs/features/vX.X.X/pX-feature-name-implement-plan.md` (same folder as design doc)

**Purpose**: Detailed step-by-step implementation guide with file checklists and testing strategy

**Key Sections**:

- Implementation Steps (P0/P1/P2 priority breakdown)
- File Checklist (new files + modified files with line numbers)
- Core Logic Implementation (code examples)
- **E2E Test Execution Plan** (how to run and verify scenarios - NEW)
- Testing Strategy (unit, integration tests to supplement E2E)
- Definition of Done (functional, testing, code quality, documentation)
- Progress Tracking

**Template**: [`templates/docs/implementation-plan-template.md`](../templates/docs/implementation-plan-template.md)

**Links Back To**:
- Design document (at the top of the file)
- E2E test scenarios (reference specific test cases)

**When**: After Phase 1.5 (E2E scenarios written), before coding begins

---

#### Phase 3: Review Document

**Naming Convention**: `pX-feature-name-review-document.md`

- `p` = phase number (lowercase)
- `X` = phase number (digit)
- `feature-name` = descriptive kebab-case name (same as design doc and implement plan)
- Examples:
  - ✅ `p1-input-enhancement-review-document.md`
  - ✅ `p8-session-manager-review-document.md`
  - ✅ `p10-web-search-tool-review-document.md`

**Location**: `docs/features/vX.X.X/pX-feature-name-review-document.md` (same folder as design doc and implement plan)

**Purpose**: Post-implementation review with checklist verification, deviation analysis, and lessons learned

**Key Sections**:

- Executive Summary (metrics, final status)
- Implementation Checklist (completed/partial/incomplete features)
- Deviation Analysis (design changes, scope changes)
- **E2E Test Results** (which scenarios passed, which failed, why - NEW)
- Test Results (unit, integration, performance, security)
- **Documentation-Reality Gaps** (what assumptions were wrong - NEW)
- Problems & Solutions (critical issues, root causes, prevention)
- Lessons Learned (what worked, what didn't, technical debt)
- Quality Metrics (code quality, documentation, user impact)

**Template**: [`templates/docs/review-document-template.md`](../templates/docs/review-document-template.md)

**Links Back To**:
- Design document (at the top)
- Implementation plan (at the top)
- E2E test scenarios (final pass/fail status)

**When**: After implementation is complete AND all E2E tests pass (or failures documented)

---

#### Workflow Benefits

✅ **Prevents Documentation-Reality Gaps** (NEW)

- E2E tests written first expose missing requirements early
- Tests fail until real-world issues are addressed
- Forces consideration of environment prerequisites (permissions, config)

✅ **Clear Definition of Done**

- Feature complete = all E2E scenarios pass
- No ambiguity about "is it really working?"

✅ **Ensures Stable Implementation**

- Clear roadmap from start to finish
- All requirements documented upfront
- No surprise scope creep

✅ **Easy Context Recovery**

- Documents serve as project memory
- AI assistants can quickly understand context
- Easy handoff between team members

✅ **MVP-First Approach**

- Forces prioritization (P0/P1/P2)
- Manages context window limits
- Delivers value incrementally

✅ **Knowledge Base**

- Lessons learned captured for future reference
- Technical decisions documented with rationale
- Problems and solutions searchable

#### Test Strategy Guidelines

**When to Write E2E Tests** (Risk-Based):

- ✅ **High Priority**: User-facing features, system integrations, security-critical paths
- ✅ **Medium Priority**: Complex workflows, multi-component interactions
- ❌ **Low Priority**: Pure algorithms, simple utilities, internal helpers

**Test Pyramid Balance**:

```
        E2E (Few, Slow, High Value)
       /   \
      /     \
     /       \
    / Integration (More, Faster)
   /           \
  /             \
 / Unit (Many, Fast, Low Level)
/_______________\
```

**For Existing Features** (P1-P12):

1. **Risk Assessment**: Evaluate impact if feature breaks
2. **Selective E2E**: Add tests only for high-risk features (like P12)
3. **Maintain Current Tests**: Keep existing unit/integration tests
4. **Document Gaps**: Note in Review Doc where E2E coverage is missing

#### Example File Structure

```
docs/features/v0.0.1/
├── p12-global-esc-monitor-design-document.md       # Phase 1
├── p12-global-esc-monitor-e2e-scenarios.md         # Phase 1.5 (NEW)
├── p12-global-esc-monitor-implement-plan.md        # Phase 2
└── p12-global-esc-monitor-review-document.md       # Phase 3

tests/e2e/
└── test_p12_esc_monitor.py                         # E2E scenarios (code)
```

---

### Test Organization Standards

🧪 **Tests must follow strict directory structure:**

1. **Unit Tests**: `tests/unit/`

   - Fast tests using mocks
   - No external dependencies (network, database, filesystem)
   - Example: `tests/unit/test_agent_state.py`

2. **Integration Tests**: `tests/integration/`

   - Tests with real external services
   - May require network, database, or real APIs
   - Use `@pytest.mark.integration` marker
   - Example: `tests/integration/test_web_search_integration.py`

3. **End-to-End Tests**: `tests/e2e/`

   - Full workflow tests
   - Test complete user scenarios
   - Example: `tests/e2e/test_full_conversation.py`

4. **Prohibited Locations**:
   - ❌ `tests/test_sessions/` - Use `tests/unit/test_session_*.py` instead
   - ❌ `tests/manual/` - Convert to `tests/integration/` with pytest
   - ❌ Root `tests/` directory for test files - Always use subdirectories

### Temporary Test Files Standard

⚠️ **Temporary test files MUST be managed properly:**

1. **Purpose**:

   - For manual testing, debugging, and experimentation
   - Quick validation of features or bug reproduction
   - NOT for permanent test suites (use `tests/` directories instead)

2. **Naming Convention**:

   - Prefix with `test_` for easy identification
   - Use descriptive names indicating purpose
   - Examples:
     - ✅ `test_ui_workflow.py` - Testing UI interaction flow
     - ✅ `test_consecutive_queries.py` - Testing multiple queries
     - ✅ `test_session_restore.py` - Testing session restoration
     - ❌ `temp.py` - Too vague
     - ❌ `debug.py` - Not following convention

3. **Location**:

   - ✅ **Project root directory** (for visibility and easy cleanup)
   - ❌ Do NOT place in `tests/` directories (reserved for permanent tests)
   - ❌ Do NOT place in `src/` directories (pollutes source code)

4. **Lifecycle Management**:

   - **Create**: When you need to manually test something
   - **Use**: Run and iterate during development
   - **DELETE**: Immediately after testing is complete
   - **Convert**: If test is valuable, convert to proper unit/integration test

5. **Git Guidelines**:

   - **Default**: Temporary files SHOULD NOT be committed
   - **Exception**: If needed for collaboration, commit with clear message
   - **Cleanup**: Delete in the same or next commit
   - **Best Practice**: Add `test_*.py` to `.gitignore` if frequently created

6. **Commit Checklist** (see Git Commit Standards below):
   - Before running `/commit`, check for temporary test files
   - Delete all `test_*.py` files in root directory
   - Or explicitly document why they're being committed

**Why This Matters**:

- Prevents repository pollution with temporary files
- Avoids confusion between temporary and permanent tests
- Keeps git history clean
- Maintains clear separation of concerns

**Example Workflow**:

```bash
# Create temporary test file
$ touch test_new_feature.py
# ... write test code, run it ...

# After testing is done, DELETE it:
$ rm test_new_feature.py

# Or if it's valuable, convert to proper test:
$ mv test_new_feature.py tests/unit/test_new_feature.py
# ... adapt to pytest format ...
```

### Git Commit Standards

📝 **All commits MUST follow these rules:**

1. **Use the `/commit` Command** (Claude Code only):

   - This project has a custom commit command: `.claude/commands/commit.md`
   - Claude Code automatically loads it as `/commit` command
   - **Always use `/commit` instead of manual `git commit`**
   - The command ensures consistent format and quality checks

2. **Commit Message Format**:

   - Follow **Conventional Commits** with emoji: `{emoji} {type}: {description}`
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
   - Examples:
     - ✨ `feat: add user authentication system`
     - 🐛 `fix: resolve memory leak in rendering process`
     - 📝 `docs: update API documentation`
     - 🔒️ `fix: patch critical security vulnerability`

3. **Atomic Commits**:

   - One commit = One logical change
   - Don't mix features, fixes, and refactoring in one commit
   - If `/commit` detects multiple concerns, it will suggest splitting

4. **Pre-Commit Checks** (enforced by `/commit`):

   - Code must pass linting
   - Build must succeed
   - Documentation must be up-to-date
   - Use `--no-verify` only in exceptional cases

5. **Commit Message Guidelines**:

   - Present tense, imperative mood ("add" not "added")
   - First line < 72 characters
   - Include context in body for complex changes
   - Reference issues/PRs when applicable

6. **Temporary Test Files** (see Temporary Test Files Standard above):

   - **Check for `test_*.py` files in root directory before committing**
   - Delete temporary test files or document why they're being committed
   - If committed for collaboration, mark for cleanup in commit message

7. **Documentation Updates** (see Documentation Update Standard below):
   - **Check if README.md/README_zh.md need updates before committing**
   - AI assistant will proactively detect and offer to draft updates
   - Ensure both English and Chinese versions are synchronized
   - Pre-commit hooks will warn if documentation appears outdated

**Why This Matters**:

- Enables automatic changelog generation
- Improves git history readability
- Facilitates code review process
- Supports semantic versioning
- Maintains consistent code quality

**Example Workflow**:

```bash
# Make your changes
# Then use the command (Claude Code will handle everything):
/commit

# The command will:
# 1. Run pre-commit checks (lint, build, docs)
# 2. Stage files if needed
# 3. Analyze changes and suggest splits if needed
# 4. Generate appropriate commit message
# 5. Create the commit with proper format
```

### Documentation Update Standard

📚 **README and documentation MUST be updated for significant changes:**

1. **When to Update README**:

   - ✅ After adding a new feature (Phase 2+)
   - ✅ After architectural changes
   - ✅ After security fixes
   - ✅ When changing CLI commands or APIs
   - ✅ When modifying configuration options
   - ✅ When adding/removing dependencies
   - ❌ For minor bug fixes (unless user-facing behavior changes)

2. **README Sections to Check**:

   - **Features** - Add new features to the list with brief description
   - **Architecture** - Update design descriptions if structure changed
   - **Quick Start** - Update commands if CLI interface changed
   - **Configuration** - Update settings examples if options changed
   - **Testing** - Update test coverage and methodology
   - **Troubleshooting** - Add new common issues and solutions
   - **Documentation Index** - Update links if new docs added

3. **Multi-language Consistency**:

   - Update both `README.md` (English) and `README_zh.md` (Chinese)
   - Keep content synchronized across languages
   - Both files should have same sections and structure
   - If only updating one language temporarily, note it in commit message

4. **AI Assistant Responsibility** (for Claude Code):

   When user runs `/commit`, the AI assistant MUST:

   a. **Detect documentation impact**:

   ```python
   # Check if README update is needed
   staged_files = get_staged_files()
   if any(f.startswith('src/') for f in staged_files):
       if not any('README' in f for f in staged_files):
           # Proactively ask user about documentation
   ```

   b. **Analyze specific sections needing updates**:

   - New files in `src/tools/` → Update "Features" list
   - Changes to `src/agents/` → Check "Architecture" section
   - New tests in `tests/` → Update "Testing" section
   - Changes to config files → Update "Configuration" examples

   c. **Offer to draft updates**:

   ```
   "⚠️  I notice you modified [specific files].

   The following README sections may need updates:
     • Features - Add description of [new feature]
     • Testing - Update test count from X to Y
     • Architecture - Explain [architectural change]

   Should I draft these README updates for you? (y/n)"
   ```

   d. **Ensure bilingual updates**:

   - Draft updates for both README.md and README_zh.md
   - Maintain consistent formatting and structure
   - Preserve existing translation style

5. **User Responsibility**:

   - **Prefer `/commit` command** for AI-assisted documentation checks
   - Review AI-drafted documentation changes for accuracy
   - Explicitly ask "Does this need README update?" if unsure
   - Ensure technical accuracy of AI-generated content
   - Final approval of all documentation changes

6. **Pre-Commit Safety Net** (Git Hook):

   A pre-commit hook will check for missing documentation:

   - Detects code changes in `src/` without README updates
   - Displays warning and suggests using `/commit` command
   - Allows user to proceed or abort to update documentation
   - See `.git/hooks/pre-commit` for implementation

**Why This Matters**:

- Users discover features through README first
- Outdated documentation confuses new contributors
- Architecture section guides future development
- Configuration examples prevent setup errors
- Bilingual support serves international users

**Example Workflow**:

```bash
# Scenario: Just finished implementing Session Manager

# Step 1: Use /commit command
$ /commit

# Step 2: AI checks and prompts
Claude: "⚠️  I notice changes in src/sessions/.
README updates needed:
  • Features - Add 'Session Manager' to list
  • Testing - Update test count (31 → 53 tests)
  • Architecture - Explain session persistence

Should I draft these updates? (y/n)"

# Step 3: User confirms
You: "y"

# Step 4: AI drafts updates
Claude: "Updating README.md and README_zh.md..."
[Shows diff of proposed changes]
"Look good? (y/n)"

# Step 5: User reviews and confirms
You: "y"

# Step 6: AI commits everything together
Claude: "Creating commit with code + documentation..."
✅ Committed: feat: add Session Manager with updated docs
```

---

## Development

### Key Files

- `src/main.py` - Application entry point
- `src/agents/enhanced_agent.py` - Agent core
- `docs/architecture_guide.md` - Detailed architecture
- `docs/development_guide.md` - Contribution guidelines

### Technology Stack

- **Python 3.10+** - Language
- **LLM Providers** - Anthropic Claude ✅, OpenAI ✅, Moonshot Kimi ✅
- **Pydantic 2.0+** - Data validation
- **Rich 13.0+** - Terminal output
- **Prompt-Toolkit 3.0+** - CLI input
- **asyncio** - Asynchronous programming

### Common Tasks

**Add a Tool:**

```python
from src.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    async def execute(self, **params) -> ToolResult:
        return ToolResult(success=True, output="result")
```

**Add a LLM Provider:**

```python
from src.clients.base import BaseClient

class MyClient(BaseClient):
    async def create_message(self, messages, tools=None, **kwargs):
        # Implementation
        pass
```

---

## Quick Troubleshooting

| Issue             | Solution                                                                             |
| ----------------- | ------------------------------------------------------------------------------------ |
| No API provider   | Set API key env var or ~/.tiny-claude-code/settings.json (see config examples above) |
| MCP not loading   | Verify: `pip install mcp`, check config                                              |
| Context exceeded  | Use `/clear` to reset conversation                                                   |
| Tool fails        | Check permissions, verify parameters                                                 |
| Kimi tool calling | Ensure using latest version with provider-specific message handling                  |

For detailed issues: [docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)

---

## Documentation Index

- 📖 [README.md](./README.md) - User guide and quick overview
- 🏗️ [Architecture Guide](./docs/architecture_guide.md) - System design
- 🛠️ [Development Guide](./docs/development_guide.md) - Contribution guidelines
- ❓ [Troubleshooting Guide](./docs/troubleshooting_guide.md) - Common issues
- ✨ [Features](./docs/features/) - Phase 1-3 implementations
- 🐛 [Hotfixes](./docs/hotfixes/) - Recent production fixes

---

## Project Status

**Production Ready** - Core functionality complete, continuously optimized.

**Last Updated:** 2025-01-15

**License:** MIT

---

**This project is a learning resource for understanding AI Agent design patterns and building practical development tools.**
