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

### Benefits

- Internationalization support for global developers
- Better GitHub visibility and SEO
- Unified codebase maintenance
- Open source ecosystem alignment
- Clear test separation (fast unit tests vs slow integration tests)
- Easy to run specific test categories

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

| Issue            | Solution                                       |
| ---------------- | ---------------------------------------------- |
| No API provider  | Set API key env var or ~/.tiny-claude-code/settings.json (see config examples above) |
| MCP not loading  | Verify: `pip install mcp`, check config        |
| Context exceeded | Use `/clear` to reset conversation             |
| Tool fails       | Check permissions, verify parameters           |
| Kimi tool calling | Ensure using latest version with provider-specific message handling |

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
