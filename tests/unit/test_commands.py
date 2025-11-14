"""
Unit tests for Builtin and Persistence Commands

Tests help, clear, exit, status, todos commands and persistence operations.
"""

import pytest
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.commands.base import CLIContext
from src.commands.builtin import (
    HelpCommand, ClearCommand, ExitCommand, StatusCommand, TodosCommand
)
from src.commands.persistence_commands import (
    SaveCommand, LoadCommand, ListConversationsCommand, DeleteConversationCommand
)


@pytest.mark.unit
class TestHelpCommand:
    """Tests for HelpCommand"""

    @pytest.mark.asyncio
    async def test_help_command_name(self):
        """Test HelpCommand has correct name"""
        cmd = HelpCommand()
        assert cmd.name == "help"

    @pytest.mark.asyncio
    async def test_help_command_description(self):
        """Test HelpCommand has description"""
        cmd = HelpCommand()
        assert "command" in cmd.description.lower()

    @pytest.mark.asyncio
    async def test_help_command_aliases(self):
        """Test HelpCommand has aliases"""
        cmd = HelpCommand()
        assert "h" in cmd.aliases
        assert "?" in cmd.aliases

    @pytest.mark.asyncio
    async def test_help_command_execute(self):
        """Test HelpCommand executes and returns help text"""
        cmd = HelpCommand()
        context = Mock()

        with patch('src.commands.base.command_registry') as mock_registry:
            mock_registry.get_all.return_value = [
                Mock(name="test", description="Test command", aliases=[])
            ]
            result = await cmd.execute("", context)

            assert result is not None
            assert "Available Commands" in result or "available" in result.lower()


@pytest.mark.unit
class TestClearCommand:
    """Tests for ClearCommand"""

    @pytest.mark.asyncio
    async def test_clear_command_name(self):
        """Test ClearCommand has correct name"""
        cmd = ClearCommand()
        assert cmd.name == "clear"

    @pytest.mark.asyncio
    async def test_clear_command_description(self):
        """Test ClearCommand has description"""
        cmd = ClearCommand()
        assert "clear" in cmd.description.lower() or "history" in cmd.description.lower()

    @pytest.mark.asyncio
    async def test_clear_command_aliases(self):
        """Test ClearCommand has aliases"""
        cmd = ClearCommand()
        assert "reset" in cmd.aliases

    @pytest.mark.asyncio
    async def test_clear_command_clears_messages(self):
        """Test ClearCommand clears conversation messages"""
        cmd = ClearCommand()

        mock_agent = Mock()
        mock_agent.context_manager.messages = Mock()
        mock_agent.context_manager.summary = "summary"
        mock_agent.todo_manager = Mock()

        context = Mock()
        context.agent = mock_agent

        result = await cmd.execute("", context)

        mock_agent.context_manager.messages.clear.assert_called()
        mock_agent.todo_manager.clear.assert_called()
        assert "cleared" in result.lower() or "✓" in result

    @pytest.mark.asyncio
    async def test_clear_command_returns_success_message(self):
        """Test ClearCommand returns success message"""
        cmd = ClearCommand()
        context = Mock()
        context.agent.context_manager.messages = []
        context.agent.todo_manager.clear = Mock()

        result = await cmd.execute("", context)

        assert result is not None
        assert len(result) > 0


@pytest.mark.unit
class TestExitCommand:
    """Tests for ExitCommand"""

    @pytest.mark.asyncio
    async def test_exit_command_name(self):
        """Test ExitCommand has correct name"""
        cmd = ExitCommand()
        assert cmd.name == "exit"

    @pytest.mark.asyncio
    async def test_exit_command_aliases(self):
        """Test ExitCommand has aliases"""
        cmd = ExitCommand()
        assert "quit" in cmd.aliases
        assert "q" in cmd.aliases

    @pytest.mark.asyncio
    async def test_exit_command_calls_sys_exit(self):
        """Test ExitCommand calls sys.exit"""
        cmd = ExitCommand()
        context = Mock()

        with patch('builtins.print'):
            with patch('sys.exit') as mock_exit:
                await cmd.execute("", context)
                mock_exit.assert_called_once_with(0)


@pytest.mark.unit
class TestStatusCommand:
    """Tests for StatusCommand"""

    @pytest.mark.asyncio
    async def test_status_command_name(self):
        """Test StatusCommand has correct name"""
        cmd = StatusCommand()
        assert cmd.name == "status"

    @pytest.mark.asyncio
    async def test_status_command_description(self):
        """Test StatusCommand has description"""
        cmd = StatusCommand()
        assert "status" in cmd.description.lower()

    @pytest.mark.asyncio
    async def test_status_command_aliases(self):
        """Test StatusCommand has aliases"""
        cmd = StatusCommand()
        assert "info" in cmd.aliases

    @pytest.mark.asyncio
    async def test_status_command_returns_status_info(self):
        """Test StatusCommand returns system status"""
        cmd = StatusCommand()

        mock_agent = Mock()
        mock_agent.client.model_name = "test-model"
        mock_agent.context_manager.get_messages.return_value = [{"msg": "1"}, {"msg": "2"}]
        mock_agent.context_manager.estimate_tokens.return_value = 100
        mock_agent.context_manager.max_tokens = 1000
        mock_agent.context_manager.summary = "test summary"
        mock_agent.tool_manager.tools = {"tool1": Mock()}
        mock_agent.todo_manager.get_all.return_value = [
            {"status": "pending"},
            {"status": "in_progress"},
            {"status": "completed"}
        ]

        context = Mock()
        context.agent = mock_agent

        result = await cmd.execute("", context)

        assert result is not None
        assert "Model" in result or "model" in result
        assert "2" in result or "Message" in result


@pytest.mark.unit
class TestTodosCommand:
    """Tests for TodosCommand"""

    @pytest.mark.asyncio
    async def test_todos_command_name(self):
        """Test TodosCommand has correct name"""
        cmd = TodosCommand()
        assert cmd.name == "todos"

    @pytest.mark.asyncio
    async def test_todos_command_aliases(self):
        """Test TodosCommand has aliases"""
        cmd = TodosCommand()
        assert "tasks" in cmd.aliases

    @pytest.mark.asyncio
    async def test_todos_command_empty_list(self):
        """Test TodosCommand with no todos"""
        cmd = TodosCommand()

        mock_agent = Mock()
        mock_agent.todo_manager.get_all.return_value = []

        context = Mock()
        context.agent = mock_agent

        result = await cmd.execute("", context)

        assert "No todos" in result

    @pytest.mark.asyncio
    async def test_todos_command_lists_todos(self):
        """Test TodosCommand lists todos with emojis"""
        cmd = TodosCommand()

        mock_agent = Mock()
        mock_agent.todo_manager.get_all.return_value = [
            {"status": "pending", "content": "Task 1"},
            {"status": "in_progress", "content": "Task 2"},
            {"status": "completed", "content": "Task 3"}
        ]

        context = Mock()
        context.agent = mock_agent

        result = await cmd.execute("", context)

        assert "Task 1" in result or "task" in result.lower()
        assert result is not None


@pytest.mark.unit
class TestSaveCommand:
    """Tests for SaveCommand"""

    @pytest.mark.asyncio
    async def test_save_command_name(self):
        """Test SaveCommand has correct name"""
        cmd = SaveCommand()
        assert cmd.name == "save"

    @pytest.mark.asyncio
    async def test_save_command_description(self):
        """Test SaveCommand has description"""
        cmd = SaveCommand()
        assert "save" in cmd.description.lower()

    @pytest.mark.asyncio
    async def test_save_command_no_persistence(self):
        """Test SaveCommand when persistence unavailable"""
        cmd = SaveCommand()

        context = Mock()
        context.config = {"persistence": None}

        result = await cmd.execute("", context)

        assert "not available" in result.lower() or "❌" in result

    @pytest.mark.asyncio
    async def test_save_command_with_custom_id(self):
        """Test SaveCommand with custom conversation ID"""
        cmd = SaveCommand()

        mock_persistence = Mock()
        mock_persistence.save_conversation.return_value = "/path/file.json"

        mock_agent = Mock()
        mock_agent.context_manager.messages = []
        mock_agent.context_manager.system_prompt = "prompt"
        mock_agent.context_manager.summary = "summary"
        mock_agent.todo_manager.get_all.return_value = []

        context = Mock()
        context.config = {"persistence": mock_persistence}
        context.agent = mock_agent

        result = await cmd.execute("my_conv", context)

        mock_persistence.save_conversation.assert_called_once()
        assert "saved" in result.lower() or "✓" in result

    @pytest.mark.asyncio
    async def test_save_command_auto_generate_id(self):
        """Test SaveCommand auto-generates ID when none provided"""
        cmd = SaveCommand()

        mock_persistence = Mock()
        mock_persistence.auto_save_id.return_value = "auto_20240101_120000"
        mock_persistence.save_conversation.return_value = "/path/file.json"

        mock_agent = Mock()
        mock_agent.context_manager.messages = []
        mock_agent.context_manager.system_prompt = "prompt"
        mock_agent.context_manager.summary = "summary"
        mock_agent.todo_manager.get_all.return_value = []

        context = Mock()
        context.config = {"persistence": mock_persistence}
        context.agent = mock_agent

        result = await cmd.execute("", context)

        assert "saved" in result.lower() or "✓" in result


@pytest.mark.unit
class TestLoadCommand:
    """Tests for LoadCommand"""

    @pytest.mark.asyncio
    async def test_load_command_name(self):
        """Test LoadCommand has correct name"""
        cmd = LoadCommand()
        assert cmd.name == "load"

    @pytest.mark.asyncio
    async def test_load_command_no_id(self):
        """Test LoadCommand without conversation ID"""
        cmd = LoadCommand()

        context = Mock()
        context.config = {"persistence": Mock()}

        result = await cmd.execute("", context)

        assert "Usage" in result or "❌" in result

    @pytest.mark.asyncio
    async def test_load_command_not_found(self):
        """Test LoadCommand when conversation not found"""
        cmd = LoadCommand()

        mock_persistence = Mock()
        mock_persistence.load_conversation.return_value = None

        context = Mock()
        context.config = {"persistence": mock_persistence}

        result = await cmd.execute("nonexistent", context)

        assert "not found" in result.lower() or "❌" in result

    @pytest.mark.asyncio
    async def test_load_command_successful_load(self):
        """Test LoadCommand successfully loads conversation"""
        cmd = LoadCommand()

        mock_persistence = Mock()
        mock_persistence.load_conversation.return_value = {
            "system_prompt": "System",
            "summary": "Summary",
            "messages": [],
            "metadata": {"todos": []}
        }

        mock_agent = Mock()
        mock_agent.context_manager.clear = Mock()
        mock_agent.context_manager.set_system_prompt = Mock()
        mock_agent.context_manager.messages = []
        mock_agent.context_manager.summary = "Summary"
        mock_agent.todo_manager.update = Mock()

        context = Mock()
        context.config = {"persistence": mock_persistence}
        context.agent = mock_agent

        result = await cmd.execute("test_id", context)

        mock_persistence.load_conversation.assert_called_once_with("test_id")
        assert "loaded" in result.lower() or "✓" in result


@pytest.mark.unit
class TestListConversationsCommand:
    """Tests for ListConversationsCommand"""

    @pytest.mark.asyncio
    async def test_list_command_name(self):
        """Test ListConversationsCommand has correct name"""
        cmd = ListConversationsCommand()
        assert cmd.name == "conversations"

    @pytest.mark.asyncio
    async def test_list_command_aliases(self):
        """Test ListConversationsCommand has aliases"""
        cmd = ListConversationsCommand()
        assert "list" in cmd.aliases or "ls" in cmd.aliases

    @pytest.mark.asyncio
    async def test_list_command_no_persistence(self):
        """Test ListConversationsCommand when persistence unavailable"""
        cmd = ListConversationsCommand()

        context = Mock()
        context.config = {"persistence": None}

        result = await cmd.execute("", context)

        assert "not available" in result.lower() or "❌" in result

    @pytest.mark.asyncio
    async def test_list_command_empty_list(self):
        """Test ListConversationsCommand with no conversations"""
        cmd = ListConversationsCommand()

        mock_persistence = Mock()
        mock_persistence.list_conversations.return_value = []

        context = Mock()
        context.config = {"persistence": mock_persistence}

        result = await cmd.execute("", context)

        assert "No saved" in result or "no" in result.lower()

    @pytest.mark.asyncio
    async def test_list_command_shows_conversations(self):
        """Test ListConversationsCommand lists conversations"""
        cmd = ListConversationsCommand()

        mock_persistence = Mock()
        mock_persistence.list_conversations.return_value = [
            {"id": "conv1", "timestamp": "2024-01-01T10:00:00", "message_count": 5},
            {"id": "conv2", "timestamp": "2024-01-01T11:00:00", "message_count": 3}
        ]

        context = Mock()
        context.config = {"persistence": mock_persistence}

        result = await cmd.execute("", context)

        assert "conv1" in result or "conv2" in result


@pytest.mark.unit
class TestDeleteConversationCommand:
    """Tests for DeleteConversationCommand"""

    @pytest.mark.asyncio
    async def test_delete_command_name(self):
        """Test DeleteConversationCommand has correct name"""
        cmd = DeleteConversationCommand()
        assert cmd.name == "delete"

    @pytest.mark.asyncio
    async def test_delete_command_aliases(self):
        """Test DeleteConversationCommand has aliases"""
        cmd = DeleteConversationCommand()
        assert "rm" in cmd.aliases

    @pytest.mark.asyncio
    async def test_delete_command_no_id(self):
        """Test DeleteConversationCommand without ID"""
        cmd = DeleteConversationCommand()

        context = Mock()
        context.config = {"persistence": Mock()}

        result = await cmd.execute("", context)

        assert "Usage" in result or "❌" in result

    @pytest.mark.asyncio
    async def test_delete_command_successful_delete(self):
        """Test DeleteConversationCommand successfully deletes"""
        cmd = DeleteConversationCommand()

        mock_persistence = Mock()
        mock_persistence.delete_conversation.return_value = True

        context = Mock()
        context.config = {"persistence": mock_persistence}

        result = await cmd.execute("test_id", context)

        assert "deleted" in result.lower() or "✓" in result

    @pytest.mark.asyncio
    async def test_delete_command_not_found(self):
        """Test DeleteConversationCommand when conversation not found"""
        cmd = DeleteConversationCommand()

        mock_persistence = Mock()
        mock_persistence.delete_conversation.return_value = False

        context = Mock()
        context.config = {"persistence": mock_persistence}

        result = await cmd.execute("nonexistent", context)

        assert "not found" in result.lower() or "❌" in result


@pytest.mark.unit
class TestCommandProperties:
    """Tests for command properties and attributes"""

    def test_all_commands_have_name(self):
        """Test all commands have name property"""
        commands = [
            HelpCommand(), ClearCommand(), ExitCommand(), StatusCommand(), TodosCommand(),
            SaveCommand(), LoadCommand(), ListConversationsCommand(), DeleteConversationCommand()
        ]

        for cmd in commands:
            assert hasattr(cmd, 'name')
            assert isinstance(cmd.name, str)
            assert len(cmd.name) > 0

    def test_all_commands_have_description(self):
        """Test all commands have description"""
        commands = [
            HelpCommand(), ClearCommand(), ExitCommand(), StatusCommand(), TodosCommand(),
            SaveCommand(), LoadCommand(), ListConversationsCommand(), DeleteConversationCommand()
        ]

        for cmd in commands:
            assert hasattr(cmd, 'description')
            assert isinstance(cmd.description, str)

    def test_all_commands_have_aliases(self):
        """Test all commands have aliases"""
        commands = [
            HelpCommand(), ClearCommand(), ExitCommand(), StatusCommand(), TodosCommand(),
            SaveCommand(), LoadCommand(), ListConversationsCommand(), DeleteConversationCommand()
        ]

        for cmd in commands:
            assert hasattr(cmd, 'aliases')
            assert isinstance(cmd.aliases, list)

    def test_all_commands_have_execute(self):
        """Test all commands have execute method"""
        commands = [
            HelpCommand(), ClearCommand(), ExitCommand(), StatusCommand(), TodosCommand(),
            SaveCommand(), LoadCommand(), ListConversationsCommand(), DeleteConversationCommand()
        ]

        for cmd in commands:
            assert hasattr(cmd, 'execute')
            assert callable(cmd.execute)
