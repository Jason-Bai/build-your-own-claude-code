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
        context.agent.context_manager.messages.clear()
        context.agent.context_manager.summary = ""
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

        # Properly clean up before exiting
        from ..logging import get_action_logger
        from ..logging.constants import DEFAULT_BATCH_TIMEOUT
        import time

        # End session if it exists
        if hasattr(context.agent, 'session_manager'):
            session_manager = context.agent.session_manager
            if session_manager.current_session:
                await session_manager.end_session_async()

        # Wait for worker thread to process the session_end log
        # Worker thread has a batch_timeout (default 1.0s), so we need to wait
        # longer than that to ensure it completes the batch write
        action_logger = get_action_logger()
        wait_time = DEFAULT_BATCH_TIMEOUT + 0.5  # Add 0.5s buffer
        time.sleep(wait_time)

        # Now shutdown the logger (stops worker, flushes queue, closes files)
        action_logger.shutdown()

        # Clean up MCP connections if they exist
        if hasattr(context.agent, 'mcp_client') and context.agent.mcp_client:
            await context.agent.mcp_client.disconnect_all()

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
        total_messages = len(agent.context_manager.get_messages())
        estimated_tokens = agent.context_manager.estimate_tokens()
        max_tokens = agent.context_manager.max_tokens
        token_usage_pct = (estimated_tokens / max_tokens * 100) if max_tokens > 0 else 0

        # 工具统计
        tool_count = len(agent.tool_manager.tools)

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
            f"  Summary length: {len(agent.context_manager.summary)} chars",
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
