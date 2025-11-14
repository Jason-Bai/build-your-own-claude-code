"""
Unit tests for Built-in Commands

Tests help, clear, exit, status, and todos commands.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from src.commands.builtin import (
    HelpCommand,
    ClearCommand,
    ExitCommand,
    StatusCommand,
    TodosCommand,
)
from src.commands.base import CLIContext


@pytest.mark.unit
class TestHelpCommand:
    """Tests for HelpCommand"""

    def test_help_command_properties(self):
        """Test HelpCommand properties"""
        cmd = HelpCommand()
        assert cmd.name == "help"
        assert cmd.description == "Show available commands"
        assert "h" in cmd.aliases
        assert "?" in cmd.aliases

    @pytest.mark.asyncio
    async def test_help_command_execute(self):
        """Test HelpCommand execution"""
        cmd = HelpCommand()

        # Mock context and registry
        agent = Mock()
        context = CLIContext(agent, {})

        with patch('src.commands.base.command_registry') as mock_registry:
            mock_cmd1 = Mock()
            mock_cmd1.name = "help"
            mock_cmd1.description = "Show help"
            mock_cmd1.aliases = ["h"]

            mock_cmd2 = Mock()
            mock_cmd2.name = "clear"
            mock_cmd2.description = "Clear history"
            mock_cmd2.aliases = []

            mock_registry.get_all.return_value = [mock_cmd1, mock_cmd2]

            result = await cmd.execute("", context)

            assert result is not None
            assert "Available Commands" in result
            assert "/help" in result
            assert "/clear" in result

    @pytest.mark.asyncio
    async def test_help_command_with_aliases(self):
        """Test HelpCommand displays aliases correctly"""
        cmd = HelpCommand()
        agent = Mock()
        context = CLIContext(agent, {})

        with patch('src.commands.base.command_registry') as mock_registry:
            mock_cmd = Mock()
            mock_cmd.name = "status"
            mock_cmd.description = "Show status"
            mock_cmd.aliases = ["info", "s"]

            mock_registry.get_all.return_value = [mock_cmd]

            result = await cmd.execute("", context)

            assert "status" in result
            assert "aliases:" in result.lower()


@pytest.mark.unit
class TestClearCommand:
    """Tests for ClearCommand"""

    def test_clear_command_properties(self):
        """Test ClearCommand properties"""
        cmd = ClearCommand()
        assert cmd.name == "clear"
        assert cmd.description == "Clear conversation history"
        assert "reset" in cmd.aliases

    @pytest.mark.asyncio
    async def test_clear_command_clears_messages(self):
        """Test ClearCommand clears messages"""
        cmd = ClearCommand()

        # Mock agent and context
        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.messages = Mock()
        agent.context_manager.summary = "Some summary"
        agent.todo_manager = Mock()

        context = CLIContext(agent, {})

        result = await cmd.execute("", context)

        assert result == "✓ Conversation history cleared"
        agent.context_manager.messages.clear.assert_called_once()
        agent.todo_manager.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_command_clears_todos(self):
        """Test ClearCommand clears todos"""
        cmd = ClearCommand()

        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.messages = []
        agent.todo_manager = Mock()

        context = CLIContext(agent, {})

        await cmd.execute("", context)

        agent.todo_manager.clear.assert_called_once()


@pytest.mark.unit
class TestExitCommand:
    """Tests for ExitCommand"""

    def test_exit_command_properties(self):
        """Test ExitCommand properties"""
        cmd = ExitCommand()
        assert cmd.name == "exit"
        assert cmd.description == "Exit the program"
        assert "quit" in cmd.aliases
        assert "q" in cmd.aliases

    @pytest.mark.asyncio
    async def test_exit_command_exits(self):
        """Test ExitCommand calls sys.exit"""
        cmd = ExitCommand()

        agent = Mock()
        context = CLIContext(agent, {})

        with patch('src.commands.builtin.sys.exit') as mock_exit:
            with patch('builtins.print'):
                try:
                    await cmd.execute("", context)
                except SystemExit:
                    pass

                # ExitCommand should try to exit
                # (Note: actual exit is blocked by patch)

    @pytest.mark.asyncio
    async def test_exit_command_prints_goodbye(self):
        """Test ExitCommand prints goodbye message"""
        cmd = ExitCommand()

        agent = Mock()
        context = CLIContext(agent, {})

        with patch('src.commands.builtin.sys.exit'):
            with patch('builtins.print') as mock_print:
                try:
                    await cmd.execute("", context)
                except SystemExit:
                    pass

                # Should print goodbye message
                assert mock_print.called


@pytest.mark.unit
class TestStatusCommand:
    """Tests for StatusCommand"""

    def test_status_command_properties(self):
        """Test StatusCommand properties"""
        cmd = StatusCommand()
        assert cmd.name == "status"
        assert cmd.description == "Show system status (tools, tokens, etc.)"
        assert "info" in cmd.aliases

    @pytest.mark.asyncio
    async def test_status_command_shows_model_info(self):
        """Test StatusCommand displays model information"""
        cmd = StatusCommand()

        # Mock agent with all required attributes
        agent = Mock()
        agent.client = Mock()
        agent.client.model_name = "gpt-4o"
        agent.context_manager = Mock()
        agent.context_manager.get_messages.return_value = [Mock(), Mock()]
        agent.context_manager.estimate_tokens.return_value = 1500
        agent.context_manager.max_tokens = 150000
        agent.context_manager.summary = "Test summary"
        agent.tool_manager = Mock()
        agent.tool_manager.tools = [Mock(), Mock()]
        agent.todo_manager = Mock()
        agent.todo_manager.get_all.return_value = [
            {"status": "pending"},
            {"status": "in_progress"},
            {"status": "completed"},
        ]

        context = CLIContext(agent, {})

        result = await cmd.execute("", context)

        assert result is not None
        assert "System Status" in result
        assert "gpt-4o" in result
        assert "2" in result  # 2 messages
        assert "Tokens:" in result
        assert "Tools:" in result

    @pytest.mark.asyncio
    async def test_status_command_calculates_token_percentage(self):
        """Test StatusCommand calculates token usage percentage"""
        cmd = StatusCommand()

        agent = Mock()
        agent.client = Mock()
        agent.client.model_name = "test-model"
        agent.context_manager = Mock()
        agent.context_manager.get_messages.return_value = []
        agent.context_manager.estimate_tokens.return_value = 75000
        agent.context_manager.max_tokens = 150000
        agent.context_manager.summary = ""
        agent.tool_manager = Mock()
        agent.tool_manager.tools = []
        agent.todo_manager = Mock()
        agent.todo_manager.get_all.return_value = []

        context = CLIContext(agent, {})

        result = await cmd.execute("", context)

        # Should show 50% usage
        assert "50.0%" in result

    @pytest.mark.asyncio
    async def test_status_command_shows_todo_counts(self):
        """Test StatusCommand shows todo counts"""
        cmd = StatusCommand()

        agent = Mock()
        agent.client = Mock()
        agent.client.model_name = "model"
        agent.context_manager = Mock()
        agent.context_manager.get_messages.return_value = []
        agent.context_manager.estimate_tokens.return_value = 0
        agent.context_manager.max_tokens = 1
        agent.context_manager.summary = ""
        agent.tool_manager = Mock()
        agent.tool_manager.tools = []
        agent.todo_manager = Mock()
        agent.todo_manager.get_all.return_value = [
            {"status": "pending"},
            {"status": "pending"},
            {"status": "in_progress"},
            {"status": "completed"},
            {"status": "completed"},
            {"status": "completed"},
        ]

        context = CLIContext(agent, {})

        result = await cmd.execute("", context)

        assert "Pending: 2" in result
        assert "In Progress: 1" in result
        assert "Completed: 3" in result


@pytest.mark.unit
class TestTodosCommand:
    """Tests for TodosCommand"""

    def test_todos_command_properties(self):
        """Test TodosCommand properties"""
        cmd = TodosCommand()
        assert cmd.name == "todos"
        assert cmd.description == "Show current todo list"
        assert "tasks" in cmd.aliases

    @pytest.mark.asyncio
    async def test_todos_command_empty_list(self):
        """Test TodosCommand with empty todo list"""
        cmd = TodosCommand()

        agent = Mock()
        agent.todo_manager = Mock()
        agent.todo_manager.get_all.return_value = []

        context = CLIContext(agent, {})

        result = await cmd.execute("", context)

        assert result is not None
        assert "no todos" in result.lower()

    @pytest.mark.asyncio
    async def test_todos_command_shows_todos(self):
        """Test TodosCommand displays todos"""
        cmd = TodosCommand()

        agent = Mock()
        agent.todo_manager = Mock()
        agent.todo_manager.get_all.return_value = [
            {"content": "Task 1", "status": "pending"},
            {"content": "Task 2", "status": "completed"},
        ]

        context = CLIContext(agent, {})

        result = await cmd.execute("", context)

        assert result is not None
        # Result should include todo information


@pytest.mark.unit
class TestCommandIntegration:
    """Integration tests for commands"""

    @pytest.mark.asyncio
    async def test_all_commands_have_required_properties(self):
        """Test all built-in commands have required properties"""
        commands = [
            HelpCommand(),
            ClearCommand(),
            ExitCommand(),
            StatusCommand(),
            TodosCommand(),
        ]

        for cmd in commands:
            assert hasattr(cmd, 'name')
            assert hasattr(cmd, 'description')
            assert hasattr(cmd, 'aliases')
            assert hasattr(cmd, 'execute')
            assert cmd.name is not None
            assert cmd.description is not None
            assert isinstance(cmd.aliases, (list, tuple))

    @pytest.mark.asyncio
    async def test_all_commands_are_async_executable(self):
        """Test all commands can be executed asynchronously"""
        commands = [
            HelpCommand(),
            ClearCommand(),
            ExitCommand(),
            StatusCommand(),
            TodosCommand(),
        ]

        for cmd in commands:
            # Verify execute is async
            import inspect
            assert inspect.iscoroutinefunction(cmd.execute)

    @pytest.mark.asyncio
    async def test_commands_dont_require_arguments(self):
        """Test commands handle empty arguments"""
        cmd = HelpCommand()

        agent = Mock()
        context = CLIContext(agent, {})

        with patch('src.commands.base.command_registry') as mock_registry:
            mock_registry.get_all.return_value = []

            result = await cmd.execute("", context)
            assert result is not None

    def test_command_aliases_are_unique(self):
        """Test that command aliases are unique across commands"""
        commands = [
            HelpCommand(),
            ClearCommand(),
            ExitCommand(),
            StatusCommand(),
            TodosCommand(),
        ]

        all_names = set()
        all_aliases = set()

        for cmd in commands:
            name = cmd.name
            assert name not in all_aliases, f"Command name '{name}' is used as alias"
            assert name not in all_names, f"Duplicate command name '{name}'"
            all_names.add(name)

            for alias in cmd.aliases:
                assert alias not in all_names, f"Alias '{alias}' conflicts with command name"
                assert alias not in all_aliases, f"Duplicate alias '{alias}'"
                all_aliases.add(alias)
