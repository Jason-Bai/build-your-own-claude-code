"""Commands module exports"""

from .base import Command, CLIContext, CommandRegistry, command_registry
from .builtin import (
    HelpCommand,
    ClearCommand,
    ExitCommand,
    StatusCommand,
    TodosCommand
)
from .persistence_commands import (
    SaveCommand,
    LoadCommand,
    ListConversationsCommand,
    DeleteConversationCommand
)
from .checkpoint_commands import (
    CheckpointCommand
)
from .session_commands import (
    SessionCommand
)
from .workspace_commands import (
    InitCommand,
    ShowContextCommand,
    LoadContextCommand
)
from .output_commands import (
    VerboseCommand,
    QuietCommand
)
from .logging_commands import (
    LogCommand
)
from .permission_commands import (
    CheckPermissionsCommand
)


def register_builtin_commands():
    """注册所有内置命令"""
    command_registry.register(HelpCommand())
    command_registry.register(ClearCommand())
    command_registry.register(ExitCommand())
    command_registry.register(StatusCommand())
    command_registry.register(TodosCommand())
    command_registry.register(SaveCommand())
    command_registry.register(LoadCommand())
    command_registry.register(ListConversationsCommand())
    command_registry.register(DeleteConversationCommand())
    # Checkpoint commands
    command_registry.register(CheckpointCommand())
    # Session commands
    command_registry.register(SessionCommand())
    # Workspace commands
    command_registry.register(InitCommand())
    command_registry.register(ShowContextCommand())
    command_registry.register(LoadContextCommand())
    # Output commands
    command_registry.register(VerboseCommand())
    command_registry.register(QuietCommand())
    # Logging commands
    command_registry.register(LogCommand())
    # Permission commands
    command_registry.register(CheckPermissionsCommand())


__all__ = [
    "Command",
    "CLIContext",
    "CommandRegistry",
    "command_registry",
    "register_builtin_commands",
]
