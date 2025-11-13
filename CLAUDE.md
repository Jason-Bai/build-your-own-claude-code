# Build Your Own Claude Code - Project Context

## 项目概述

一个功能完整、生产就绪的 AI 编码助手实现，灵感来自 Anthropic 的 Claude Code。
本项目展示了现代 AI Agent 架构，包括高级状态管理、上下文处理、多提供商 LLM 支持、MCP 集成和可扩展的插件系统。

**项目类型：** Python CLI 应用 + AI Agent 框架

## 核心特性

### 🎯 AI Agent 系统
- **增强型 Agent** (`src/agents/enhanced_agent.py`)
  - 有限状态机管理 (IDLE → THINKING → USING_TOOL → COMPLETED)
  - 动态工具注册和执行
  - 智能重试逻辑和错误处理
  - Token 数量追踪和管理

### 📥 高级输入体验 (Phase 1 - Prompt-Toolkit)
- **智能命令自动补全**
  - 自定义 CommandCompleter 类
  - "/" 前缀命令智能匹配
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
  - `async_get_input()` 与 asyncio 事件循环兼容
  - `async_get_multiline_input()` 用于复杂输入

### 📤 高级输出体验 (Phase 2 - Rich)
- **彩色样式输出**
  - Success: 绿色
  - Error: 红色加粗
  - Info: 青色
  - Warning: 黄色

- **Markdown 自动渲染**
  - 自动检测 Markdown 元素
  - 在 Panel 中渲染
  - 支持标题、列表、引用、代码块

- **代码语法高亮**
  - Monokai 主题
  - 行号和缩进指南
  - 多语言支持

- **表格和 Panel**
  - 格式化表格显示
  - 带样式的 Panel 包装
  - 可扩展的布局

### 🔧 工具系统
- **7 个内置工具**
  - Read: 文件读取
  - Write: 文件写入
  - Edit: 文件编辑
  - Bash: 命令执行
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

### 🤖 LLM 客户端抽象
- **多提供商支持**
  - Anthropic Claude (完全验证)
  - OpenAI GPT (开发中)
  - Google Gemini (开发中)

- **统一接口**
  - 相同的 API 用于所有提供商
  - 自动模型检测
  - 流式和非流式响应

### 🪝 Hook 系统
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

### 📊 实时反馈系统 (Phase 3)
- **事件总线**
  - 发布-订阅消息传递
  - 异步事件处理
  - 事件优先级

- **完整的事件流**
  - 工具调用日志
  - Token 使用追踪
  - 状态变化通知

## 目录结构

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
│   │   ├── input.py         # Prompt-Toolkit 增强输入
│   │   ├── output.py        # Rich 增强输出
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
├── config.json              # 默认配置
├── requirements.txt         # 依赖
├── setup.py                 # 包设置
└── README.md                # 用户指南
```

## 技术栈

### 核心
- **Python 3.10+**
- **asyncio**: 异步编程
- **Pydantic 2.0+**: 数据验证和类型检查

### AI/LLM
- **Anthropic Claude API** (`anthropic>=0.40.0`) - 主要，完全验证
- **OpenAI API** (`openai`) - 开发中
- **Google Generative AI** (`google-generativeai`) - 开发中

### CLI 增强
- **Rich 13.0+**: 终端输出格式化
  - Markdown 渲染
  - 代码高亮
  - 表格和 Panel
- **Prompt-Toolkit 3.0+**: 增强的 CLI 输入
  - 自动补全
  - 历史管理
  - 快捷键

### 其他
- **MCP 1.0+**: Model Context Protocol (可选)
- **python-dotenv**: 环境变量管理

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 配置 API 密钥

**方法 1 - 环境变量 (推荐)**
```bash
export ANTHROPIC_API_KEY="your-key"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"  # 可选
```

**方法 2 - .env 文件**
```bash
cp .env.example .env
# 编辑 .env 并添加 API 密钥
```

**方法 3 - config.json**
```json
{
  "model": {
    "ANTHROPIC_API_KEY": "your-key"
  }
}
```

### 运行

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

## 可用命令

在交互式会话中输入以下命令：

- `/help` - 显示所有可用命令
- `/status` - 显示系统状态 (工具、Token、待办事项)
- `/todos` - 显示当前任务列表
- `/save [id]` - 保存当前对话
- `/load <id>` - 加载已保存的对话
- `/conversations` - 列出所有已保存的对话
- `/delete <id>` - 删除对话
- `/clear` - 清空对话历史
- `/init` - 初始化项目上下文 (创建 CLAUDE.md)
- `/quiet on|off` - 切换输出级别
- `/exit` - 退出应用

## 配置

### config.json 结构

```json
{
  "model": {
    "provider": "anthropic",
    "ANTHROPIC_API_KEY": "your-key",
    "model": "claude-sonnet-4-5-20250929"
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

在 `~/.tiny-claude/settings.json` 或 `.tiny-claude/settings.json` 中定义：

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

## 项目演进

### Phase 1 ✅ - Prompt-Toolkit 输入增强
- 实现 PromptInputManager 类
- 异步兼容性修复 (async_get_input)
- 智能命令自动补全 (CommandCompleter)
- 历史记录和快捷键支持

### Phase 2 ✅ - Rich 输出增强
- Rich Console 集成
- Markdown 自动检测和渲染
- 代码语法高亮
- 彩色样式输出
- 表格和 Panel 支持

### Phase 3 ✅ - 事件驱动实时反馈
- 事件总线 (EventBus)
- 完整的事件流
- 工具执行监控
- 状态变化通知

## 文档和代码规范

### 📝 语言要求

**以下内容必须使用英文：**

1. **README.md** - 项目主入口，面向国际用户
   - 提供中文备份版本 (README_zh.md)，但主 README 必须是英文

2. **所有 docs/ 目录下的文档** - 开发者文档、架构设计、故障排除等
   - `docs/architecture_guide.md` - 英文
   - `docs/development_guide.md` - 英文
   - `docs/troubleshooting_guide.md` - 英文
   - `docs/features/` - 所有功能文档英文
   - `docs/hotfixes/` - 所有修复文档英文

3. **代码注释和文档字符串** - 所有 Python 源代码中的注释
   - Docstrings 必须英文 (Google 风格)
   - 代码行内注释必须英文
   - 函数/类/模块描述必须英文

4. **Commit 消息** - 保持一致性和可搜索性
   - 需要英文 commit messages
   - 可在 commit 消息中添加多语言翻译（可选）

### 📚 例外情况

- CLAUDE.md 本身可以是中文 (内部项目上下文)
- `.env.example` 中的注释可以是中文
- 内部 .tiny-claude/ 配置文件注释可以是中文

### ✅ 好处

- **国际化支持** - 面向全球开发者和用户
- **搜索引擎友好** - 英文文档更容易被搜索到
- **GitHub 可见性** - 英文 README 提高项目曝光度
- **代码维护** - 统一的代码注释语言减少混淆
- **开源生态** - 符合开源项目的国际标准

## 开发工作流

1. 创建功能分支
2. 实现更改（含英文类型提示和文档字符串）
3. 在 `tests/` 中添加测试
4. 运行测试并确保通过
5. 使用英文更新文档
6. 创建拉取请求（英文 commit message）

## 常见任务

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

## 故障排除

**没有配置 API 提供商**
- 确保通过环境变量、.env 文件或 config.json 设置 API 密钥
- 检查提供商包已安装 (`pip install anthropic`)

**MCP 服务器无法加载**
- 验证 MCP 包已安装: `pip install mcp`
- 检查 config.json 中的 MCP 服务器命令和参数
- 确保已安装 Node.js (用于基于 npx 的服务器)

**上下文窗口超出**
- 系统在达到 80% 窗口时自动压缩
- 使用 `/clear` 重置对话
- 在 config 中调整 `max_context_tokens`

**工具执行失败**
- 检查文件权限
- 验证工具参数与 schema 匹配
- 使用 `--verbose` 查看详细错误消息

## 许可证

MIT

## 项目状态

**生产就绪**: 核心功能完整，持续优化

**最后更新**: 2025-01-13

## 贡献指南

欢迎贡献！请：
1. Fork 项目
2. 创建特性分支
3. 提交拉取请求

---

**项目为学习 AI Agent 设计模式和构建实用开发工具的教学资源。**
