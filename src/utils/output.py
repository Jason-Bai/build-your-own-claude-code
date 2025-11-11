"""Output formatting utilities for terminal display"""

from typing import Optional
from enum import Enum
import json


class OutputLevel(Enum):
    """输出级别"""
    QUIET = 0    # 只输出错误和 Agent 回复
    NORMAL = 1   # 默认：关键信息（工具调用、成功/失败）
    VERBOSE = 2  # 详细信息（工具参数、思考过程、执行结果）


class OutputFormatter:
    """统一的输出格式化工具"""

    level: OutputLevel = OutputLevel.NORMAL

    @classmethod
    def set_level(cls, level: OutputLevel):
        """设置输出级别"""
        cls.level = level

    @classmethod
    def success(cls, msg: str):
        """成功信息"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            print(f"✓ {msg}")

    @classmethod
    def error(cls, msg: str):
        """错误信息（总是显示）"""
        print(f"❌ {msg}")

    @classmethod
    def info(cls, msg: str):
        """信息提示"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            print(f"ℹ️  {msg}")

    @classmethod
    def warning(cls, msg: str):
        """警告信息"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            print(f"⚠️  {msg}")

    @classmethod
    def thinking(cls, msg: str = "Thinking..."):
        """AI 思考过程（verbose 模式）"""
        if cls.level.value >= OutputLevel.VERBOSE.value:
            print(f"💭 {msg}")

    @classmethod
    def tool_use(cls, tool_name: str, params: Optional[dict] = None):
        """工具使用通知"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            print(f"🔧 {tool_name}")

        if cls.level.value >= OutputLevel.VERBOSE.value and params:
            print(f"   Parameters: {json.dumps(params, indent=2)}")

    @classmethod
    def tool_result(cls, tool_name: str, success: bool, output: str = ""):
        """工具执行结果（verbose 模式）"""
        if cls.level.value >= OutputLevel.VERBOSE.value:
            status = "✓" if success else "✗"
            # 限制输出长度
            display_output = output[:100] + "..." if len(output) > 100 else output
            print(f"   {status} Result: {display_output}")

    @classmethod
    def debug(cls, msg: str):
        """调试信息（verbose 模式）"""
        if cls.level.value >= OutputLevel.VERBOSE.value:
            print(f"🐛 {msg}")

    @classmethod
    def agent_response(cls, text: str):
        """Agent 回复（总是显示）"""
        print(f"\n🤖 {text}\n")

    @classmethod
    def separator(cls, char: str = "=", length: int = 50):
        """分隔线"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            print(char * length)

    @classmethod
    def section(cls, title: str):
        """章节标题"""
        if cls.level.value >= OutputLevel.NORMAL.value:
            print(f"\n{'='*50}")
            print(f"{title}")
            print(f"{'='*50}")
