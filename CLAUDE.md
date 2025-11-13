# Build Your Own Claude Code - Project Context

## Project Overview

A feature-complete, production-ready implementation of an AI coding assistant inspired by Anthropic's Claude Code. This project demonstrates modern AI agent architecture with advanced state management, context handling, multi-provider LLM support, MCP integration, and an extensible plugin system.

**Project Type:** Python CLI Application + AI Agent Framework

---

## Core Features

### 🎯 AI Agent System
- **Enhanced Agent** (`src/agents/enhanced_agent.py`)
  - Finite State Machine management (IDLE → THINKING → USING_TOOL → COMPLETED)
  - Dynamic tool registration and execution
  - Intelligent retry logic and error handling
  - Token count tracking and management

### 📥 Advanced Input Experience (Phase 1 - Prompt-Toolkit)
- **Intelligent Command Autocomplete**
  - Custom CommandCompleter class
  - "/" prefix command smart matching
  - Case-insensitive completion
  - Multi-line input support

- **History Management**
  - Persistent history to `~/.cache/tiny_claude_code/`
  - Search history (Ctrl+R)
  - Browse history (Up/Down)

- **Keyboard Shortcuts**
  - Ctrl+A/E: Beginning/End of line
  - Ctrl+K/U: Delete to end/beginning of line
  - Ctrl+W: Delete previous word
  - Alt+Enter: Multi-line editing
  - Mouse support: Select, copy, paste

- **Async Compatibility**
  - `async_get_input()` compatible with asyncio event loops
  - `async_get_multiline_input()` for complex input

### 📤 Advanced Output Experience (Phase 2 - Rich)
- **Colored Styled Output**
  - Success: Green
  - Error: Red bold
  - Info: Cyan
  - Warning: Yellow

- **Automatic Markdown Rendering**
  - Auto-detect Markdown elements
  - Render in Panel
  - Support for headings, lists, quotes, code blocks

- **Code Syntax Highlighting**
  - Monokai theme
  - Line numbers and indentation guides
  - Multi-language support

- **Tables and Panels**
  - Formatted table display
  - Styled Panel wrapping
  - Expandable layouts

### 🔧 Tool System
- **7 Built-in Tools**
  - Read: File reading
  - Write: File writing
  - Edit: File editing
  - Bash: Command execution
  - Glob: File pattern matching
  - Grep: Content search
  - Todo: Task tracking

- **Three-Tier Permission System**
  - SAFE: Read-only operations (auto-approved)
  - NORMAL: Standard operations (requires confirmation)
  - DANGEROUS: Destructive operations (explicit confirmation)

- **Intelligent Retry Mechanism**
  - Exponential backoff
  - Error recovery
  - Timeout handling

### 🤖 LLM Client Abstraction
- **Multi-Provider Support**
  - Anthropic Claude (fully verified)
  - OpenAI GPT (in development)
  - Google Gemini (in development)

- **Unified Interface**
  - Same API for all providers
  - Automatic model detection
  - Streaming and non-streaming responses

### 🪝 Hook System
- **Event-Driven Extensibility**
  - Before/after tool execution
  - Agent state changes
  - Message send/receive

- **Secure Python Code Loading**
  - AST validation
  - Restricted imports
  - Execution sandbox

- **Persistent Configuration**
  - Global: `~/.tiny-claude/settings.json`
  - Project: `.tiny-claude/settings.json`
  - Local: `.tiny-claude/settings.local.json`

### 📊 Real-Time Feedback System (Phase 3)
- **Event Bus**
  - Pub-sub messaging
  - Async event handling
  - Event priority

- **Complete Event Stream**
  - Tool invocation logging
  - Token usage tracking
  - State change notifications

---

## Directory Structure

```
build-your-own-claude-code/
├── src/
│   ├── agents/              # Agent core
│   │   ├── enhanced_agent.py
│   │   ├── state.py
│   │   ├── context_manager.py
│   │   ├── tool_manager.py
│   │   ├── permission_manager.py
│   │   └── feedback.py
│   ├── clients/             # LLM clients
│   │   ├── base.py
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   ├── google.py
│   │   └── factory.py
│   ├── tools/               # Tool system
│   │   ├── base.py
│   │   ├── file_ops.py
│   │   ├── bash.py
│   │   ├── search.py
│   │   ├── todo.py
│   │   └── executor.py
│   ├── commands/            # CLI commands
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── conversation_commands.py
│   │   ├── workspace_commands.py
│   │   └── settings_commands.py
│   ├── utils/               # Utilities
│   │   ├── input.py         # Prompt-Toolkit enhanced input
│   │   ├── output.py        # Rich enhanced output
│   │   └── formatting.py
│   ├── hooks/               # Hook system
│   │   ├── manager.py
│   │   ├── types.py
│   │   ├── config_loader.py
│   │   ├── validator.py
│   │   └── secure_loader.py
│   ├── events/              # Event system
│   │   ├── bus.py
│   │   ├── types.py
│   │   └── __init__.py
│   ├── mcps/                # MCP integration
│   │   ├── client.py
│   │   └── config.py
│   ├── prompts/             # System prompts
│   │   └── system.py
│   ├── persistence.py       # Conversation persistence
│   └── main.py              # Application entry point
├── tests/                   # Test suite
├── docs/                    # Documentation
├── config.json              # Default configuration
├── requirements.txt         # Dependencies
├── setup.py                 # Package setup
└── README.md                # User guide
```

---

## Technology Stack

### Core
- **Python 3.10+**
- **asyncio**: Asynchronous programming
- **Pydantic 2.0+**: Data validation and type checking

### AI/LLM
- **Anthropic Claude API** (`anthropic>=0.40.0`) - Primary, fully verified
- **OpenAI API** (`openai`) - In development
- **Google Generative AI** (`google-generativeai`) - In development

### CLI Enhancement
- **Rich 13.0+**: Terminal output formatting
  - Markdown rendering
  - Code highlighting
  - Tables and Panels
- **Prompt-Toolkit 3.0+**: Enhanced CLI input
  - Autocomplete
  - History management
  - Keyboard shortcuts

### Other
- **MCP 1.0+**: Model Context Protocol (optional)
- **python-dotenv**: Environment variable management

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configure API Key

**Method 1 - Environment Variables (Recommended)**
```bash
export ANTHROPIC_API_KEY="your-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # Optional
```

**Method 2 - .env File**
```bash
cp .env.example .env
# Edit .env and add your API key
```

**Method 3 - config.json**
```json
{
  "model": {
    "ANTHROPIC_API_KEY": "your-key"
  }
}
```

### Run the Application

```bash
# Basic run
python -m src.main

# Verbose mode (show tool details and thinking process)
python -m src.main --verbose

# Quiet mode (show only errors and agent responses)
python -m src.main --quiet

# Custom configuration file
python -m src.main --config my-config.json

# Skip permission checks (dangerous!)
python -m src.main --dangerously-skip-permissions
```

---

## Available Commands

Available commands in the interactive session:

- `/help` - Show all available commands
- `/status` - Display system status (tools, tokens, todos)
- `/todos` - Show current task list
- `/save [id]` - Save current conversation
- `/load <id>` - Load a saved conversation
- `/conversations` - List all saved conversations
- `/delete <id>` - Delete a conversation
- `/clear` - Clear conversation history
- `/init` - Initialize project context (create CLAUDE.md)
- `/quiet on|off` - Toggle output level
- `/exit` - Exit the application

---

## Configuration

### config.json Structure

```json
{
  "model": {
    "provider": "anthropic",
    "ANTHROPIC_API_KEY": "your-key",
    "model": "claude-sonnet-4-5-20250929"
  },
  "ui": {
    "output_level": "normal"
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

For detailed configuration options, see [config.json](./config.json) in the project root.

### Hook Configuration

Define hooks in `~/.tiny-claude/settings.json` or `.tiny-claude/settings.json`:

```json
{
  "hooks": [
    {
      "event": "on_tool_execute",
      "type": "command",
      "command": "echo 'Tool executed: {tool_name}'",
      "priority": 10
    }
  ]
}
```

For comprehensive hook system details and examples, refer to the [Hook System Development](./docs/development_guide.md#hook-system-development) section in the development guide.

---

## Project Evolution

### Phase 1 ✅ - Prompt-Toolkit Input Enhancement
Implemented advanced CLI input with autocomplete, history, and keyboard shortcuts for improved user experience.

**Key Features:**
- Smart command autocomplete with "/" prefix support
- Persistent history management (Ctrl+R search)
- Comprehensive keyboard shortcut support
- Async-compatible input handling

**Details:** See [Prompt-Toolkit Input Enhancement](./docs/features/v0.0.1/p1-input-enhancement.md)

### Phase 2 ✅ - Rich Output Enhancement
Added beautiful terminal output with Markdown rendering, syntax highlighting, and styled formatting.

**Key Features:**
- Automatic Markdown detection and rendering
- Code block syntax highlighting with Monokai theme
- Professional table and panel formatting
- Colored output for different message types

**Details:** See [Rich Output Enhancement](./docs/features/v0.0.1/p2-output-enhancement.md)

### Phase 3 ✅ - Event-Driven Real-Time Feedback
Implemented event bus system for pub-sub messaging and real-time event tracking.

**Key Features:**
- EventBus implementation with 17 event types
- Tool execution event tracking
- LLM call event notifications
- State update event stream

**Details:** See [Event-Driven Real-Time Feedback](./docs/features/v0.0.1/p3-event-driven-feedback.md)

---

## Documentation and Code Standards

### 📝 Language Requirements

**All of the following must be in English:**

1. **README.md** - Project main entry point for international users
   - Chinese backup version (README_zh.md) provided
   - Main README must be in English

2. **All docs/ directory content** - Developer documentation, architecture design, troubleshooting guides
   - `docs/architecture_guide.md` - English
   - `docs/development_guide.md` - English
   - `docs/troubleshooting_guide.md` - English
   - `docs/features/` - All feature documentation in English
   - `docs/hotfixes/` - All fix documentation in English

3. **Code comments and docstrings** - All Python source code comments
   - Docstrings must be in English (Google style)
   - Inline code comments must be in English
   - Function/class/module descriptions must be in English

4. **Commit messages** - For consistency and searchability
   - Commit messages must be in English
   - Optional: Add multi-language translations in commit messages

### 📚 Exceptions

- CLAUDE.md itself can be in Chinese (internal project context)
- Comments in `.env.example` can be in Chinese
- Internal `.tiny-claude/` configuration file comments can be in Chinese

### ✅ Benefits

- **Internationalization Support** - Reach global developers and users
- **Search Engine Friendly** - English documentation is more easily indexed
- **GitHub Visibility** - English README improves project exposure
- **Code Maintenance** - Unified code comment language reduces confusion
- **Open Source Ecosystem** - Aligns with international open source standards

---

## Development Workflow

1. Create a feature branch
2. Implement changes with English type hints and docstrings
3. Add tests in `tests/`
4. Run tests and ensure they pass
5. Update documentation in English
6. Create pull request with English commit messages

For detailed development guidelines, refer to [Development Guide](./docs/development_guide.md).

---

## Common Tasks

### Adding a New Tool

```python
from src.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    async def execute(self, **params) -> ToolResult:
        return ToolResult(success=True, output="result")
```

### Adding a New LLM Provider

```python
from src.clients.base import BaseClient

class MyClient(BaseClient):
    async def create_message(self, ...):
        # Implementation
        pass
```

### Adding a New Command

```python
from src.commands.base import Command

class MyCommand(Command):
    @property
    def name(self) -> str:
        return "mycommand"

    async def execute(self, args: str, context) -> str:
        return "result"
```

For comprehensive extension guides, see [Extending the Project](./docs/development_guide.md#extending-the-project) in the development guide.

---

## Troubleshooting

For detailed troubleshooting information, refer to the [Troubleshooting Guide](./docs/troubleshooting_guide.md).

**Quick Solutions:**

- **No API provider configured** - Ensure API key is set via environment variable, .env file, or config.json
- **MCP servers not loading** - Verify MCP package: `pip install mcp`
- **Context window exceeded** - Use `/clear` to reset conversation
- **Tool execution fails** - Check file permissions and verify tool parameters

---

## Architecture

For detailed information about the system architecture, design patterns, data flow, and agent state machine, see [Architecture Guide](./docs/architecture_guide.md).

**Key Topics:**
- Layered architecture design
- Agent state machine implementation
- Context window management
- Tool execution and retry logic
- Permission system design
- Event system architecture

---

## License

MIT

---

## Project Status

**Production Ready**: Core functionality is complete and continuously optimized.

**Last Updated**: 2025-01-13

---

## Contributing Guidelines

Contributions are welcome! Please:
1. Fork the project
2. Create a feature branch
3. Submit a pull request with English commit messages

For detailed contribution guidelines, see [Development Guide](./docs/development_guide.md#contribution-process).

---

**This project serves as a learning resource for understanding AI Agent design patterns and building practical development tools.**
