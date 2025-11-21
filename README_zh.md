# Build Your Own Claude Code

功能完整、架构先进的 AI 编码助手实现，展示现代 Agent 架构和最佳实践。

## 📖 快速介绍

### 核心特性

- **智能输入增强** - 命令自动补全、历史管理、快捷键支持
- **美观输出增强** - Markdown 渲染、代码高亮、彩色样式
- **完整工具系统** - 8 个内置工具 + MCP 集成支持
- **先进 Agent 架构** - 状态管理、上下文管理、权限控制
- **事件驱动反馈** - 实时事件流、Hook 系统、可扩展架构
- **多模型支持** - Anthropic Claude ✅、OpenAI ✅、Moonshot Kimi ✅
- **会话管理系统** - 自动会话持久化、命令历史跟踪、会话恢复
- **丰富 CLI 命令** - 15 个命令系统（含别名）、对话管理、工作流支持
- **响应式 UI 系统** - 响应式显示与交互输入之间的无缝模式切换
- **三级权限系统** - SAFE/NORMAL/DANGEROUS 三级权限，4 种访问控制模式
- **结构化行动日志** - 全面的事件追踪、异步队列处理、数据脱敏、查询分析工具

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
    "provider": "kimi", // 选择: "anthropic", "openai", "kimi"
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

**方法 2：环境变量（覆盖配置文件）**

```bash
# Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # 可选
export ANTHROPIC_API_BASE="https://api.anthropic.com/v1"  # 可选

# OpenAI
export OPENAI_API_KEY="your-openai-key"
export OPENAI_MODEL="gpt-4o"  # 可选
export OPENAI_API_BASE="https://api.openai.com/v1"  # 可选

# Moonshot Kimi（使用专用 provider）
export KIMI_API_KEY="your-kimi-key"
export KIMI_MODEL="kimi-k2-thinking"  # 可选
export KIMI_API_BASE="https://api.moonshot.cn/v1"  # 可选

# 选择使用哪个提供商
export MODEL_PROVIDER="kimi"  # 或 "anthropic", "openai"
```

**方法 3：.env 文件（本地项目配置）**

```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 API key
```

**配置优先级：** 环境变量 > .env 文件 > settings.json

### 3. 运行应用

```bash
python -m src.main
```

## 🏗️ 架构设计

本项目采用分层架构设计，将复杂的 AI Agent 系统分解为多个可管理的模块。

### 核心架构组件

- **Agent 状态机 (FSM)**：IDLE → THINKING → USING_TOOL → WAITING_FOR_RESULT → COMPLETED/ERROR
- **响应式 UI 系统**：在 REACTIVE（实时显示）和 INTERACTIVE（同步输入）模式之间动态切换
- **UI 协调器**：在权限请求期间管理模式转换
- **权限系统**：三级访问控制（SAFE/NORMAL/DANGEROUS），4 种模式（ALWAYS_ASK, AUTO_APPROVE_SAFE, AUTO_APPROVE_ALL, SKIP_ALL）
- **事件驱动架构**：19 种事件类型，基于 EventBus 的发布-订阅模式
- **Hook 系统**：19 种 hook 事件类型，基于优先级的执行
- **会话管理**：自动持久化、命令历史跟踪、会话恢复
- **Checkpoint 与恢复**：步骤级 checkpoint、上下文快照、状态恢复
- **行动日志系统**：异步队列 + 后台 worker、17 种 ActionTypes、数据脱敏、JSON Lines 格式按日轮转

详细的架构设计、数据流、Agent 状态机等内容，请查看：

👉 **[docs/architecture_guide.md](./docs/architecture_guide.md)**

## 🧪 测试

本项目包含全面的测试套件，共 **1,800+ 个测试**，**70%+ 代码覆盖率**。

### 测试组织结构

测试按类型组织，遵循 pytest 最佳实践：

```
tests/
├── unit/          # 单元测试（快速、使用 mock、无外部依赖）
├── integration/   # 集成测试（真实外部服务、需要网络）
└── e2e/          # 端到端测试（完整工作流）
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 仅运行单元测试（快速）
pytest tests/unit/

# 运行集成测试（需要网络）
pytest tests/integration/
# 或: pytest -m integration

# 跳过集成测试（离线工作）
pytest -m "not integration"

# 查看覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 测试覆盖概况

- **整体覆盖率**: 66.0% (2,111 / 3,200 行)
- **测试总数**: 42 个文件中的 1,167 个测试
- **通过率**: 99.9% (1,166 个通过，1 个失败，19 个 UI 相关错误)
- **执行时间**: 约 88 秒

### 测试分布

- **单元测试**: 1,600+ 个测试位于 `tests/unit/`
  - Agent 系统: 97+ 个测试（状态管理、上下文、反馈、权限）
  - LLM 客户端: 35+ 个测试（Anthropic、OpenAI、Kimi、基础客户端、工厂）
  - 工具系统: 135+ 个测试（执行器、文件操作、bash、搜索、todo、网页搜索）
  - Hook 系统: 70+ 个测试（类型、管理器、构建器、验证器、配置加载）
  - 命令系统: 60+ 个测试（内置命令、持久化、工作区、会话）
  - 会话管理器: 53 个测试（管理器、类型、命令、性能）
  - 日志系统: 603 个测试（行动日志器、数据脱敏、维护、查询）
  - UI 系统: 响应式 UI、UI 协调器、UI 管理器的测试
- **集成测试**: 2 个测试文件位于 `tests/integration/`
  - 网页搜索: 真实 DDGS API 集成测试
  - 日志集成: 端到端日志工作流
- **端到端测试**: 计划中，位于 `tests/e2e/`

### 模块覆盖率

| 模块                                   | 覆盖率 | 状态      |
| -------------------------------------- | ------ | --------- |
| **utils, config, sessions, tools**     | 84-90% | ✅ 优秀   |
| **hooks, initialization, persistence** | 65-78% | 🟢 良好   |
| **agents, clients, commands**          | 46-66% | 🟡 中等   |
| **cli, events**                        | 15-40% | 🟠 需改进 |

### 100% 覆盖率模块（27 个文件）

`agents/feedback.py`, `agents/state.py`, `commands/builtin.py`, `commands/persistence_commands.py`, `sessions/types.py`, `tools/executor.py`, `utils/output.py`, `checkpoint/types.py` 等 19+ 个支持模块。

### 测试文档

👉 **[TESTING_QUICKSTART.md](./docs/TESTING_QUICKSTART.md)** - 快速参考和常用命令

👉 **[TEST_QUALITY_REPORT.md](./docs/TEST_QUALITY_REPORT.md)** - 全面分析和建议

## 🔧 内置工具

系统包含 8 个内置工具，支持流式输出：

| 工具          | 权限       | 描述                                      |
| ------------- | ---------- | ----------------------------------------- |
| **Read**      | SAFE       | 文件读取，支持行偏移和限制                |
| **Write**     | NORMAL     | 文件创建/写入（已存在文件建议使用 Edit）  |
| **Edit**      | NORMAL     | 文件修改（优先于 Write）                  |
| **Bash**      | DANGEROUS  | 命令执行，带超时和安全控制                |
| **Glob**      | SAFE       | 使用 glob 模式的文件模式匹配              |
| **Grep**      | SAFE       | 通过 ripgrep 进行内容搜索，支持正则表达式 |
| **TodoWrite** | SAFE       | 任务管理和进度跟踪                        |
| **WebSearch** | SAFE       | 通过 DDGS（DuckDuckGo 搜索）进行网页搜索  |

## 💻 CLI 命令

系统提供 15 个命令，并带有便捷的别名：

| 命令            | 别名            | 描述                         |
| --------------- | --------------- | ---------------------------- |
| `/help`         | `/h`, `/?`      | 显示所有可用命令             |
| `/clear`        | `/reset`        | 清除对话历史                 |
| `/exit`         | `/quit`, `/q`   | 退出程序                     |
| `/status`       | `/info`         | 显示系统状态（工具、token）  |
| `/todos`        | -               | 显示当前任务列表             |
| `/save`         | -               | 保存当前对话                 |
| `/load`         | -               | 加载已保存的对话             |
| `/list`         | -               | 列出所有已保存的对话         |
| `/delete`       | -               | 删除已保存的对话             |
| `/checkpoint`   | -               | 管理 agent 状态 checkpoint   |
| `/session`      | `/sess`, `/resume` | 管理和恢复会话            |
| `/init`         | -               | 初始化工作区上下文           |
| `/show`         | -               | 显示当前工作区上下文         |
| `/load-context` | -               | 从文件加载工作区上下文       |
| `/verbose`      | -               | 切换详细输出模式             |
| `/quiet`        | -               | 切换安静输出模式             |

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
- **[P8](./docs/P8_SESSION_MANAGER_FINAL_REPORT.md)** - 会话管理系统（4 个阶段：核心实现、系统集成、生产迁移、验证）✅
- **[P9](./docs/features/v0.0.1/p9-extensible-commands.md)** - 可扩展命令系统（通过 `.claude/commands/` 自定义斜杠命令）✅
- **[P10](./docs/features/v0.0.1/p10-web-search-tool.md)** - 网页搜索工具（DDGS 集成，支持流式输出）✅

### 计划功能

- **[P4](./docs/features/v0.0.1/p4-sandbox-execution.md)** - 沙箱执行（安全隔离）📋
- **[P5](./docs/features/v0.0.1/p5-conditional-routing.md)** - 条件路由（流程控制）📋
- **[P7](./docs/features/v0.0.1/p7-multi-agent-orchestration.md)** - 多 Agent 编排（协作）📋

## ❓ 故障排除

遇到问题？常见问题的诊断和解决方案：

👉 **[docs/troubleshooting_guide.md](./docs/troubleshooting_guide.md)**

## 📝 版权

MIT License
