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

### Benefits

- Internationalization support for global developers
- Better GitHub visibility and SEO
- Unified codebase maintenance
- Open source ecosystem alignment

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
