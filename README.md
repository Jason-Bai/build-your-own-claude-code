# Build Your Own Claude Code

A production-ready, feature-complete AI coding assistant implementation that demonstrates modern Agent architecture and best practices. Learn to build intelligent CLI applications with advanced state management, multi-model LLM support, and extensible tool systems.

## 📖 Quick Overview

### Core Features

- **Intelligent Input Enhancement** - Command auto-completion, history management, keyboard shortcuts
- **Beautiful Output Enhancement** - Markdown rendering, syntax highlighting, colored styles
- **Complete Tool System** - 7 built-in tools + MCP integration support
- **Advanced Agent Architecture** - State management, context management, permission controls
- **Event-Driven Feedback** - Real-time event streams, Hook system, extensible architecture
- **Multi-Model Support** - Anthropic Claude ✅, OpenAI ✅, Moonshot Kimi ✅
- **Session Management** - Automatic session persistence, command history tracking, session restoration
- **Rich CLI Commands** - 10+ command system, conversation management, workflow support

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
    "provider": "openai", // Choose: "anthropic", "openai", "kimi"
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

# For Moonshot Kimi (using OpenAI-compatible provider)
export OPENAI_API_KEY="your-kimi-api-key"
export OPENAI_MODEL="moonshot-v1-8k"  # Optional
export OPENAI_API_BASE="https://api.moonshot.cn/v1"

# Select which provider to use
export MODEL_PROVIDER="openai"  # or "anthropic"
```

**Method 3: .env File (Local project configuration)**

```bash
cp .env.example .env
# Edit .env file with your API keys
```

**Configuration Priority:** Environment Variables > .env File > settings.json

**Using OpenAI-Compatible APIs (Moonshot Kimi Example):**

```json
{
  "model": {
    "provider": "openai"
  },
  "providers": {
    "openai": {
      "api_key": "your-kimi-api-key",
      "model_name": "moonshot-v1-8k",
      "api_base": "https://api.moonshot.cn/v1"
    }
  }
}
```

### 3. Run the Application

```bash
python -m src.main
```

## 🏗️ Architecture Design

This project uses a layered architecture design that decomposes complex AI Agent systems into manageable modules.

For detailed architecture design, data flow, Agent state machine and more:

👉 **[docs/architecture_guide.md](./docs/architecture_guide.md)**

## 🧪 Testing

This project includes a comprehensive test suite with **1,113 tests** (99.6% passing) and **66% code coverage**.

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
- **Total Tests**: 1,113 tests in 36 files
- **Pass Rate**: 99.6% (1,108 passing, 5 minor failures)
- **Execution Time**: ~10 seconds

### Test Distribution

- **Unit Tests**: 1,000+ tests in `tests/unit/`
  - Agent System: 97+ tests (state management, context, feedback, permissions)
  - LLM Clients: 35+ tests (Anthropic, OpenAI, base client, factory)
  - Tool System: 135+ tests (executor, file ops, bash, search, todo, web search)
  - Hook System: 70+ tests (types, manager, builder, validator, config loader)
  - Commands: 60+ tests (builtin, persistence, workspace, session)
  - Session Manager: 53 tests (manager, types, commands, performance)
- **Integration Tests**: 8+ tests in `tests/integration/`
  - Web Search: Real DuckDuckGo API integration tests
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

### Planned Features

- **[P4](./docs/features/v0.0.1/p4-sandbox-execution.md)** - Sandbox Execution (Security Isolation) 📋
- **[P5](./docs/features/v0.0.1/p5-conditional-routing.md)** - Conditional Routing (Flow Control) 📋
- **[P7](./docs/features/v0.0.1/p7-multi-agent-orchestration.md)** - Multi-Agent Orchestration (Collaboration) 📋

## ❓ Troubleshooting

Encountered problems? Find diagnostic guides and solutions for common issues:

👉 **[docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)**

## 📝 License

MIT License
