"""Built-in commands implementation"""

import sys
from typing import Optional
from .base import Command, CLIContext


class HelpCommand(Command):
    """显示帮助信息"""

    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "Show available commands"

    @property
    def aliases(self):
        return ["h", "?"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        from .base import command_registry

        output = ["📚 Available Commands:", ""]

        for cmd in command_registry.get_all():
            aliases_str = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
            output.append(f"  /{cmd.name}{aliases_str}")
            output.append(f"    {cmd.description}")
            output.append("")

        return "\n".join(output)


class ClearCommand(Command):
    """清空对话历史"""

    @property
    def name(self) -> str:
        return "clear"

    @property
    def description(self) -> str:
        return "Clear conversation history"

    @property
    def aliases(self):
        return ["reset"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        context.agent.context.messages.clear()
        context.agent.context.summary = ""
        context.agent.todo_manager.clear()

        return "✓ Conversation history cleared"


class ExitCommand(Command):
    """退出程序"""

    @property
    def name(self) -> str:
        return "exit"

    @property
    def description(self) -> str:
        return "Exit the program"

    @property
    def aliases(self):
        return ["quit", "q"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        print("\n👋 Goodbye!")
        sys.exit(0)


class StatusCommand(Command):
    """显示系统状态"""

    @property
    def name(self) -> str:
        return "status"

    @property
    def description(self) -> str:
        return "Show system status (tools, tokens, etc.)"

    @property
    def aliases(self):
        return ["info"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        agent = context.agent

        # 统计信息
        total_messages = len(agent.context.messages)
        estimated_tokens = agent.context.estimate_tokens()
        max_tokens = agent.context.max_tokens
        token_usage_pct = (estimated_tokens / max_tokens * 100) if max_tokens > 0 else 0

        # 工具统计
        tool_count = len(agent.tools.tools)

        # Todo 统计
        todos = agent.todo_manager.get_all()
        pending = sum(1 for t in todos if t["status"] == "pending")
        in_progress = sum(1 for t in todos if t["status"] == "in_progress")
        completed = sum(1 for t in todos if t["status"] == "completed")

        output = [
            "📊 System Status",
            "",
            "🤖 Model:",
            f"  {agent.client.model_name}",
            "",
            "💬 Conversation:",
            f"  Messages: {total_messages}",
            f"  Tokens: ~{estimated_tokens:,} / {max_tokens:,} ({token_usage_pct:.1f}%)",
            f"  Summary length: {len(agent.context.summary)} chars",
            "",
            "🔧 Tools:",
            f"  Total: {tool_count}",
            "",
            "✅ Todos:",
            f"  Pending: {pending}",
            f"  In Progress: {in_progress}",
            f"  Completed: {completed}",
        ]

        return "\n".join(output)


class TodosCommand(Command):
    """显示当前任务列表"""

    @property
    def name(self) -> str:
        return "todos"

    @property
    def description(self) -> str:
        return "Show current todo list"

    @property
    def aliases(self):
        return ["tasks"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        todos = context.agent.todo_manager.get_all()

        if not todos:
            return "No todos"

        output = ["📝 Todo List:", ""]

        status_emoji = {
            "pending": "⏸️",
            "in_progress": "▶️",
            "completed": "✅"
        }

        for i, todo in enumerate(todos, 1):
            emoji = status_emoji.get(todo["status"], "❓")
            content = todo.get("content", "")
            output.append(f"  {i}. {emoji} {content}")

        return "\n".join(output)
