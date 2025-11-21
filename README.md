# Build Your Own Claude Code

A production-ready, feature-complete AI coding assistant implementation that demonstrates modern Agent architecture and best practices. Learn to build intelligent CLI applications with advanced state management, multi-model LLM support, and extensible tool systems.

## 📖 Quick Overview

### Core Features

- **Intelligent Input Enhancement** - Command auto-completion, history management, keyboard shortcuts
- **Beautiful Output Enhancement** - Markdown rendering, syntax highlighting, colored styles
- **Complete Tool System** - 8 built-in tools + MCP integration support
- **Advanced Agent Architecture** - State management, context management, permission controls
- **Event-Driven Feedback** - Real-time event streams, Hook system, extensible architecture
- **Multi-Model Support** - Anthropic Claude ✅, OpenAI ✅, Moonshot Kimi ✅
- **Session Management** - Automatic session persistence, command history tracking, session restoration
- **Rich CLI Commands** - 15 command system with aliases, conversation management, workflow support
- **Reactive UI System** - Seamless mode switching between reactive display and interactive input
- **3-Tier Permission System** - SAFE/NORMAL/DANGEROUS with 4 access control modes

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

The system automatically creates `~/.tiny-claude-code/settings.json` on first run. Configure your API keys using any of these methods:

**Method 1: Configuration File (Recommended)**

Edit `~/.tiny-claude-code/settings.json`:

```json
{
  "model": {
    "provider": "kimi", // Choose: "anthropic", "openai", "kimi"
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "providers": {
    "anthropic": {
      "api_key": "your-anthropic-key",
      "model_name": "claude-sonnet-4-5-20250929",
      "api_base": "https://api.anthropic.com/v1"
    },
    "openai": {
      "api_key": "your-openai-key",
      "model_name": "gpt-4o",
      "api_base": "https://api.openai.com/v1"
    },
    "kimi": {
      "api_key": "your-kimi-key",
      "model_name": "kimi-k2-thinking",
      "api_base": "https://api.moonshot.cn/v1"
    }
  }
}
```

**Method 2: Environment Variables (Override config file)**

```bash
# For Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # Optional
export ANTHROPIC_API_BASE="https://api.anthropic.com/v1"  # Optional

# For OpenAI
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-4o"  # Optional
export OPENAI_API_BASE="https://api.openai.com/v1"  # Optional

# For Moonshot Kimi (dedicated provider)
export KIMI_API_KEY="your-kimi-key"
export KIMI_MODEL="kimi-k2-thinking"  # Optional
export KIMI_API_BASE="https://api.moonshot.cn/v1"  # Optional

# Select which provider to use
export MODEL_PROVIDER="kimi"  # or "anthropic", "openai"
```

**Method 3: .env File (Local project configuration)**

```bash
cp .env.example .env
# Edit .env file with your API keys
```

**Configuration Priority:** Environment Variables > .env File > settings.json

### 3. Run the Application

```bash
python -m src.main
```

## 🏗️ Architecture Design

This project uses a layered architecture design that decomposes complex AI Agent systems into manageable modules.

### Key Architecture Components

- **Agent State Machine (FSM)**: IDLE → THINKING → USING_TOOL → WAITING_FOR_RESULT → COMPLETED/ERROR
- **Reactive UI System**: Dynamic mode switching between REACTIVE (live display) and INTERACTIVE (sync input)
- **UI Coordinator**: Manages mode transitions during permission requests
- **Permission System**: 3-tier access control (SAFE/NORMAL/DANGEROUS) with 4 modes (ALWAYS_ASK, AUTO_APPROVE_SAFE, AUTO_APPROVE_ALL, SKIP_ALL)
- **Event-Driven Architecture**: 19 event types with EventBus pub-sub pattern
- **Hook System**: 19 hook event types with priority-based execution
- **Session Management**: Automatic persistence, command history tracking, session restoration
- **Checkpoint & Recovery**: Step-level checkpoints, context snapshots, state restoration

For detailed architecture design, data flow, Agent state machine and more:

👉 **[docs/architecture_guide.md](./docs/architecture_guide.md)**

## 🧪 Testing

This project includes a comprehensive test suite with **1,167 tests** (99.9% passing) and **66% code coverage**.

### Test Organization

Tests are organized by type following pytest best practices:

```
tests/
├── unit/          # Unit tests (fast, use mocks, no external dependencies)
├── integration/   # Integration tests (real external services, network)
└── e2e/          # End-to-end tests (full workflows)
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run only unit tests (fast)
pytest tests/unit/

# Run integration tests (requires network)
pytest tests/integration/
# or: pytest -m integration

# Skip integration tests (for offline work)
pytest -m "not integration"

# View coverage report
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage Summary

- **Overall Coverage**: 66.0% (2,111 / 3,200 lines)
- **Total Tests**: 1,167 tests in 42 files
- **Pass Rate**: 99.9% (1,166 passing, 1 failed, 19 UI-related errors)
- **Execution Time**: ~88 seconds

### Test Distribution

- **Unit Tests**: 1,000+ tests in `tests/unit/` (41 files)
  - Agent System: 97+ tests (state management, context, feedback, permissions)
  - LLM Clients: 35+ tests (Anthropic, OpenAI, Kimi, base client, factory)
  - Tool System: 135+ tests (executor, file ops, bash, search, todo, web search)
  - Hook System: 70+ tests (types, manager, builder, validator, config loader)
  - Commands: 60+ tests (builtin, persistence, workspace, session)
  - Session Manager: 53 tests (manager, types, commands, performance)
  - UI System: Tests for reactive UI, UI coordinator, UI manager
- **Integration Tests**: 1 test file in `tests/integration/`
  - Web Search: Real DDGS API integration tests
- **E2E Tests**: Planned in `tests/e2e/`

### Coverage by Module

| Module                                 | Coverage | Status        |
| -------------------------------------- | -------- | ------------- |
| **utils, config, sessions, tools**     | 84-90%   | ✅ Excellent  |
| **hooks, initialization, persistence** | 65-78%   | 🟢 Good       |
| **agents, clients, commands**          | 46-66%   | 🟡 Moderate   |
| **cli, events**                        | 15-40%   | 🟠 Needs Work |

### 100% Coverage Modules (27 files)

`agents/feedback.py`, `agents/state.py`, `commands/builtin.py`, `commands/persistence_commands.py`, `sessions/types.py`, `tools/executor.py`, `utils/output.py`, `checkpoint/types.py`, and 19+ supporting modules.

### Testing Documentation

👉 **[TESTING_QUICKSTART.md](./docs/TESTING_QUICKSTART.md)** - Quick reference and common commands

👉 **[TEST_QUALITY_REPORT.md](./docs/TEST_QUALITY_REPORT.md)** - Comprehensive analysis and recommendations

## 🔧 Built-in Tools

The system includes 8 built-in tools with streaming output support:

| Tool         | Permission | Description                                          |
| ------------ | ---------- | ---------------------------------------------------- |
| **Read**     | SAFE       | File reading with line offset/limit support          |
| **Write**    | NORMAL     | File creation/writing (prefer Edit for existing)     |
| **Edit**     | NORMAL     | File modification (preferred over Write)             |
| **Bash**     | DANGEROUS  | Command execution with timeout and security controls |
| **Glob**     | SAFE       | File pattern matching with glob patterns             |
| **Grep**     | SAFE       | Content search via ripgrep with regex support        |
| **TodoWrite** | SAFE      | Task management and progress tracking                |
| **WebSearch** | SAFE      | Web search via DDGS (DuckDuckGo Search)              |

## 💻 CLI Commands

The system provides 15 commands with convenient aliases:

| Command         | Aliases         | Description                             |
| --------------- | --------------- | --------------------------------------- |
| `/help`         | `/h`, `/?`      | Show all available commands             |
| `/clear`        | `/reset`        | Clear conversation history              |
| `/exit`         | `/quit`, `/q`   | Exit the program                        |
| `/status`       | `/info`         | Show system status (tools, tokens)      |
| `/todos`        | -               | Display current task list               |
| `/save`         | -               | Save current conversation               |
| `/load`         | -               | Load a saved conversation               |
| `/list`         | -               | List all saved conversations            |
| `/delete`       | -               | Delete a saved conversation             |
| `/checkpoint`   | -               | Manage agent state checkpoints          |
| `/session`      | `/sess`, `/resume` | Manage and restore sessions          |
| `/init`         | -               | Initialize workspace context            |
| `/show`         | -               | Show current workspace context          |
| `/load-context` | -               | Load workspace context from file        |
| `/verbose`      | -               | Toggle verbose output mode              |
| `/quiet`        | -               | Toggle quiet output mode                |

## 🛠️ Development Guide

Want to contribute to the project? Learn how to add new tools, new LLM providers, new commands, and more:

👉 **[docs/development_guide.md](./docs/development_guide.md)**

## ✨ Feature Development

The project is organized into major feature enhancement phases. Check the implementation details for each phase:

👉 **[docs/features/](./docs/features/)**

### Completed Features

- **[P1](./docs/features/v0.0.1/p1-input-enhancement.md)** - Prompt-Toolkit Input Enhancement ✅
- **[P2](./docs/features/v0.0.1/p2-output-enhancement.md)** - Rich Output Enhancement ✅
- **[P3](./docs/features/v0.0.1/p3-event-driven-feedback.md)** - Event-Driven Real-Time Feedback ✅
- **[P6](./docs/features/v0.0.1/p6-checkpoint-persistence.md)** - Checkpoint Persistence (State Management) ✅
- **[P8](./docs/P8_SESSION_MANAGER_FINAL_REPORT.md)** - Session Manager (4 phases: Core Implementation, System Integration, Production Migration, Verification) ✅
- **[P9](./docs/features/v0.0.1/p9-extensible-commands.md)** - Extensible Commands System (Custom slash commands via `.claude/commands/`) ✅
- **[P10](./docs/features/v0.0.1/p10-web-search-tool.md)** - Web Search Tool (DDGS integration with streaming output) ✅

### Planned Features

- **[P4](./docs/features/v0.0.1/p4-sandbox-execution.md)** - Sandbox Execution (Security Isolation) 📋
- **[P5](./docs/features/v0.0.1/p5-conditional-routing.md)** - Conditional Routing (Flow Control) 📋
- **[P7](./docs/features/v0.0.1/p7-multi-agent-orchestration.md)** - Multi-Agent Orchestration (Collaboration) 📋

## ❓ Troubleshooting

Encountered problems? Find diagnostic guides and solutions for common issues:

👉 **[docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)**

## 📝 License

MIT License
