# Rich 集成方案 - 增强 CLI 输出

## 📋 概述

当前项目的 CLI 输出过于简化，特别是：
1. **Markdown 输出**：Agent 响应通常包含 Markdown，但当前直接打印，无法渲染
2. **代码块**：无语法高亮，难以阅读
3. **表格数据**：无专门格式化，看起来混乱
4. **信息层级**：所有输出看起来都一样，缺乏视觉层次

**目标**：集成 Rich 库，提升 CLI 的专业度和可读性，同时保持依赖最小化

---

## 🎯 优化方案

### 阶段 1：清理依赖（5分钟）

**现状**：
```
requirements.txt:
- rich>=13.0.0         ✓ 声明但未使用 → 保留（即将使用）
- prompt-toolkit>=3.0.0 ✗ 声明但未使用 → 移除
```

**改动**：
```diff
- prompt-toolkit>=3.0.0
```

**原因**：prompt-toolkit 是为了交互式输入而加的，但项目中用 input() 就够了

---

### 阶段 2：改造 OutputFormatter（20分钟）

#### 2.1 核心改进

**文件**：`src/utils/output.py`

**关键改动**：

```python
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.style import Style

class OutputFormatter:
    """使用 Rich 增强的输出格式化工具"""

    console = Console()
    level: OutputLevel = OutputLevel.NORMAL

    # ========== 基础输出 ==========

    @classmethod
    def success(cls, msg: str):
        """成功信息 - 绿色"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            cls.console.print(f"✓ {msg}", style="green")

    @classmethod
    def error(cls, msg: str):
        """错误信息 - 红色（总是显示）"""
        cls.console.print(f"❌ {msg}", style="red bold")

    @classmethod
    def info(cls, msg: str):
        """信息提示 - 蓝色"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            cls.console.print(f"ℹ️  {msg}", style="cyan")

    @classmethod
    def warning(cls, msg: str):
        """警告信息 - 黄色"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            cls.console.print(f"⚠️  {msg}", style="yellow")

    # ========== Agent 响应（核心改进） ==========

    @classmethod
    def print_assistant_response(cls, text: str):
        """打印 AI 响应 - 支持 Markdown 自动渲染"""
        # 检测是否包含 Markdown 元素
        if cls._contains_markdown(text):
            # 用 Panel 包装，显示为"Assistant"块
            md = Markdown(text)
            panel = Panel(
                md,
                title="🤖 Assistant",
                style="blue",
                expand=False
            )
            cls.console.print(panel)
        else:
            # 普通文本用 Panel 包装
            panel = Panel(
                text,
                title="🤖 Assistant",
                style="blue",
                expand=False
            )
            cls.console.print(panel)

    @classmethod
    def print_code_block(cls, code: str, language: str = "python", title: str = None):
        """打印代码块 - 带语法高亮"""
        syntax = Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=True,
            indent_guides=True,
            word_wrap=True
        )
        if title:
            panel = Panel(syntax, title=title, style="cyan")
            cls.console.print(panel)
        else:
            cls.console.print(syntax)

    @classmethod
    def print_table(cls, headers: list, rows: list, title: str = None):
        """打印表格 - 格式化数据展示"""
        table = Table(title=title, show_lines=False)

        # 添加列
        for header in headers:
            table.add_column(header, style="cyan", no_wrap=False)

        # 添加行
        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        cls.console.print(table)

    # ========== 工具相关 ==========

    @classmethod
    def tool_use(cls, tool_name: str, params: dict = None):
        """工具使用通知 - 增强显示"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            msg = f"🔧 Using {tool_name}"
            if params and cls.level.value >= OutputLevel.VERBOSE.value:
                cls.console.print(msg, style="yellow")
                # 显示参数（缩小版）
                for key, value in params.items():
                    value_str = str(value)[:50]
                    cls.console.print(f"   {key}: {value_str}", style="dim")
            else:
                cls.console.print(msg, style="yellow")

    @classmethod
    def tool_result(cls, tool_name: str, success: bool, output: str = ""):
        """工具执行结果"""
        if cls.level.value >= OutputLevel.VERBOSE.value:
            status = "✓" if success else "✗"
            style = "green" if success else "red"

            # 限制输出长度
            display_output = output[:200] + "..." if len(output) > 200 else output

            panel = Panel(
                display_output,
                title=f"{status} {tool_name} Result",
                style=style
            )
            cls.console.print(panel)

    # ========== 辅助方法 ==========

    @staticmethod
    def _contains_markdown(text: str) -> bool:
        """检测文本是否包含 Markdown 元素"""
        markdown_patterns = [
            '#',      # 标题
            '##',     # 子标题
            '`',      # 代码
            '**',     # 加粗
            '_',      # 斜体
            '-',      # 列表（需要在行首）
            '*',      # 列表（需要在行首）
            '> ',     # 引用
            '[',      # 链接
            '|',      # 表格
        ]

        lines = text.split('\n')
        for line in lines:
            stripped = line.strip()
            # 检查标题
            if stripped.startswith(('#', '##', '###', '####')):
                return True
            # 检查列表
            if stripped.startswith(('- ', '* ')):
                return True
            # 检查引用
            if stripped.startswith('> '):
                return True
            # 检查代码块
            if line.startswith('    ') or line.startswith('\t'):
                return True
            # 检查行内元素
            if any(pattern in line for pattern in ['**', '__', '`', '[', '|']):
                return True

        return False

    # ========== 保留的原始方法（向后兼容） ==========

    @classmethod
    def print_separator(cls):
        """打印分隔线"""
        cls.console.print("━" * 50, style="dim")

    @classmethod
    def print_welcome(cls, model_name: str, provider: str, tools_count: int, claude_md_info: str = None):
        """打印欢迎信息 - 增强样式"""
        title = "[bold cyan]🤖 Build Your Own Claude Code[/] - [yellow]Enhanced Edition[/]"

        content = f"""
[cyan]✓ Model:[/] {model_name} [dim]({provider})[/]
[cyan]✓ Tools:[/] {tools_count} built-in
[cyan]✓ Commands:[/] Type [bold]/help[/] to see available commands
"""

        if claude_md_info:
            content += f"\n[yellow]{claude_md_info}[/]"

        panel = Panel(
            content.strip(),
            border_style="blue",
            padding=(1, 2)
        )
        cls.console.print(panel)

    @classmethod
    def print_user_prompt(cls):
        """打印用户输入提示"""
        cls.console.print("👤 You: ", end="", style="green")

    @classmethod
    def print_assistant_response_header(cls):
        """打印 AI 响应头"""
        cls.console.print("🤖 Assistant:", style="blue bold")
```

---

### 阶段 3：集成到代码（5分钟）

#### 3.1 检测 Agent 响应中的代码块

**文件**：`src/main.py`

在输出 Agent 响应时，检测并单独渲染代码块：

```python
# 在 main() 函数中的输出处理部分
final_response = result.get("final_response", "")
if final_response:
    # 检测并提取代码块
    import re
    code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', final_response, re.DOTALL)

    if code_blocks:
        # 有代码块 - 使用 Markdown 渲染（会自动高亮代码）
        OutputFormatter.print_assistant_response(final_response)
    else:
        # 无代码块 - 直接打印
        OutputFormatter.print_assistant_response(final_response)
```

#### 3.2 工具结果展示优化

```python
# 在处理工具执行结果时
if result.success:
    OutputFormatter.success(f"✓ {tool_name} completed")
    # 如果输出是表格数据，使用表格显示
    if _is_table_format(result.output):
        OutputFormatter.print_table(headers, rows, title=f"{tool_name} Results")
else:
    OutputFormatter.error(f"❌ {tool_name} failed: {result.error}")
```

---

## 📊 效果对比

### 原始输出：
```
2 + 2 = 4
```

### 改进后的输出：
```
┌──────────────────────────────────────┐
│           🤖 Assistant               │
│                                      │
│ 2 + 2 = 4                            │
│                                      │
└──────────────────────────────────────┘
```

### Markdown 支持示例：

**输入**：Tell me about Python lists

**原始输出**：
```
Lists are a fundamental data structure in Python.

# Key Features:
- Ordered collection
- Mutable (can be modified)
- Heterogeneous (can contain different types)

Example:
    my_list = [1, 2, 3]
    my_list.append(4)
```

**改进后的输出**：
```
┌────────────────────────────────────────┐
│         🤖 Assistant                   │
│                                        │
│ Lists are a fundamental data structure │
│ in Python.                             │
│                                        │
│ # Key Features:                        │ (渲染为大标题)
│ • Ordered collection                   │ (列表项)
│ • Mutable (can be modified)            │
│ • Heterogeneous (can contain diff...) │
│                                        │
│ Example:                               │
│ ┌──────────────────────────────────┐  │
│ │ my_list = [1, 2, 3]          ⬜  │  │ (高亮代码)
│ │ my_list.append(4)            ⬜  │  │
│ └──────────────────────────────────┘  │
│                                        │
└────────────────────────────────────────┘
```

---

## 🔧 实现步骤

### Step 1: 清理依赖
```bash
# 编辑 requirements.txt
# 移除 prompt-toolkit 一行
# 保留 rich>=13.0.0
```

### Step 2: 改造 OutputFormatter
- 用 `Rich.Console` 替换 `print()`
- 实现 Markdown 检测
- 实现代码块渲染
- 实现表格显示
- 保持向后兼容

### Step 3: 集成到主程序
- 更新 Agent 响应输出逻辑
- 测试 Markdown 渲染效果
- 测试代码块高亮

### Step 4: 测试用例

**Test Case 1: 简单问答**
```
Input: "2+2"
Expected: 响应在 Panel 中显示
```

**Test Case 2: Markdown 响应**
```
Input: "explain decorators in python"
Expected: 代码块高亮，标题显示，列表格式化
```

**Test Case 3: 代码块**
```
Input: "write hello world in python"
Expected: 代码块用 monokai 主题高亮显示
```

**Test Case 4: 工具结果**
```
Input: "list files in directory"
Expected: 文件列表用表格格式化显示
```

---

## 📝 向后兼容性

所有原始方法保留：
- ✅ `print_separator()`
- ✅ `print_welcome()`
- ✅ `print_user_prompt()`
- ✅ `print_assistant_response_header()`
- ✅ `success()`, `error()`, `info()`, `warning()`
- ✅ `tool_use()`, `tool_result()`

只是在底层用 Rich Console 而不是 print()，对外部调用者完全透明。

---

## 🎨 Rich 特性清单

### 已用特性：
- ✅ Console（统一输出点）
- ✅ Markdown（自动解析和渲染）
- ✅ Syntax（代码高亮）
- ✅ Table（数据表格）
- ✅ Panel（内容框）
- ✅ Style（颜色和样式）

### 未来可用特性（Phase 4）：
- ⏳ Progress（进度条）
- ⏳ Live（实时更新）
- ⏳ Tree（目录树）
- ⏳ Log（日志输出）

---

## 📦 依赖影响

**安装包大小**：
- 当前：~150KB（仅 anthropic + pydantic）
- 添加 Rich：~200KB（rich 本身只有 ~50KB）
- 影响：≈ 33% 增长（仍然很小）

**启动时间**：
- Rich 是轻量级库，import 时间 < 50ms
- 对用户体验无影响

---

## ✅ 验收标准

1. ✅ requirements.txt 已清理
2. ✅ OutputFormatter 支持 Markdown 渲染
3. ✅ 代码块显示带语法高亮
4. ✅ Agent 响应在 Panel 中显示
5. ✅ 所有原始功能仍然工作
6. ✅ 测试通过（至少 4 个测试 case）
7. ✅ 无新的 bug 或错误

---

## 📌 总结

- **总耗时**：~45 分钟
- **依赖增加**：~50KB
- **性能影响**：无
- **用户体验**：显著提升 ⬆️⬆️⬆️
- **代码复杂度**：低（Rich 非常易用）

这是一个 **低风险、高回报** 的改进！
