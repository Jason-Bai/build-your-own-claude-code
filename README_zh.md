# Build Your Own Claude Code

功能完整、架构先进的 AI 编码助手实现，展示现代 Agent 架构和最佳实践。

## 📖 快速介绍

### 核心特性

- **智能输入增强** - 命令自动补全、历史管理、快捷键支持
- **美观输出增强** - Markdown 渲染、代码高亮、彩色样式
- **完整工具系统** - 7 个内置工具 + MCP 集成支持
- **先进 Agent 架构** - 状态管理、上下文管理、权限控制
- **事件驱动反馈** - 实时事件流、Hook 系统、可扩展架构
- **多模型支持** - Anthropic Claude ✅、OpenAI ✅、Moonshot Kimi ✅
- **会话管理系统** - 自动会话持久化、命令历史跟踪、会话恢复
- **丰富 CLI 命令** - 10+ 命令系统、对话管理、工作流支持

## 🚀 快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

系统首次运行时会自动创建 `~/.tiny-claude-code/settings.json`。使用以下任一方法配置 API Key：

**方法 1：配置文件（推荐）**

编辑 `~/.tiny-claude-code/settings.json`：

```json
{
  "model": {
    "provider": "openai",  // 选择: "anthropic", "openai", 或使用自定义提供商
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
    }
  }
}
```

**方法 2：环境变量（覆盖配置文件）**

```bash
# Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # 可选
export ANTHROPIC_API_BASE="https://api.anthropic.com/v1"  # 可选

# OpenAI（或 OpenAI 兼容 API，如 Moonshot Kimi）
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-4o"  # 可选
export OPENAI_API_BASE="https://api.openai.com/v1"  # 可选

# 选择使用哪个提供商
export MODEL_PROVIDER="openai"  # 或 "anthropic"
```

**方法 3：.env 文件（本地项目配置）**

```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 API key
```

**配置优先级：** 环境变量 > .env 文件 > settings.json

**使用 OpenAI 兼容 API（例如 Moonshot Kimi）：**

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

### 3. 运行应用

```bash
python -m src.main
```

## 🏗️ 架构设计

本项目采用分层架构设计，将复杂的 AI Agent 系统分解为多个可管理的模块。

详细的架构设计、数据流、Agent 状态机等内容，请查看：

👉 **[docs/architecture_guide.md](./docs/architecture_guide.md)**

## 🧪 测试

本项目包含全面的测试套件，共 **1,160+ 个通过测试**，**68% 代码覆盖率**。

```bash
# 运行所有测试
pytest tests/ -v

# 查看覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 测试覆盖

- **Agent 系统**: 97+ 个测试（状态管理、上下文、反馈、权限）
- **LLM 客户端**: 35+ 个测试（Anthropic、OpenAI、Kimi、工厂）
- **工具系统**: 40+ 个测试（执行器、文件操作、bash、搜索、todo）
- **Hook 系统**: 70+ 个测试（类型、管理器、构建器、验证器、配置加载）
- **命令系统**: 60+ 个测试（内置命令、持久化、工作区）
- **会话管理**: 61+ 个测试（单元测试、集成测试、性能验证）
- **其他**: 800+ 个额外的集成和边界情况测试

### 高覆盖率模块 (>80%)

- **95%+**: `hooks/manager.py`、`agents/context_manager.py`、`clients/base.py`
- **85%+**: `tools/file_ops.py`、`tools/base.py`、`tools/bash.py`、`hooks/config_loader.py`
- **100% 覆盖**: `agents/feedback.py`、`agents/state.py`、`commands/builtin.py`、`commands/persistence_commands.py`、`persistence.py`、`utils/output.py`

快速入门和详细文档：

👉 **[docs/testing_quickstart.md](./docs/testing_quickstart.md)** - 5 分钟快速上手

👉 **[docs/testing_summary.md](./docs/testing_summary.md)** - 完整测试概览

## 🛠️ 开发指南

想要为项目贡献代码？包括如何添加新工具、新 LLM 提供商、新命令等内容：

👉 **[docs/development_guide.md](./docs/development_guide.md)**

## ✨ 功能开发

项目分为多个主要的功能增强阶段。查看每个阶段的实现细节：

👉 **[docs/features/](./docs/features/)**

### 已完成功能

- **[P1](./docs/features/v0.0.1/p1-input-enhancement.md)** - Prompt-Toolkit 输入增强 ✅
- **[P2](./docs/features/v0.0.1/p2-output-enhancement.md)** - Rich 输出增强 ✅
- **[P3](./docs/features/v0.0.1/p3-event-driven-feedback.md)** - 事件驱动实时反馈 ✅
- **[P6](./docs/features/v0.0.1/p6-checkpoint-persistence.md)** - Checkpoint 持久化（状态管理）✅
- **[P8](./docs/P8_SESSION_MANAGER_FINAL_REPORT.md)** - 会话管理系统（4个阶段：核心实现、系统集成、生产迁移、验证）✅

### 计划功能

- **[P4](./docs/features/v0.0.1/p4-sandbox-execution.md)** - 沙箱执行（安全隔离）📋
- **[P5](./docs/features/v0.0.1/p5-conditional-routing.md)** - 条件路由（流程控制）📋
- **[P7](./docs/features/v0.0.1/p7-multi-agent-orchestration.md)** - 多 Agent 编排（协作）📋

## ❓ 故障排除

遇到问题？常见问题的诊断和解决方案：

👉 **[docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)**

## 📝 版权

MIT License
