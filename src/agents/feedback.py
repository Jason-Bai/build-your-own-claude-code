"""
Agent反馈系统 - 收集和管理Agent执行过程中的简化反馈信息
"""

from enum import Enum
from typing import List


class FeedbackLevel(Enum):
    """反馈级别 - 控制反馈的详尽程度"""
    SILENT = 0      # 静默，不输出任何中间过程
    MINIMAL = 1     # 最小化，只输出关键状态变化和工具调用
    VERBOSE = 2     # 详细，输出所有中间过程


class AgentFeedback:
    """
    Agent反馈信息收集器

    用于收集Agent执行过程中的简化反馈信息，供UI层实时显示
    不包含完整的内部细节，只显示用户关心的关键信息
    """

    def __init__(self, level: FeedbackLevel = FeedbackLevel.MINIMAL):
        """
        初始化反馈收集器

        Args:
            level: 反馈级别，控制收集的详尽程度
        """
        self.level = level
        self.messages: List[str] = []

    def add_tool_call(self, tool_name: str, brief_description: str):
        """
        添加工具调用反馈

        示例: add_tool_call("bash", "execute: ls -R")
        输出: "🔧 Using bash: execute: ls -R"

        Args:
            tool_name: 工具名称（如 "bash", "read", "grep"）
            brief_description: 简短的操作描述（LLM提供的工具参数概要）
        """
        if self.level.value >= FeedbackLevel.MINIMAL.value:
            msg = f"🔧 Using {tool_name}: {brief_description}"
            self.messages.append(msg)

    def add_tool_completed(self, tool_name: str):
        """
        添加工具完成反馈

        示例: add_tool_completed("bash")
        输出: "✓ bash completed"

        Args:
            tool_name: 工具名称
        """
        if self.level.value >= FeedbackLevel.MINIMAL.value:
            msg = f"✓ {tool_name} completed"
            self.messages.append(msg)

    def add_status(self, status: str):
        """
        添加状态变化反馈

        示例: add_status("Analyzing results...")
        输出: "ℹ️  Analyzing results..."

        Args:
            status: 状态描述
        """
        if self.level.value >= FeedbackLevel.MINIMAL.value:
            msg = f"ℹ️  {status}"
            self.messages.append(msg)

    def add_error(self, error: str):
        """
        添加错误反馈（总是显示，不受级别限制）

        示例: add_error("Tool execution failed")
        输出: "❌ Tool execution failed"

        Args:
            error: 错误信息
        """
        msg = f"❌ {error}"
        self.messages.append(msg)

    def add_thinking(self):
        """
        添加思考状态反馈

        示例: add_thinking()
        输出: "💭 Thinking..."
        """
        if self.level.value >= FeedbackLevel.MINIMAL.value:
            msg = "💭 Thinking..."
            self.messages.append(msg)

    def get_all(self) -> List[str]:
        """
        获取所有反馈消息

        Returns:
            包含所有反馈消息的列表
        """
        return self.messages

    def clear(self):
        """清空所有反馈消息"""
        self.messages = []

    def has_messages(self) -> bool:
        """检查是否有反馈消息"""
        return len(self.messages) > 0
