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

### Design Document Standards

📋 **Design documents must follow these rules:**

1. **Location**: All feature design documents MUST be placed in `docs/features/vX.X.X/`

   - Example: `docs/features/v0.0.1/`, `docs/features/v1.0.0/`

2. **Naming Convention**: File names MUST follow the pattern `pX-feature-name.md`

   - `p` = phase number (lowercase)
   - `X` = phase number (digit)
   - `feature-name` = descriptive kebab-case name
   - Examples:
     - ✅ `p1-input-enhancement.md`
     - ✅ `p8-session-manager.md`
     - ✅ `p10-web-search-tool.md`
     - ❌ `P1-input.md` (uppercase P)
     - ❌ `phase1-input.md` (wrong prefix)
     - ❌ `input-enhancement.md` (missing pX prefix)

3. **Version Folder**: Group related features by version milestone
   - `v0.0.1/` - Initial release features
   - `v0.1.0/` - Minor version features
   - `v1.0.0/` - Major version features

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

### Report Generation Standards

📊 **All summary reports MUST be placed in `docs/reports/`:**

1. **Report Types and Locations**:

   **Feature Reports** → `docs/reports/vX.X.X/{feature-name}-report.md`

   - Post-implementation summaries of completed features
   - Executive summary, implementation highlights, lessons learned
   - Example: `docs/reports/v0.0.1/reactive-ui-report.md`

   **Hotfix Reports** → `docs/reports/vYYYY.MM.DD/{issue-name}-report.md`

   - Root cause analysis and post-mortem of bugs/issues
   - Problem description, solution, prevention measures
   - Example: `docs/reports/v2025.11.18/eval-security-report.md`

   **Architecture Decision Records (ADRs)** → `docs/reports/adr-{NNN}-{decision-name}.md`

   - Documentation of significant architectural decisions
   - Context, decision, rationale, alternatives, consequences
   - Example: `docs/reports/adr-001-event-driven-ui.md`

2. **Report vs. Documentation**:

   | Aspect      | Reports (`docs/reports/`)      | Documentation (`docs/features/`, `docs/hotfixes/`) |
   | ----------- | ------------------------------ | -------------------------------------------------- |
   | **Timing**  | After implementation           | Before/during implementation                       |
   | **Purpose** | Summary & analysis             | Design & specification                             |
   | **Content** | What happened, lessons learned | What to build, how to build                        |
   | **Format**  | Executive summary style        | Technical spec style                               |

3. **When to Create Reports**:

   - ✅ After completing a Phase 2+ feature
   - ✅ After fixing critical security issues
   - ✅ When making significant architectural changes
   - ✅ When consolidating multiple related hotfixes
   - ❌ Don't create reports before implementation (use design docs)

4. **Report Requirements**:

   - Clear executive summary (1-2 paragraphs)
   - Implementation highlights (key decisions)
   - Test results and metrics (coverage, performance)
   - Impact assessment (user, performance, security)
   - Honest lessons learned (what worked, what didn't)
   - Links to related design docs, PRs, issues

5. **Report Templates**:
   - See `docs/reports/README.md` for detailed templates
   - Use appropriate template for each report type
   - Include all required sections
   - Keep reports concise (1-3 pages)

**Why This Matters**:

- Provides high-level context for stakeholders
- Documents "why" decisions were made
- Helps onboard new team members
- Creates searchable knowledge base
- Facilitates retrospectives and improvements

**Example**:
After implementing the reactive UI system, create:

- Design docs: `docs/hotfixes/v2025.11.18/hf3-*.md` (during implementation)
- Report: `docs/reports/v2025.11.18/reactive-ui-report.md` (after completion)

The report consolidates learnings from multiple hotfix docs into one executive summary.

### Benefits

- Internationalization support for global developers
- Better GitHub visibility and SEO
- Unified codebase maintenance
- Open source ecosystem alignment
- Clear test separation (fast unit tests vs slow integration tests)
- Easy to run specific test categories
- **Clean repository without temporary files** (Temporary Test Files Standard)
- **Consistent commit history and quality** (Git Commit Standards)
- **Centralized knowledge and decision documentation** (Report Generation Standards)
- **Up-to-date documentation with minimal friction** (Documentation Update Standard)

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
