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

**Method 3: config.json**

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

This project includes a comprehensive test suite to ensure code quality and maintainability.

### Test Statistics

- **Total Tests**: 359 passing tests ✅
- **Code Coverage**: 34% (up from 5%)
- **Test Files**: 8 unit test modules
- **Test Infrastructure**: 30+ reusable fixtures
- **Execution Time**: ~3.3 seconds

### Running Tests

```bash
# Run all tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_hook_manager.py -v

# Run with coverage report
pytest tests/unit/ --cov=src --cov-report=html

# Quick verification
pytest tests/unit/ -v --tb=short | tail -20
```

### Test Coverage by Module

**High Coverage (>80%)**
- `hooks/manager.py`: 95% - Hook registration and triggering
- `hooks/types.py`: 95% - Hook event types and context
- `tools/executor.py`: 95% - Tool execution with retry logic
- `agents/tool_manager.py`: 91% - Tool management
- `tools/file_ops.py`: 88% - File operations (Read/Write/Edit)
- `tools/base.py`: 87% - Base tool abstractions
- `tools/todo.py`: 83% - Task management

**Good Coverage (60-80%)**
- `tools/search.py`: 79% - File search (Glob/Grep)
- `clients/anthropic.py`: 76% - Anthropic Claude client
- `tools/bash.py`: 76% - Shell command execution
- `agents/permission_manager.py`: 60% - Permission control

### Test Organization

Tests are organized into focused modules:

1. **Agent System Tests** (193 tests)
   - State management and FSM transitions
   - Context management and token estimation
   - Tool registration and execution
   - Permission control system

2. **LLM Client Tests** (42 tests)
   - Client initialization and configuration
   - Message creation and streaming
   - Multi-provider support

3. **Tool System Tests** (47 tests)
   - File operations (Read, Write, Edit)
   - Shell execution (Bash)
   - Search tools (Glob, Grep)
   - Task management (Todo)

4. **Hook System Tests** (63 tests)
   - Hook event types and context
   - Hook manager and registration
   - Priority-based execution
   - Error handling and recovery

### Contributing Tests

When adding new features:

1. Write tests first (TDD approach)
2. Aim for >80% coverage for new code
3. Include edge cases and error scenarios
4. Use descriptive test names and docstrings
5. Follow existing test patterns in `tests/unit/`

For detailed testing documentation:

👉 **[TESTING_SUMMARY.md](./TESTING_SUMMARY.md)**

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
