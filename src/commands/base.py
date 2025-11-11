"""Command system for CLI"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import sys


class Command(ABC):
    """命令基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """命令名（不含 /）"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """命令描述"""
        pass

    @property
    def aliases(self) -> List[str]:
        """命令别名"""
        return []

    @abstractmethod
    async def execute(self, args: str, context: "CLIContext") -> Optional[str]:
        """
        执行命令

        Args:
            args: 命令参数（命令名后的所有内容）
            context: CLI 上下文

        Returns:
            返回消息（显示给用户）或 None
        """
        pass


class CLIContext:
    """CLI 上下文，Commands 可以访问的资源"""

    def __init__(self, agent, config: Dict):
        self.agent = agent
        self.config = config
        self.session_history: List[str] = []


class CommandRegistry:
    """命令注册表"""

    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.aliases: Dict[str, str] = {}  # alias -> command_name

    def register(self, command: Command):
        """注册命令"""
        self.commands[command.name] = command

        # 注册别名
        for alias in command.aliases:
            self.aliases[alias] = command.name

    def get(self, name: str) -> Optional[Command]:
        """根据名称或别名获取命令"""
        # 去掉开头的 /
        name = name.lstrip("/")

        # 先查找命令
        if name in self.commands:
            return self.commands[name]

        # 再查找别名
        if name in self.aliases:
            return self.commands[self.aliases[name]]

        return None

    def get_all(self) -> List[Command]:
        """获取所有命令"""
        return list(self.commands.values())

    def is_command(self, text: str) -> bool:
        """判断是否是命令"""
        return text.strip().startswith("/")

    async def execute(self, text: str, context: CLIContext) -> Optional[str]:
        """执行命令"""
        text = text.strip()

        if not self.is_command(text):
            return None

        # 解析命令和参数
        parts = text[1:].split(maxsplit=1)  # 去掉开头的 /
        command_name = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        # 查找命令
        command = self.get(command_name)

        if not command:
            return f"❌ Unknown command: /{command_name}\nType /help to see available commands"

        # 执行命令
        try:
            return await command.execute(args, context)
        except Exception as e:
            return f"❌ Command execution failed: {str(e)}"


# 全局注册表
command_registry = CommandRegistry()
