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

## 🛠️ Development Guide

Want to contribute to the project? Learn how to add new tools, new LLM providers, new commands, and more:

👉 **[docs/development_guide.md](./docs/development_guide.md)**

## ✨ Feature Development

The project is organized into three main feature enhancement phases. Check the implementation details for each phase:

👉 **[docs/features/](./docs/features/)**

- **Phase 1**: Prompt-Toolkit Input Enhancement ✅
- **Phase 2**: Rich Output Enhancement ✅
- **Phase 3**: Event-Driven Real-Time Feedback ✅

## 🐛 Production Bug Fixes

Records of identified and fixed production issues:

👉 **[docs/hotfixes/](./docs/hotfixes/)**

## ❓ Troubleshooting

Encountered problems? Find diagnostic guides and solutions for common issues:

👉 **[docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)**

## 📝 License

MIT License
