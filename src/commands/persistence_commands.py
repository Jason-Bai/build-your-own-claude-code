"""Commands for conversation persistence"""

from typing import Optional
from .base import Command, CLIContext


class SaveCommand(Command):
    """保存当前对话"""

    @property
    def name(self) -> str:
        return "save"

    @property
    def description(self) -> str:
        return "Save current conversation"

    @property
    def aliases(self):
        return []

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        persistence = context.config.get("persistence")
        if not persistence:
            return "❌ Persistence not available"

        # 使用参数作为 conversation_id，或者自动生成
        conversation_id = args.strip() if args.strip() else persistence.auto_save_id()

        # 保存对话
        file_path = persistence.save_conversation(
            conversation_id,
            [msg.model_dump() for msg in context.agent.context_manager.messages],
            context.agent.context_manager.system_prompt,
            context.agent.context_manager.summary,
            {"todos": context.agent.todo_manager.get_all()}
        )

        return f"✓ Conversation saved: {conversation_id}\n  File: {file_path}"


class LoadCommand(Command):
    """加载保存的对话"""

    @property
    def name(self) -> str:
        return "load"

    @property
    def description(self) -> str:
        return "Load a saved conversation"

    @property
    def aliases(self):
        return []

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        persistence = context.config.get("persistence")
        if not persistence:
            return "❌ Persistence not available"

        conversation_id = args.strip()
        if not conversation_id:
            return "❌ Usage: /load <conversation_id>"

        # 加载对话
        data = persistence.load_conversation(conversation_id)
        if not data:
            return f"❌ Conversation not found: {conversation_id}"

        # 恢复状态
        context.agent.context_manager.clear()
        context.agent.context_manager.set_system_prompt(data.get("system_prompt", ""))
        context.agent.context_manager.summary = data.get("summary", "")

        # 恢复消息
        from ..agents.context_manager import Message
        for msg_data in data.get("messages", []):
            context.agent.context_manager.messages.append(Message(**msg_data))

        # 恢复 todos
        if "metadata" in data and "todos" in data["metadata"]:
            context.agent.todo_manager.update(data["metadata"]["todos"])

        message_count = len(data.get("messages", []))
        return f"✓ Conversation loaded: {conversation_id}\n  Messages: {message_count}"


class ListConversationsCommand(Command):
    """列出所有保存的对话"""

    @property
    def name(self) -> str:
        return "conversations"

    @property
    def description(self) -> str:
        return "List all saved conversations"

    @property
    def aliases(self):
        return ["list", "ls"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        persistence = context.config.get("persistence")
        if not persistence:
            return "❌ Persistence not available"

        conversations = persistence.list_conversations()

        if not conversations:
            return "No saved conversations"

        output = ["📋 Saved Conversations:", ""]

        for i, conv in enumerate(conversations[:10], 1):  # 只显示最近 10 个
            output.append(f"  {i}. {conv['id']}")
            output.append(f"     Time: {conv['timestamp'][:19]}")
            output.append(f"     Messages: {conv['message_count']}")
            output.append("")

        if len(conversations) > 10:
            output.append(f"... and {len(conversations) - 10} more")

        return "\n".join(output)


class DeleteConversationCommand(Command):
    """删除保存的对话"""

    @property
    def name(self) -> str:
        return "delete"

    @property
    def description(self) -> str:
        return "Delete a saved conversation"

    @property
    def aliases(self):
        return ["rm"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        persistence = context.config.get("persistence")
        if not persistence:
            return "❌ Persistence not available"

        conversation_id = args.strip()
        if not conversation_id:
            return "❌ Usage: /delete <conversation_id>"

        # 删除对话
        if persistence.delete_conversation(conversation_id):
            return f"✓ Conversation deleted: {conversation_id}"
        else:
            return f"❌ Conversation not found: {conversation_id}"
