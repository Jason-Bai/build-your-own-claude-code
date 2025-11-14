# Build Your Own Claude Code

A production-ready, feature-complete AI coding assistant implementation that demonstrates modern Agent architecture and best practices. Learn to build intelligent CLI applications with advanced state management, multi-model LLM support, and extensible tool systems.

## 📖 Quick Overview

### Core Features

- **Intelligent Input Enhancement** - Command auto-completion, history management, keyboard shortcuts
- **Beautiful Output Enhancement** - Markdown rendering, syntax highlighting, colored styles
- **Complete Tool System** - 7 built-in tools + MCP integration support
- **Advanced Agent Architecture** - State management, context management, permission controls
- **Event-Driven Feedback** - Real-time event streams, Hook system, extensible architecture
- **Multi-Model Support** - Anthropic Claude (verified), OpenAI, Google Gemini
- **Conversation Persistence** - Save/load conversations, auto-save support
- **Rich CLI Commands** - 10+ command system, conversation management, workflow support

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

**Method 1: Environment Variables (Recommended)**

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # Optional
```

**Method 2: .env File**

```bash
cp .env.example .env
# Edit .env file and add your API key
```

**Method 3: ~/.tiny-claude-code/settings.json**

```json
{
  "model": {
    "ANTHROPIC_API_KEY": "your-key"
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

This project includes a comprehensive test suite with **1,100 passing tests** and **68% code coverage**.

```bash
# Run all tests
pytest tests/unit/ -v

# View coverage report
pytest tests/unit/ --cov=src --cov-report=html
```

### Test Coverage

- **Agent System**: 97+ tests (state management, context, feedback, permission)
- **LLM Clients**: 35+ tests (Anthropic, OpenAI, Google, factory)
- **Tool System**: 40+ tests (executor, file ops, bash, search, todo)
- **Hook System**: 70+ tests (types, manager, builder, validator, config loader)
- **Commands**: 60+ tests (builtin commands, persistence, workspace)
- **Other**: 800+ additional integration and edge case tests

### High Coverage Modules (>80%)

- **95%+**: `hooks/manager.py`, `agents/context_manager.py`, `clients/base.py`
- **85%+**: `tools/file_ops.py`, `tools/base.py`, `tools/bash.py`, `hooks/config_loader.py`
- **100% coverage**: `agents/feedback.py`, `agents/state.py`, `commands/builtin.py`, `commands/persistence_commands.py`, `persistence.py`, `utils/output.py`

For quick start guide and detailed documentation:

👉 **[docs/testing/quickstart.md](./docs/testing/quickstart.md)** - Get started in 5 minutes

👉 **[docs/testing/summary.md](./docs/testing/summary.md)** - Complete testing overview

## 🛠️ Development Guide

Want to contribute to the project? Learn how to add new tools, new LLM providers, new commands, and more:

👉 **[docs/development_guide.md](./docs/development_guide.md)**

## ✨ Feature Development

The project is organized into three main feature enhancement phases. Check the implementation details for each phase:

👉 **[docs/features/](./docs/features/)**

### Recent Features (2025-01-13)

- **[P1](./docs/features/v0.0.1/p1-input-enhancement.md)** - Prompt-Toolkit Input Enhancement ✅
- **[P2](./docs/features/v0.0.1/p2-output-enhancement.md)** - Rich Output Enhancement ✅
- **[P3](./docs/features/v0.0.1/p3-event-driven-feedback.md)** - Event-Driven Real-Time Feedback ✅

## 🐛 Production Bug Fixes

Records of identified and fixed production issues:

👉 **[docs/hotfixes/](./docs/hotfixes/)**

### Recent Fixes (2025-01-13)

- **[v2025.01.13.1](./docs/hotfixes/v2025.01.13/1-fix-asyncio-loop.md)** - asyncio Event Loop Conflict ✅
- **[v2025.01.13.2](./docs/hotfixes/v2025.01.13/2-fix-tab-autocomplete.md)** - Tab Autocomplete "/" Prefix Issue ✅
- **[v2025.01.13.3](./docs/hotfixes/v2025.01.13/3-fix-application-startup.md)** - Application Startup Errors ✅
- **[v2025.01.13.4](./docs/hotfixes/v2025.01.13/4-fix-optional-imports.md)** - Optional Client Import Errors ✅
- **[v2025.01.13.5](./docs/hotfixes/v2025.01.13/5-fix-gemini-response.md)** - Google Gemini API Response Handling ✅

## 🚀 What's Next

Planned features for upcoming releases:

👉 **[docs/features/v0.0.1/](./docs/features/v0.0.1/)**

- **[P4](./docs/features/v0.0.1/p4-sandbox-execution.md)** - Sandbox Execution (Security Isolation) 📋
- **[P5](./docs/features/v0.0.1/p5-conditional-routing.md)** - Conditional Routing (Flow Control) 📋
- **[P6](./docs/features/v0.0.1/p6-checkpoint-persistence.md)** - Checkpoint Persistence (State Management) 📋
- **[P7](./docs/features/v0.0.1/p7-multi-agent-orchestration.md)** - Multi-Agent Orchestration (Collaboration) 📋

## ❓ Troubleshooting

Encountered problems? Find diagnostic guides and solutions for common issues:

👉 **[docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)**

## 📝 License

MIT License
