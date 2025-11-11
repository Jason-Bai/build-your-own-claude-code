# Build Your Own Claude Code - MVP

一个最小但完整的 Claude Code 实现，展示 AI 编码助手的核心能力。

## ✨ 核心特性

### 🛠️ 工具系统
- **文件操作**: Read, Write, Edit - 完整的文件管理
- **命令执行**: Bash - 执行系统命令
- **代码搜索**: Glob (文件模式), Grep (内容搜索)
- **任务管理**: TodoWrite - 多步骤任务跟踪
- **智能重试**: 自动重试 2 次 + Claude 智能决策

### 🤖 增强的 Agent 架构
- **状态管理**: 完整的 Agent 运行状态追踪
- **上下文管理**: 自动压缩、摘要化、Token 估算
- **工具管理**: 统一的工具注册和执行接口
- **统计信息**: 详细的执行统计和性能指标

### 🔌 MCP 集成
- **动态工具加载**: 通过 MCP 协议加载外部工具
- **标准化接口**: 统一的工具调用协议
- **可选安装**: MCP 为可选依赖，不影响核心功能
- **丰富生态**: 支持 filesystem, github, postgres 等 MCP 服务器

### 💾 对话持久化
- **保存/加载**: 保存和恢复对话历史
- **自动保存**: 可选的自动保存功能
- **对话管理**: 列出、删除历史对话

### 💬 CLI 命令系统
- `/help` - 显示所有命令
- `/status` - 系统状态（工具、tokens、todos）
- `/todos` - 当前任务列表
- `/save [id]` - 保存对话
- `/load <id>` - 加载对话
- `/conversations` - 列出所有对话
- `/delete <id>` - 删除对话
- `/clear` - 清空历史
- `/exit` - 退出

### 🔄 多模型支持
- **抽象客户端**: 统一的 LLM 客户端接口
- **Anthropic**: Claude 3.5 Sonnet (默认)
- **可扩展**: 预留 OpenAI、本地模型接口

## 📦 项目结构

```
build-your-own-claude-code/
├── src/
│   ├── main.py                # CLI 入口
│   ├── agents/                # Agent 实现
│   │   ├── enhanced_agent.py  # 增强的 Agent
│   │   ├── state.py           # 状态管理
│   │   ├── context_manager.py # 上下文管理
│   │   └── tool_manager.py    # 工具管理
│   ├── clients/               # LLM 客户端
│   │   ├── base.py            # 抽象接口
│   │   └── anthropic.py       # Anthropic 实现
│   ├── tools/                 # 工具实现
│   │   ├── file_ops.py        # Read/Write/Edit
│   │   ├── bash.py
│   │   ├── search.py          # Glob/Grep
│   │   └── todo.py
│   ├── commands/              # CLI 命令
│   │   ├── builtin.py
│   │   └── persistence_commands.py
│   ├── mcp_integration.py     # MCP 集成
│   ├── persistence.py         # 对话持久化
│   └── prompt.py              # System Prompt
├── config.json                # 配置文件
├── requirements.txt
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，添加你的 ANTHROPIC_API_KEY
```

### 3. 运行

```bash
python -m src.main
```

## ⚙️ 配置文件

`config.json` 示例：

```json
{
  "model": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-5-20250929"
  },
  "max_turns": 20,
  "auto_save": false,
  "mcp_servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "enabled": false
    }
  ]
}
```

## 📖 使用示例

### 文件操作

```
You: Read the README.md file
You: Create a new Python file called hello.py
You: Edit hello.py to add error handling
```

### 任务管理

```
You: Help me refactor the agent.py file
[Agent 会创建 todo list 并逐步完成]

You: /todos
[查看当前任务进度]
```

### 对话管理

```
You: /save my-session
You: /conversations
You: /load my-session
```

## 🔧 MCP 集成

### 安装 MCP

```bash
pip install mcp
```

### 启用 MCP 服务器

编辑 `config.json`，设置 `enabled: true`

## 🏗️ 架构设计

本项目采用分层架构设计，包含完整的状态管理、上下文管理和工具管理系统。

### 核心架构

- **Enhanced Agent**: 整合 StateManager、ContextManager、ToolManager 的核心控制器
- **状态机**: IDLE → THINKING → USING_TOOL → COMPLETED/ERROR
- **智能重试**: 自动重试 2 次 + Claude 决策
- **上下文压缩**: 自动摘要化，避免 Token 超限
- **MCP 集成**: 动态加载外部工具

详细架构设计请参考：[架构设计文档](docs/architecture.md)

### 快速了解

```
用户输入 → CLI → EnhancedAgent → LLM → 工具执行 → 结果返回 → 继续对话
              ↓
        [StateManager, ContextManager, ToolManager]
```

## 🔨 扩展开发

### 添加新工具

```python
from src.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "MyTool"

    async def execute(self, **params) -> ToolResult:
        return ToolResult(success=True, output="Result")
```

### 添加新命令

```python
from src.commands.base import Command

class MyCommand(Command):
    @property
    def name(self) -> str:
        return "mycommand"

    async def execute(self, args: str, context) -> str:
        return "Result"
```

## 🎯 后续迭代方向

- [ ] 流式输出支持
- [ ] LangGraph 集成
- [ ] 简单 Agent（任务分解）
- [ ] Web 界面
- [ ] 更多 MCP 服务器集成

## 📝 许可证

MIT

## 🙏 致谢

本项目受 Anthropic Claude Code 启发。
