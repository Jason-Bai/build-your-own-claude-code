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

## 🛠️ 开发指南

想要为项目贡献代码？包括如何添加新工具、新 LLM 提供商、新命令等内容：

👉 **[docs/development_guide.md](./docs/development_guide.md)**

## ✨ 功能开发

项目分为三个主要的功能增强阶段。查看每个阶段的实现细节：

👉 **[docs/features/](./docs/features/)**

- **Phase 1**: Prompt-Toolkit 输入增强 ✅
- **Phase 2**: Rich 输出增强 ✅
- **Phase 3**: 事件驱动实时反馈 ✅

## 🐛 线上 Bug 修复

项目已识别和修复的线上问题记录：

👉 **[docs/hotfixes/](./docs/hotfixes/)**

## ❓ 故障排除

遇到问题？常见问题的诊断和解决方案：

👉 **[docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)**

## 📝 版权

MIT License
