# Build Your Own Claude Code

功能完整、架构先进的 AI 编码助手实现，展示现代 Agent 架构和最佳实践。

## 📖 快速介绍

### 核心特性

- **智能输入增强** - 命令自动补全、历史管理、快捷键支持
- **美观输出增强** - Markdown 渲染、代码高亮、彩色样式
- **完整工具系统** - 7 个内置工具 + MCP 集成支持
- **先进 Agent 架构** - 状态管理、上下文管理、权限控制
- **事件驱动反馈** - 实时事件流、Hook 系统、可扩展架构
- **多模型支持** - Anthropic Claude (已验证)、OpenAI、Google Gemini
- **对话持久化** - 保存/加载对话、自动保存支持
- **丰富 CLI 命令** - 10+ 命令系统、对话管理、工作流支持

## 🚀 快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

**方法 1：环境变量（推荐）**

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # 可选
```

**方法 2：.env 文件**

```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 API key
```

**方法 3：config.json**

```json
{
  "model": {
    "ANTHROPIC_API_KEY": "your-key"
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

本项目包含全面的测试套件，共 **1,100 个通过测试**，**68% 代码覆盖率**。

```bash
# 运行所有测试
pytest tests/unit/ -v

# 查看覆盖率报告
pytest tests/unit/ --cov=src --cov-report=html
```

### 测试覆盖

- **Agent 系统**: 97+ 个测试（状态管理、上下文、反馈、权限）
- **LLM 客户端**: 35+ 个测试（Anthropic、OpenAI、Google、工厂）
- **工具系统**: 40+ 个测试（执行器、文件操作、bash、搜索、todo）
- **Hook 系统**: 70+ 个测试（类型、管理器、构建器、验证器、配置加载）
- **命令系统**: 60+ 个测试（内置命令、持久化、工作区）
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

项目分为三个主要的功能增强阶段。查看每个阶段的实现细节：

👉 **[docs/features/](./docs/features/)**

### 近期功能增强 (2025-01-13)

- **[P1](./docs/features/v0.0.1/p1-input-enhancement.md)** - Prompt-Toolkit 输入增强 ✅
- **[P2](./docs/features/v0.0.1/p2-output-enhancement.md)** - Rich 输出增强 ✅
- **[P3](./docs/features/v0.0.1/p3-event-driven-feedback.md)** - 事件驱动实时反馈 ✅

## 🐛 线上 Bug 修复

项目已识别和修复的线上问题记录：

👉 **[docs/hotfixes/](./docs/hotfixes/)**

### 近期修复 (2025-01-13)

- **[v2025.01.13.1](./docs/hotfixes/v2025.01.13/1-fix-asyncio-loop.md)** - asyncio 事件循环冲突 ✅
- **[v2025.01.13.2](./docs/hotfixes/v2025.01.13/2-fix-tab-autocomplete.md)** - Tab 自动补全 "/" 前缀问题 ✅
- **[v2025.01.13.3](./docs/hotfixes/v2025.01.13/3-fix-application-startup.md)** - 应用启动错误 ✅
- **[v2025.01.13.4](./docs/hotfixes/v2025.01.13/4-fix-optional-imports.md)** - 可选客户端导入错误 ✅
- **[v2025.01.13.5](./docs/hotfixes/v2025.01.13/5-fix-gemini-response.md)** - Google Gemini API 响应处理 ✅

## 🚀 接下来

即将发布的计划功能：

👉 **[docs/features/v0.0.1/](./docs/features/v0.0.1/)**

- **[P4](./docs/features/v0.0.1/p4-sandbox-execution.md)** - 沙箱执行（安全隔离）📋
- **[P5](./docs/features/v0.0.1/p5-conditional-routing.md)** - 条件路由（流程控制）📋
- **[P6](./docs/features/v0.0.1/p6-checkpoint-persistence.md)** - Checkpoint 持久化（状态管理）📋
- **[P7](./docs/features/v0.0.1/p7-multi-agent-orchestration.md)** - 多 Agent 编排（协作）📋

## ❓ 故障排除

遇到问题？常见问题的诊断和解决方案：

👉 **[docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)**

## 📝 版权

MIT License
