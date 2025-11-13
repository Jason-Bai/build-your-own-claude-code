# 开发指南

本文档包含为 Build Your Own Claude Code 项目贡献代码的所有信息。

## 目录

- [开发工作流](#开发工作流)
- [代码风格规范](#代码风格规范)
- [扩展项目](#扩展项目)
- [测试](#测试)
- [贡献流程](#贡献流程)

---

## 开发工作流

### 1. 创建功能分支

```bash
# 创建新分支进行功能开发
git checkout -b feature/your-feature-name

# 或者修复 bug
git checkout -b bugfix/your-bugfix-name
```

### 2. 开发和测试

```bash
# 在虚拟环境中安装开发依赖
pip install -r requirements.txt
pip install -e .

# 运行应用
python -m src.main

# 运行测试
pytest tests/
```

### 3. 代码审查和提交

- 确保代码有完整的类型提示和文档字符串
- 添加相应的测试
- 更新相关文档
- 创建 Pull Request

---

## 代码风格规范

### 文件组织

- **一个类一个文件** - 主要组件（管理器、客户端）单独成文件
- **Manager 后缀** - 管理类使用 Manager 后缀（StateManager, ToolManager）
- **Base 前缀** - 抽象类使用 Base 前缀（BaseClient, BaseTool）
- **私有方法** - 使用下划线前缀（`_internal_method`）
- **常量** - 使用全大写（`UPPER_CASE`）

### 类型提示

所有函数都应该有完整的类型提示：

```python
from typing import Optional, List, Dict

async def process_message(
    message: str,
    options: Optional[Dict[str, str]] = None
) -> bool:
    """处理消息。

    Args:
        message: 输入消息
        options: 可选的处理选项

    Returns:
        是否处理成功
    """
    pass
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def calculate_tokens(text: str, model: str = "claude-3-sonnet") -> int:
    """计算文本的 token 数量。

    使用指定模型的 tokenizer 来计算 token 数量。
    支持多种 Claude 模型。

    Args:
        text: 输入文本
        model: 使用的模型名称，默认为 claude-3-sonnet

    Returns:
        计算出的 token 数量

    Raises:
        ValueError: 如果模型不支持
        RuntimeError: 如果 tokenizer 初始化失败

    Example:
        >>> tokens = calculate_tokens("Hello world")
        >>> print(tokens)
        3
    """
    pass
```

### 错误处理

使用有意义的错误消息：

```python
try:
    result = await client.create_message(messages)
except ValueError as e:
    logger.error(f"Invalid message format: {e}")
    raise
except RuntimeError as e:
    logger.error(f"API call failed: {e}")
    raise
```

---

## 扩展项目

### 添加新工具

1. **创建新工具类**：

```python
# src/tools/my_tool.py
from src.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    """自定义工具的说明。

    这个工具做什么，为什么需要它。
    """

    @property
    def name(self) -> str:
        """工具名称"""
        return "my_tool"

    @property
    def description(self) -> str:
        """工具描述"""
        return "Brief description of what this tool does"

    @property
    def schema(self) -> dict:
        """工具的参数 schema"""
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter 1"
                }
            },
            "required": ["param1"]
        }

    async def execute(self, **params) -> ToolResult:
        """执行工具。

        Args:
            **params: 根据 schema 定义的参数

        Returns:
            ToolResult 包含执行结果
        """
        try:
            # 实现工具逻辑
            result = await self._do_something(params)
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _do_something(self, params: dict) -> str:
        """具体实现"""
        pass
```

2. **注册工具**：

在 `src/tools/` 中的工具管理器中注册新工具。

### 添加新 LLM 提供商

1. **创建客户端类**：

```python
# src/clients/my_provider.py
from src.clients.base import BaseClient, Message

class MyProviderClient(BaseClient):
    """MyProvider LLM 客户端实现。"""

    def __init__(self, api_key: str, model: str = "default-model"):
        """初始化客户端。"""
        self.api_key = api_key
        self.model = model

    async def create_message(
        self,
        messages: List[Message],
        tools: Optional[List[dict]] = None,
        **kwargs
    ) -> str:
        """创建消息并获取响应。

        Args:
            messages: 消息历史
            tools: 可用的工具定义
            **kwargs: 其他参数

        Returns:
            模型的响应文本
        """
        # 实现 API 调用
        pass
```

2. **在工厂中注册**：

在 `src/clients/factory.py` 中注册新的客户端。

### 添加新命令

1. **创建命令类**：

```python
# src/commands/my_command.py
from src.commands.base import Command

class MyCommand(Command):
    """自定义命令的说明。"""

    @property
    def name(self) -> str:
        return "mycommand"

    @property
    def description(self) -> str:
        return "Brief description of this command"

    @property
    def help(self) -> str:
        return """Usage: /mycommand [args]

Options:
    --option1    Description
    --option2    Description
"""

    async def execute(self, args: str, context) -> str:
        """执行命令。

        Args:
            args: 命令参数
            context: 应用上下文

        Returns:
            命令输出
        """
        # 实现命令逻辑
        return "Command output"
```

2. **注册命令**：

在命令注册表中注册新命令。

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_hooks.py

# 运行特定测试函数
pytest tests/test_hooks.py::test_hook_execution

# 运行带覆盖率报告
pytest --cov=src tests/

# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html tests/
```

### 编写测试

```python
# tests/test_my_feature.py
import pytest
from src.my_module import MyClass

@pytest.fixture
def my_instance():
    """创建测试实例"""
    return MyClass()

def test_basic_functionality(my_instance):
    """测试基础功能"""
    result = my_instance.do_something()
    assert result == expected_value

@pytest.mark.asyncio
async def test_async_functionality():
    """测试异步功能"""
    result = await async_function()
    assert result is not None
```

---

## 贡献流程

### 1. Fork 项目

点击 GitHub 上的 "Fork" 按钮。

### 2. 克隆你的 Fork

```bash
git clone https://github.com/your-username/build-your-own-claude-code.git
cd build-your-own-claude-code
```

### 3. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

### 4. 实现功能

- 编写代码
- 添加类型提示和文档字符串
- 添加测试

### 5. 提交更改

```bash
git add .
git commit -m "Add: brief description of changes"
```

遵循以下提交信息格式：

- `Add:` - 新功能
- `Fix:` - 修复 Bug
- `Refactor:` - 重构代码
- `Docs:` - 文档更新
- `Test:` - 添加/修改测试

### 6. 推送到 Fork

```bash
git push origin feature/your-feature-name
```

### 7. 创建 Pull Request

在 GitHub 上创建 Pull Request，描述：

- 做了什么变更
- 为什么需要这个变更
- 如何测试变更

### 8. 等待审核

维护者会审查你的代码，可能需要做一些改进。

---

## 常见开发任务

### 运行应用的各种模式

```bash
# 基本运行
python -m src.main

# 详细模式（显示工具详情、思考过程）
python -m src.main --verbose

# 安静模式（仅显示错误和 Agent 响应）
python -m src.main --quiet

# 自定义配置文件
python -m src.main --config my-config.json

# 跳过权限检查（危险！仅用于开发）
python -m src.main --dangerously-skip-permissions
```

### 构建和打包

```bash
# 安装开发模式
pip install -e .

# 构建分发包
python setup.py sdist bdist_wheel

# 安装已构建的包
pip install dist/build-your-own-claude-code-0.1.0.tar.gz
```

### MCP 集成开发

在 `config.json` 中配置 MCP 服务器：

```json
{
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

### Hook 系统开发

在 `~/.tiny-claude/settings.json` 或项目目录的 `.tiny-claude/settings.json` 中定义 Hook：

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

---

## 故障排除

### 没有配置 API 提供商

**症状**: 运行时报错 "No API provider configured"

**解决方案**:
1. 设置环境变量: `export ANTHROPIC_API_KEY="your-key"`
2. 或在 `.env` 文件中配置
3. 或在 `config.json` 中配置
4. 确保提供商包已安装: `pip install anthropic`

### MCP 服务器无法加载

**症状**: MCP 服务器列表为空或加载失败

**解决方案**:
1. 验证 MCP 包已安装: `pip install mcp`
2. 检查 `config.json` 中 MCP 服务器的命令和参数
3. 确保 Node.js 已安装（如果使用 npx）
4. 运行 `python -m src.main --verbose` 查看详细错误

### 上下文窗口超出

**症状**: 运行时报错 "Context window exceeded"

**解决方案**:
1. 使用 `/clear` 命令清空对话历史
2. 在 `config.json` 中调整 `max_context_tokens` 配置
3. 使用 `/save` 保存当前对话，然后 `/clear` 开始新对话

### 工具执行失败

**症状**: 工具执行错误，通常来自文件操作或命令执行

**解决方案**:
1. 检查文件权限
2. 验证工具参数与 schema 匹配
3. 使用 `--verbose` 标志查看详细错误信息
4. 检查 `/status` 命令查看工具列表

### 异步相关错误

**症状**: "asyncio.run() cannot be called from a running event loop"

**解决方案**:
1. 确保使用了 `async_get_input()` 而不是同步的 `get_input()`
2. 查看 [hotfixes/v2025.01.13.1-fix-asyncio-loop.md](../hotfixes/v2025.01.13.1-fix-asyncio-loop.md)

### 命令自动补全不工作

**症状**: Tab 补全不响应或补全错误

**解决方案**:
1. 确保命令以 "/" 开头
2. 查看 [hotfixes/v2025.01.13.2-fix-tab-autocomplete.md](../hotfixes/v2025.01.13.2-fix-tab-autocomplete.md)
3. 重启应用

---

**最后更新**: 2025-01-13
**贡献者**: 欢迎所有贡献！
