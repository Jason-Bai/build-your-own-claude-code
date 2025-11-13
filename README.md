# Build Your Own Claude Code - Enhanced Edition

一个功能完整、架构先进的 Claude Code 实现，展示现代 AI 编码助手的核心能力和最佳实践。
结合了 Prompt-Toolkit 高级输入和 Rich 漂亮输出，提供专业级的终端体验。

## ✨ 核心特性

### 📥 高级输入体验 (Phase 1 - Prompt-Toolkit)

- **智能命令自动补全**
  - 自定义 CommandCompleter - "/" 前缀命令智能匹配
  - 大小写不敏感补全
  - 支持多行输入中的命令补全

- **历史记录管理**
  - 持久化历史到 `~/.cache/tiny_claude_code/`
  - 搜索历史 (Ctrl+R)
  - 浏览历史 (Up/Down)

- **键盘快捷键**
  - Ctrl+A/E: 行首/行尾
  - Ctrl+K/U: 删除到行尾/行首
  - Ctrl+W: 删除前一个单词
  - Alt+Enter: 多行编辑
  - 鼠标支持: 选择、复制、粘贴

- **异步兼容性**
  - async_get_input() 与 asyncio 事件循环兼容
  - 完美集成主应用事件循环

### 📤 高级输出体验 (Phase 2 - Rich)

- **彩色样式输出**
  - Success: 绿色 | Error: 红色加粗 | Info: 青色 | Warning: 黄色
  - Thinking: 暗紫色 | Debug: 暗灰色

- **Markdown 自动渲染**
  - 自动检测 Markdown 元素
  - 在 Panel 中智能渲染
  - 支持标题、列表、引用、代码块

- **代码语法高亮**
  - Monokai 主题
  - 行号和缩进指南
  - 多语言支持

- **表格和 Panel**
  - 格式化表格显示
  - 带样式的 Panel 包装
  - 可扩展的布局

### 🛠️ 完整的工具系统

- **7 个内置工具**
  - Read: 文件读取
  - Write: 文件写入
  - Edit: 文件编辑
  - Bash: 命令执行（支持权限控制）
  - Glob: 文件模式匹配
  - Grep: 内容搜索
  - Todo: 任务追踪

- **三层权限系统**
  - SAFE: 只读操作 (自动批准)
  - NORMAL: 标准操作 (需确认)
  - DANGEROUS: 危险操作 (明确确认)

- **智能重试机制**
  - 指数退避
  - 错误恢复
  - 超时处理

### 🤖 先进的 Agent 架构

- **状态管理**: 完整的 Agent 运行状态追踪 (IDLE → THINKING → USING_TOOL → COMPLETED)
- **上下文管理**: 自动压缩、摘要化、Token 估算和 CLAUDE.md 自动加载
- **工具管理**: 统一的工具注册和执行接口
- **权限控制**: 三级权限系统（SAFE/NORMAL/DANGEROUS）
- **统计信息**: 详细的执行统计和性能指标

### 🔌 MCP 集成

- **动态工具加载**: 通过 MCP 协议加载外部工具
- **标准化接口**: 统一的工具调用协议
- **可选安装**: MCP 为可选依赖，不影响核心功能
- **丰富生态**: 支持 filesystem, github 等 MCP 服务器

### 📊 实时反馈系统 (Phase 3)

- **事件驱动架构**
  - 发布-订阅消息传递
  - 异步事件处理
  - 事件优先级管理

- **完整的事件流**
  - 工具调用日志
  - Token 使用追踪
  - 状态变化通知

### 💾 对话持久化

- **保存/加载**: 保存和恢复对话历史
- **自动保存**: 可选的自动保存功能
- **对话管理**: 列出、删除历史对话

### 💬 丰富的 CLI 命令系统

| 命令 | 说明 |
|------|------|
| `/help` | 显示所有命令 |
| `/status` | 系统状态（工具、tokens、todos） |
| `/todos` | 当前任务列表 |
| `/save [id]` | 保存对话 |
| `/load <id>` | 加载对话 |
| `/conversations` | 列出所有对话 |
| `/delete <id>` | 删除对话 |
| `/clear` | 清空历史 |
| `/init` | 初始化项目上下文 (创建 CLAUDE.md) |
| `/quiet on\|off` | 切换输出级别 |
| `/exit` | 退出 |

### 🔄 多模型支持

**抽象客户端**: 统一的 LLM 客户端接口

| 提供商 | 状态 | 多轮对话 | 工具调用 | 备注 |
|--------|------|----------|---------|------|
| **Anthropic Claude** | ✅ 已验证 | ✅ 支持 | ✅ 支持 | 完全功能，支持代理端点 |
| **OpenAI GPT** | ⏳ 待开始 | - | - | 集成准备中 |
| **Google Gemini** | ⏳ 待开始 | - | - | 免费版本不支持工具调用 |

## 🔗 Hook 系统

- **事件驱动的可扩展性**
  - 工具执行前/后
  - Agent 状态变化
  - 消息发送/接收

- **安全的 Python 代码加载**
  - AST 验证
  - 限制导入
  - 执行沙盒

- **持久化配置**
  - 全局: `~/.tiny-claude/settings.json`
  - 项目: `.tiny-claude/settings.json`
  - 本地: `.tiny-claude/settings.local.json`

## 📦 项目结构

```
build-your-own-claude-code/
├── src/
│   ├── agents/              # Agent 核心
│   │   ├── enhanced_agent.py
│   │   ├── state.py
│   │   ├── context_manager.py
│   │   ├── tool_manager.py
│   │   ├── permission_manager.py
│   │   └── feedback.py
│   ├── clients/             # LLM 客户端
│   │   ├── base.py
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   ├── google.py
│   │   └── factory.py
│   ├── tools/               # 工具系统
│   │   ├── base.py
│   │   ├── file_ops.py
│   │   ├── bash.py
│   │   ├── search.py
│   │   ├── todo.py
│   │   └── executor.py
│   ├── commands/            # CLI 命令
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── conversation_commands.py
│   │   ├── workspace_commands.py
│   │   └── settings_commands.py
│   ├── utils/               # 工具函数
│   │   ├── input.py         # Prompt-Toolkit 增强输入 ⭐ 新
│   │   ├── output.py        # Rich 增强输出 ⭐ 新
│   │   └── formatting.py
│   ├── hooks/               # Hook 系统
│   │   ├── manager.py
│   │   ├── types.py
│   │   ├── config_loader.py
│   │   ├── validator.py
│   │   └── secure_loader.py
│   ├── events/              # 事件系统
│   │   ├── bus.py
│   │   ├── types.py
│   │   └── __init__.py
│   ├── mcps/                # MCP 集成
│   │   ├── client.py
│   │   └── config.py
│   ├── prompts/             # 系统提示
│   │   └── system.py
│   ├── persistence.py       # 对话持久化
│   └── main.py              # 应用入口
├── tests/                   # 测试套件
├── docs/                    # 文档
├── CLAUDE.md                # 项目上下文 ⭐ 新
├── config.json              # 默认配置
├── requirements.txt         # 依赖
├── setup.py                 # 包设置
└── README.md                # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

**方法1：环境变量（推荐）**
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # 可选
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

# 详细模式（显示工具详情、思考过程）
python -m src.main --verbose

# 安静模式（仅显示错误和 Agent 响应）
python -m src.main --quiet

# 自定义配置文件
python -m src.main --config my-config.json

# 跳过权限检查 (危险!)
python -m src.main --dangerously-skip-permissions
```

## 使用示例

### 基础交互

```
👤 You: 帮我总结一下当前目录的代码结构
🤖 Assistant:
┌───────────────────────────────────────────┐
│ 当前目录结构分析...                         │
│ (Rich 格式化输出，带 Markdown 渲染)       │
└───────────────────────────────────────────┘

👤 You: /save my-conversation
✓ Conversation saved with ID: my-conversation

👤 You: /status
🤖 Assistant:
┌────────────────────────────────────────────┐
│ System Status                               │
├────────────────────────────────────────────┤
│ Model: claude-sonnet-4.5                    │
│ Tools: 7/7 available                        │
│ Tokens used: 1234/8000                      │
│ Output level: normal                        │
└────────────────────────────────────────────┘
```

### 命令自动补全

```
👤 You: /h<TAB>
# 自动补全为 /help
# 也支持 Ctrl+R 搜索历史、Up/Down 浏览历史
```

### Markdown 自动渲染

当 Agent 返回包含 Markdown 的响应时：

```
👤 You: 用 Markdown 格式解释一下 Python async/await

🤖 Assistant:
┌──────────────────────────────────────────────────┐
│ # Python async/await 解释                       │
│                                                 │
│ ## 基础概念                                     │
│                                                 │
│ - **async/await** 是 Python 异步编程的核心     │
│ - `async def` 定义协程                         │
│ - `await` 等待异步操作完成                      │
│                                                 │
│ ## 示例代码                                     │
│                                                 │
│ ```python                                      │
│ async def fetch_data():                        │
│     result = await api.get_data()              │
│     return result                              │
│ ```                                            │
└──────────────────────────────────────────────────┘
```

## 配置详解

### config.json

```json
{
  "model": {
    "provider": "anthropic",
    "ANTHROPIC_API_KEY": "your-key",
    "ANTHROPIC_MODEL": "claude-sonnet-4-5-20250929"
  },
  "ui": {
    "output_level": "normal"
  },
  "mcp_servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "enabled": true
    }
  ]
}
```

### Hook 配置

在 `~/.tiny-claude/settings.json` 中定义：

```json
{
  "hooks": [
    {
      "event": "on_tool_execute",
      "type": "command",
      "command": "echo 'Tool executed: {tool_name}'",
      "priority": 10
    }
  ]
}
```

## 故障排除

### 没有配置 API 提供商

- 确保通过环境变量、.env 文件或 config.json 设置 API 密钥
- 检查提供商包已安装 (`pip install anthropic`)

### MCP 服务器无法加载

- 验证 MCP 包已安装: `pip install mcp`
- 检查 config.json 中的 MCP 服务器命令和参数
- 确保已安装 Node.js (用于基于 npx 的服务器)

### 上下文窗口超出

- 系统在达到 80% 窗口时自动压缩
- 使用 `/clear` 重置对话
- 在 config 中调整 `max_context_tokens`

### 工具执行失败

- 检查文件权限
- 验证工具参数与 schema 匹配
- 使用 `--verbose` 查看详细错误消息

## 项目演进

### Phase 1 ✅ - Prompt-Toolkit 输入增强

- ✅ 实现 PromptInputManager 类与 CommandCompleter
- ✅ 异步兼容性修复 (async_get_input)
- ✅ 智能命令自动补全 (CommandCompleter)
- ✅ 历史记录和快捷键支持

**Commits:**
- `1a81d61` - P1: Implement Prompt-Toolkit input enhancement
- `ff3f221` - Refactor: Rename src/utils/prompt_input.py to src/utils/input.py
- `0370ab7` - Fix: Add async support to PromptInputManager
- `2c8e340` - Fix: Implement smart command autocomplete

### Phase 2 ✅ - Rich 输出增强

- ✅ Rich Console 集成
- ✅ Markdown 自动检测和渲染
- ✅ 代码语法高亮
- ✅ 彩色样式输出
- ✅ 表格和 Panel 支持

**Commit:**
- `e697509` - P2: Enhance output with Rich library

### Phase 3 ✅ - 事件驱动实时反馈

- ✅ 事件总线 (EventBus)
- ✅ 完整的事件流
- ✅ 工具执行监控
- ✅ 状态变化通知

**Commit:**
- `1a17886` - P3: Implement Event-Driven Real-Time Feedback System

## 开发工作流

1. 创建功能分支
2. 实现更改（含类型提示和文档字符串）
3. 在 `tests/` 中添加测试
4. 运行测试并确保通过
5. 更新文档
6. 创建拉取请求

### 添加新工具

```python
from src.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    async def execute(self, **params) -> ToolResult:
        return ToolResult(success=True, output="result")
```

### 添加新 LLM 提供商

```python
from src.clients.base import BaseClient

class MyClient(BaseClient):
    async def create_message(self, ...):
        # 实现
        pass
```

### 添加新命令

```python
from src.commands.base import Command

class MyCommand(Command):
    @property
    def name(self) -> str:
        return "mycommand"

    async def execute(self, args: str, context) -> str:
        return "result"
```

## 技术栈

### 核心
- Python 3.10+
- asyncio - 异步编程
- Pydantic 2.0+ - 数据验证和类型检查

### AI/LLM
- **Anthropic Claude API** (anthropic>=0.40.0) - 主要，完全验证
- **OpenAI API** (openai) - 开发中
- **Google Generative AI** (google-generativeai) - 开发中

### CLI 增强
- **Rich 13.0+** - 终端输出格式化
- **Prompt-Toolkit 3.0+** - 增强的 CLI 输入

### 其他
- MCP 1.0+ - Model Context Protocol (可选)
- python-dotenv - 环境变量管理

## 许可证

MIT

## 项目状态

**生产就绪**: 核心功能完整，持续优化

**最后更新**: 2025-01-13

## 贡献指南

欢迎贡献！请：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交拉取请求

---

**项目为学习 AI Agent 设计模式和构建实用开发工具的教学资源。**

有问题？提交 Issue 或查看 [CLAUDE.md](./CLAUDE.md) 获取详细的项目文档。
