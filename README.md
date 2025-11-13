# Build Your Own Claude Code - Enhanced Edition

一个功能完整、架构先进的 Claude Code 实现，展示现代 AI 编码助手的核心能力和最佳实践。

## ✨ 核心特性

### 🛠️ 完整的工具系统
- **文件操作**: Read, Write, Edit - 完整的文件管理能力
- **命令执行**: Bash - 执行系统命令（支持权限控制）
- **代码搜索**: Glob (文件模式), Grep (内容搜索)
- **任务管理**: TodoWrite - 多步骤任务跟踪和进度管理
- **智能重试**: 自动重试 + AI 决策优化

### 🤖 先进的 Agent 架构
- **状态管理**: 完整的 Agent 运行状态追踪
- **上下文管理**: 自动压缩、摘要化、Token 估算和 CLAUDE.md 自动加载
- **工具管理**: 统一的工具注册和执行接口
- **权限控制**: 三级权限系统（SAFE/NORMAL/DANGEROUS）
- **统计信息**: 详细的执行统计和性能指标

### 🔌 MCP 集成
- **动态工具加载**: 通过 MCP 协议加载外部工具
- **标准化接口**: 统一的工具调用协议
- **可选安装**: MCP 为可选依赖，不影响核心功能
- **丰富生态**: 支持 filesystem, github 等 MCP 服务器

### 💾 对话持久化
- **保存/加载**: 保存和恢复对话历史
- **自动保存**: 可选的自动保存功能
- **对话管理**: 列出、删除历史对话

### 💬 丰富的 CLI 命令系统
- `/help` - 显示所有命令
- `/status` - 系统状态（工具、tokens、todos）
- `/todos` - 当前任务列表
- `/save [id]` - 保存对话
- `/load <id>` - 加载对话
- `/conversations` - 列出所有对话
- `/delete <id>` - 删除对话
- `/clear` - 清空历史
- `/init` - 初始化项目上下文
- `/quiet on|off` - 切换输出级别
- `/exit` - 退出

### 🔄 多模型支持
- **抽象客户端**: 统一的 LLM 客户端接口
- **Anthropic**: Claude Sonnet 4.5 (默认)
- **OpenAI**: GPT-4o
- **Google**: Gemini 1.5 Flash
- **智能检测**: 自动检测可用模型和 API key

#### 提供商支持状态

| 提供商 | 状态 | 多轮对话 | 工具调用 | 备注 |
|--------|------|----------|---------|------|
| **Anthropic Claude** | ✅ 已验证 | ✅ 支持 | ✅ 支持 | 完全功能，支持代理端点 |
| **OpenAI GPT** | ⏳ 待开始 | - | - | 集成准备中 |
| **Google Gemini** | ⏳ 待开始 | - | - | 免费版本不支持工具调用 |

## 📦 项目结构

```
build-your-own-claude-code/
├── src/
│   ├── main.py                # CLI 入口和配置管理
│   ├── agents/                # Agent 实现
│   │   ├── enhanced_agent.py  # 增强的 Agent
│   │   ├── state.py           # 状态管理
│   │   ├── context_manager.py # 上下文管理
│   │   └── tool_manager.py    # 工具管理
│   ├── clients/               # LLM 客户端
│   │   ├── base.py            # 抽象接口
│   │   ├── anthropic.py       # Anthropic 实现
│   │   ├── openai.py          # OpenAI 实现
│   │   └── google.py          # Google 实现
│   ├── tools/                 # 工具实现
│   │   ├── base.py            # 工具基类
│   │   ├── file_ops.py        # Read/Write/Edit
│   │   ├── bash.py
│   │   ├── search.py          # Glob/Grep
│   │   └── todo.py
│   ├── commands/              # CLI 命令
│   │   ├── base.py
│   │   ├── builtin.py
│   │   ├── persistence_commands.py
│   │   └── output_commands.py
│   ├── mcps/                  # MCP 集成
│   ├── persistence.py         # 对话持久化
│   ├── prompts/               # System Prompt
│   └── utils/                 # 工具类
│       ├── output_formatter.py
│       └── ...
├── config.json                # 默认配置文件
├── .env.example               # 环境变量模板
├── requirements.txt
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

**方法1：环境变量（推荐）**
```bash
# Anthropic (优先级最高)
export ANTHROPIC_API_KEY="your-anthropic-key"

# 或 OpenAI
export OPENAI_API_KEY="your-openai-key"

# 或 Google
export GOOGLE_API_KEY="your-google-key"
```

**方法2：.env 文件**
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 API key
```

**方法3：config.json**
```json
{
  "model": {
    "ANTHROPIC_API_KEY": "your-key",
    "ANTHROPIC_MODEL": "claude-sonnet-4-5-20250929"
  }
}
```

### 3. 运行

```bash
# 基本运行
python -m src.main

# 查看帮助
python -m src.main --help

# 静默模式
python -m src.main --quiet

# 详细模式
python -m src.main --verbose

# 跳过权限检查（危险）
python -m src.main --dangerously-skip-permissions
```

## ⚙️ 高级配置

### 配置优先级
1. **环境变量** (最高优先级，用户 `export`)
2. **.env 文件** (中优先级)
3. **config.json** (默认配置)

### 权限控制
- **AUTO_APPROVE_SAFE**: 自动批准安全工具
- **ALWAYS_ASK**: 总是询问权限
- **SKIP_ALL**: 跳过所有权限检查（危险）

### 输出级别
- **NORMAL**: 标准输出
- **VERBOSE**: 显示工具详情和思考过程
- **QUIET**: 只显示错误和Agent响应

## 📖 使用示例

### 基本对话
```
You: Hello! Can you help me with Python development?
[Agent 会介绍自己并询问具体需求]
```

### 文件操作
```
You: Read the README.md file
You: Create a new Python file called calculator.py with a simple calculator class
You: Edit calculator.py to add input validation
```

### 任务管理
```
You: Help me implement a user authentication system
[Agent 会创建 todo list 并逐步完成]

You: /todos
[查看当前任务进度]
```

### 对话管理
```
You: /save auth-system
You: /conversations
You: /load auth-system
You: /delete auth-system
```

### 系统控制
```
You: /status
You: /quiet on
You: /help
```

## 🔧 MCP 集成

### 安装 MCP
```bash
pip install mcp
```

### 启用 MCP 服务器
编辑 `config.json`：
```json
{
  "mcp_servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "enabled": true
    },
    {
      "name": "github",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
      "enabled": false
    }
  ]
}
```

## 🏗️ 架构设计

### 核心架构
- **EnhancedAgent**: 整合所有管理器的核心控制器
- **状态机**: IDLE → THINKING → USING_TOOL → COMPLETED/ERROR
- **智能重试**: 自动重试 + AI 决策优化
- **上下文压缩**: 自动摘要化，避免 Token 超限
- **MCP 集成**: 动态加载外部工具

### 数据流
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
        return "my_tool"

    @property
    def description(self) -> str:
        return "My custom tool"

    @property
    def permission_level(self):
        return PermissionLevel.SAFE

    async def execute(self, **params) -> ToolResult:
        # 实现工具逻辑
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
        return "Command result"
```

### 添加新模型
```python
from src.clients.base import BaseClient

class MyModelClient(BaseClient):
    def __init__(self, api_key: str, model: str):
        # 实现模型客户端
        pass
```

## 🎯 功能特性

- ✅ **多模型支持**: Anthropic, OpenAI, Google
- ✅ **权限控制**: 三级安全系统
- ✅ **输出格式化**: 统一颜色化输出
- ✅ **上下文管理**: CLAUDE.md 自动加载
- ✅ **MCP 集成**: 外部工具支持
- ✅ **对话持久化**: 完整的会话管理
- ✅ **任务跟踪**: 多步骤任务管理
- ✅ **智能重试**: 错误恢复机制

## 🔄 后续迭代方向

- [ ] 流式输出支持
- [ ] LangGraph 集成
- [ ] Web 界面
- [ ] 更多 MCP 服务器集成
- [ ] 本地模型支持
- [ ] 插件系统

## 📝 许可证

MIT

## 🙏 致谢

本项目受 Anthropic Claude Code 启发，致力于学习和实践现代 AI 编码助手的设计理念。
