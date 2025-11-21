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
- **Consistent commit history and quality** (Git Commit Standards)
- **Centralized knowledge and decision documentation** (Report Generation Standards)

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
