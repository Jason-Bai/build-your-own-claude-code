"""Output formatting utilities for terminal display - Enhanced with Rich"""

from typing import Optional
from enum import Enum
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.style import Style


class OutputLevel(Enum):
    """输出级别"""
    QUIET = 0    # 只输出错误和 Agent 回复
    NORMAL = 1   # 默认：关键信息（工具调用、成功/失败）
    VERBOSE = 2  # 详细信息（工具参数、思考过程、执行结果）


class OutputFormatter:
    """使用 Rich 增强的统一输出格式化工具"""

    console = Console()
    level: OutputLevel = OutputLevel.NORMAL

    @classmethod
    def set_level(cls, level: OutputLevel):
        """设置输出级别"""
        cls.level = level

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

    @classmethod
    def thinking(cls, msg: str = "Thinking..."):
        """AI 思考过程（verbose 模式）"""
        if cls.level.value >= OutputLevel.VERBOSE.value:
            cls.console.print(f"💭 {msg}", style="dim magenta")

    @classmethod
    def debug(cls, msg: str):
        """调试信息（verbose 模式）"""
        if cls.level.value >= OutputLevel.VERBOSE.value:
            cls.console.print(f"🐛 {msg}", style="dim")

    # ========== 工具相关 ==========

    @classmethod
    def tool_use(cls, tool_name: str, params: Optional[dict] = None):
        """工具使用通知 - 增强显示"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            cls.console.print(f"🔧 {tool_name}", style="yellow")

        if cls.level.value >= OutputLevel.VERBOSE.value and params:
            cls.console.print(f"   Parameters: {json.dumps(params, indent=2)}", style="dim")

    @classmethod
    def tool_result(cls, tool_name: str, success: bool, output: str = ""):
        """工具执行结果（verbose 模式）"""
        if cls.level.value >= OutputLevel.VERBOSE.value:
            status = "✓" if success else "✗"
            style = "green" if success else "red"
            # 限制输出长度
            display_output = output[:200] + "..." if len(output) > 200 else output

            panel = Panel(
                display_output,
                title=f"{status} {tool_name}",
                border_style=style,
                expand=False
            )
            cls.console.print(panel)

    # ========== Agent 响应（核心改进） ==========

    @classmethod
    def print_assistant_response(cls, text: str):
        """打印 AI 响应 - 支持 Markdown 自动渲染"""
        # 检测是否包含 Markdown 元素
        if cls._contains_markdown(text):
            # 用 Panel 包装，Markdown 自动渲染
            md = Markdown(text)
            panel = Panel(
                md,
                title="🤖 Assistant",
                border_style="blue",
                expand=False
            )
            cls.console.print(panel)
        else:
            # 普通文本用 Panel 包装
            panel = Panel(
                text,
                title="🤖 Assistant",
                border_style="blue",
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
            panel = Panel(syntax, title=title, border_style="cyan", expand=False)
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

    # ========== 分隔线和标题 ==========

    @classmethod
    def separator(cls, char: str = "=", length: int = 50):
        """分隔线"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            cls.console.print(char * length, style="dim")

    @classmethod
    def section(cls, title: str):
        """章节标题"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            cls.console.print(f"\n{'='*50}")
            cls.console.print(f"{title}")
            cls.console.print(f"{'='*50}")

    @classmethod
    def print_separator(cls):
        """打印对话分隔线"""
        cls.console.print("━" * 50, style="dim")

    @classmethod
    def print_welcome(cls, model_name: str, provider: str, tools_count: int, claude_md_info: str = None):
        """打印欢迎信息 - 增强样式"""
        welcome_text = f"""[bold cyan]🤖 Build Your Own Claude Code[/] - [yellow]Enhanced Edition[/]

[cyan]✓ Model:[/] {model_name} [dim]({provider})[/]
[cyan]✓ Tools:[/] {tools_count} built-in

[cyan]ℹ️  Commands:[/] Type [bold]/help[/] to see available commands"""

        if claude_md_info:
            welcome_text += f"\n\n{claude_md_info}"

        panel = Panel(
            welcome_text,
            border_style="cyan",
            padding=(1, 2)
        )
        cls.console.print(panel)

    @classmethod
    def print_user_prompt(cls):
        """打印用户输入提示（不带换行，等待输入）"""
        print("👤 You: ", end="", flush=True)

    @classmethod
    def print_user_input(cls, text: str):
        """打印用户输入的内容"""
        # 如果文本为空，只打印换行
        if text:
            cls.console.print(text, style="dim")
        cls.console.print()

    @classmethod
    def print_assistant_response_header(cls):
        """打印 AI 响应头"""
        cls.console.print("🤖 Assistant:", style="bold blue")

    @classmethod
    def agent_response(cls, text: str):
        """Agent 回复（总是显示）"""
        cls.print_assistant_response(text)

    # ========== 辅助方法 ==========

    @staticmethod
    def _contains_markdown(text: str) -> bool:
        """检测文本是否包含 Markdown 元素"""
        markdown_indicators = [
            ('#', '标题'),
            ('##', '子标题'),
            ('`', '代码'),
            ('**', '加粗'),
            ('_', '斜体'),
            ('> ', '引用'),
            ('- ', '列表项'),
            ('* ', '列表项'),
            ('[', '链接'),
            ('|', '表格'),
        ]

        lines = text.split('\n')
        for line in lines:
            stripped = line.strip()

            # 检查标题
            if stripped.startswith(('#', '##', '###', '####')):
                return True

            # 检查列表
            if stripped.startswith(('- ', '* ', '+ ')):
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
