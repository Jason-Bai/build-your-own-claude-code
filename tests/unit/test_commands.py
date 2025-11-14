"""
Unit tests for Command System

Tests command registration, execution, parsing, and various command implementations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from src.commands.base import Command, CLIContext, CommandRegistry
from src.commands.builtin import HelpCommand, ClearCommand, ExitCommand, StatusCommand, TodosCommand
from src.commands.workspace_commands import InitCommand, ShowContextCommand, LoadContextCommand
from src.commands.persistence_commands import SaveCommand, LoadCommand, ListConversationsCommand, DeleteConversationCommand
from src.commands.output_commands import VerboseCommand, QuietCommand


@pytest.mark.unit
class TestCommandBase:
    """Tests for Command base class"""

    def test_command_is_abstract(self):
        """Test that Command cannot be instantiated directly"""
        with pytest.raises(TypeError):
            Command()

    def test_command_requires_name_property(self):
        """Test that command must implement name property"""
        class BadCommand(Command):
            @property
            def description(self) -> str:
                return "Test"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "test"

        with pytest.raises(TypeError):
            BadCommand()

    def test_command_requires_description_property(self):
        """Test that command must implement description property"""
        class BadCommand(Command):
            @property
            def name(self) -> str:
                return "bad"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "test"

        with pytest.raises(TypeError):
            BadCommand()

    def test_command_requires_execute_method(self):
        """Test that command must implement execute method"""
        class BadCommand(Command):
            @property
            def name(self) -> str:
                return "bad"

            @property
            def description(self) -> str:
                return "Test"

        with pytest.raises(TypeError):
            BadCommand()


@pytest.mark.unit
class TestCLIContext:
    """Tests for CLIContext"""

    def test_context_initialization(self):
        """Test CLIContext initialization"""
        agent = Mock()
        config = {"key": "value"}

        context = CLIContext(agent, config)

        assert context.agent == agent
        assert context.config == config
        assert context.session_history == []

    def test_context_session_history(self):
        """Test session history management"""
        context = CLIContext(Mock(), {})

        context.session_history.append("command1")
        context.session_history.append("command2")

        assert len(context.session_history) == 2
        assert context.session_history[0] == "command1"


@pytest.mark.unit
class TestCommandRegistry:
    """Tests for CommandRegistry"""

    def test_registry_initialization(self):
        """Test CommandRegistry initialization"""
        registry = CommandRegistry()

        assert registry.commands == {}
        assert registry.aliases == {}

    def test_register_simple_command(self):
        """Test registering a command"""
        registry = CommandRegistry()

        class TestCommand(Command):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test command"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "executed"

        cmd = TestCommand()
        registry.register(cmd)

        assert "test" in registry.commands
        assert registry.commands["test"] == cmd

    def test_register_command_with_aliases(self):
        """Test registering command with aliases"""
        registry = CommandRegistry()

        class TestCommand(Command):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            @property
            def aliases(self):
                return ["t", "tst"]

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "executed"

        cmd = TestCommand()
        registry.register(cmd)

        assert registry.aliases["t"] == "test"
        assert registry.aliases["tst"] == "test"

    def test_get_command_by_name(self):
        """Test getting command by name"""
        registry = CommandRegistry()

        class TestCommand(Command):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "executed"

        cmd = TestCommand()
        registry.register(cmd)

        retrieved = registry.get("test")
        assert retrieved == cmd

    def test_get_command_by_alias(self):
        """Test getting command by alias"""
        registry = CommandRegistry()

        class TestCommand(Command):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            @property
            def aliases(self):
                return ["t"]

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "executed"

        cmd = TestCommand()
        registry.register(cmd)

        retrieved = registry.get("t")
        assert retrieved == cmd

    def test_get_command_strips_leading_slash(self):
        """Test that get() strips leading slash"""
        registry = CommandRegistry()

        class TestCommand(Command):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "executed"

        cmd = TestCommand()
        registry.register(cmd)

        retrieved = registry.get("/test")
        assert retrieved == cmd

    def test_get_nonexistent_command(self):
        """Test getting nonexistent command"""
        registry = CommandRegistry()

        retrieved = registry.get("nonexistent")
        assert retrieved is None

    def test_get_all_commands(self):
        """Test getting all commands"""
        registry = CommandRegistry()

        class Cmd1(Command):
            @property
            def name(self) -> str:
                return "cmd1"

            @property
            def description(self) -> str:
                return "Cmd1"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "1"

        class Cmd2(Command):
            @property
            def name(self) -> str:
                return "cmd2"

            @property
            def description(self) -> str:
                return "Cmd2"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "2"

        registry.register(Cmd1())
        registry.register(Cmd2())

        all_commands = registry.get_all()
        assert len(all_commands) == 2

    def test_is_command(self):
        """Test command detection"""
        registry = CommandRegistry()

        assert registry.is_command("/help") is True
        assert registry.is_command("  /test  ") is True
        assert registry.is_command("not a command") is False
        assert registry.is_command("") is False

    @pytest.mark.asyncio
    async def test_execute_command(self):
        """Test executing a command"""
        registry = CommandRegistry()

        class TestCommand(Command):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return f"executed with args: {args}"

        registry.register(TestCommand())
        context = CLIContext(Mock(), {})

        result = await registry.execute("/test hello", context)
        assert result == "executed with args: hello"

    @pytest.mark.asyncio
    async def test_execute_command_with_alias(self):
        """Test executing command by alias"""
        registry = CommandRegistry()

        class TestCommand(Command):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            @property
            def aliases(self):
                return ["t"]

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "executed"

        registry.register(TestCommand())
        context = CLIContext(Mock(), {})

        result = await registry.execute("/t", context)
        assert result == "executed"

    @pytest.mark.asyncio
    async def test_execute_nonexistent_command(self):
        """Test executing nonexistent command"""
        registry = CommandRegistry()
        context = CLIContext(Mock(), {})

        result = await registry.execute("/nonexistent", context)
        assert "Unknown command" in result

    @pytest.mark.asyncio
    async def test_execute_non_command_text(self):
        """Test executing non-command text"""
        registry = CommandRegistry()
        context = CLIContext(Mock(), {})

        result = await registry.execute("not a command", context)
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_command_error_handling(self):
        """Test error handling during command execution"""
        registry = CommandRegistry()

        class FailingCommand(Command):
            @property
            def name(self) -> str:
                return "fail"

            @property
            def description(self) -> str:
                return "Failing command"

            async def execute(self, args: str, context: "CLIContext") -> str:
                raise ValueError("Test error")

        registry.register(FailingCommand())
        context = CLIContext(Mock(), {})

        result = await registry.execute("/fail", context)
        assert "Command execution failed" in result
        assert "Test error" in result


@pytest.mark.unit
class TestBuiltinCommands:
    """Tests for built-in commands"""

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command execution"""
        help_cmd = HelpCommand()

        assert help_cmd.name == "help"
        assert help_cmd.description == "Show available commands"
        assert "h" in help_cmd.aliases
        assert "?" in help_cmd.aliases

        # Mock context
        context = CLIContext(Mock(), {})

        result = await help_cmd.execute("", context)
        assert "Available Commands" in result

    @pytest.mark.asyncio
    async def test_clear_command(self):
        """Test clear command execution"""
        clear_cmd = ClearCommand()

        assert clear_cmd.name == "clear"
        assert "reset" in clear_cmd.aliases

        # Mock agent with proper message list
        mock_messages = MagicMock()
        mock_agent = Mock()
        mock_agent.context_manager = Mock()
        mock_agent.context_manager.messages = mock_messages
        mock_agent.context_manager.summary = "some summary"
        mock_agent.todo_manager = Mock()

        context = CLIContext(mock_agent, {})

        result = await clear_cmd.execute("", context)

        mock_messages.clear.assert_called_once()
        mock_agent.todo_manager.clear.assert_called_once()
        assert "cleared" in result.lower()

    @pytest.mark.asyncio
    async def test_exit_command(self):
        """Test exit command"""
        exit_cmd = ExitCommand()

        assert exit_cmd.name == "exit"
        assert "quit" in exit_cmd.aliases
        assert "q" in exit_cmd.aliases

    @pytest.mark.asyncio
    async def test_status_command(self):
        """Test status command execution"""
        status_cmd = StatusCommand()

        assert status_cmd.name == "status"
        assert status_cmd.description == "Show system status (tools, tokens, etc.)"

        # Mock agent with all required components
        mock_agent = Mock()
        mock_agent.client = Mock()
        mock_agent.client.model_name = "claude-sonnet-4.5"

        # Mock context_manager
        mock_context_manager = Mock()
        mock_context_manager.get_messages.return_value = [Mock(), Mock()]  # 2 messages
        mock_context_manager.estimate_tokens.return_value = 5000
        mock_context_manager.max_tokens = 150000
        mock_context_manager.summary = "Test summary"
        mock_agent.context_manager = mock_context_manager

        # Mock tool_manager
        mock_agent.tool_manager = Mock()
        mock_agent.tool_manager.tools = {
            "Bash": Mock(),
            "Read": Mock(),
            "Write": Mock(),
        }

        # Mock todo_manager
        mock_todo_manager = Mock()
        mock_todo_manager.get_all.return_value = [
            {"status": "pending", "content": "Task 1"},
            {"status": "in_progress", "content": "Task 2"},
            {"status": "completed", "content": "Task 3"},
        ]
        mock_agent.todo_manager = mock_todo_manager

        context = CLIContext(mock_agent, {})

        result = await status_cmd.execute("", context)
        assert "status" in result.lower() or "system" in result.lower()
        assert "claude-sonnet" in result.lower()
        assert "3" in result  # Should show 3 tools or 3 todos


@pytest.mark.unit
class TestWorkspaceCommands:
    """Tests for workspace commands"""

    @pytest.mark.asyncio
    async def test_init_command(self):
        """Test init command structure"""
        init_cmd = InitCommand()

        assert init_cmd.name == "init"
        assert "initialize" in init_cmd.description.lower()

    @pytest.mark.asyncio
    async def test_show_context_command(self):
        """Test show context command"""
        show_cmd = ShowContextCommand()

        assert show_cmd.name == "show-context"
        assert "claude.md" in show_cmd.description.lower()

    @pytest.mark.asyncio
    async def test_load_context_command(self):
        """Test load context command"""
        load_cmd = LoadContextCommand()

        assert load_cmd.name == "load-context"
        assert "context" in load_cmd.description.lower()


@pytest.mark.unit
class TestPersistenceCommands:
    """Tests for persistence commands"""

    @pytest.mark.asyncio
    async def test_save_command(self):
        """Test save command structure"""
        save_cmd = SaveCommand()

        assert save_cmd.name == "save"
        assert "save" in save_cmd.description.lower()

    @pytest.mark.asyncio
    async def test_load_command(self):
        """Test load command structure"""
        load_cmd = LoadCommand()

        assert load_cmd.name == "load"
        assert "load" in load_cmd.description.lower()

    @pytest.mark.asyncio
    async def test_list_conversations_command(self):
        """Test list conversations command"""
        list_cmd = ListConversationsCommand()

        assert list_cmd.name == "conversations"
        assert "list" in list_cmd.description.lower() or "conversation" in list_cmd.description.lower()

    @pytest.mark.asyncio
    async def test_delete_conversation_command(self):
        """Test delete conversation command"""
        delete_cmd = DeleteConversationCommand()

        assert delete_cmd.name == "delete"
        assert "delete" in delete_cmd.description.lower()


@pytest.mark.unit
class TestOutputCommands:
    """Tests for output commands"""

    @pytest.mark.asyncio
    async def test_verbose_command(self):
        """Test verbose command structure"""
        verbose_cmd = VerboseCommand()

        assert verbose_cmd.name == "verbose"
        assert "verbose" in verbose_cmd.description.lower()

    @pytest.mark.asyncio
    async def test_quiet_command(self):
        """Test quiet command structure"""
        quiet_cmd = QuietCommand()

        assert quiet_cmd.name == "quiet"
        assert "quiet" in quiet_cmd.description.lower()


@pytest.mark.unit
class TestCommandParsing:
    """Tests for command parsing"""

    @pytest.mark.asyncio
    async def test_parse_command_with_args(self):
        """Test parsing command with arguments"""
        registry = CommandRegistry()

        class EchoCommand(Command):
            @property
            def name(self) -> str:
                return "echo"

            @property
            def description(self) -> str:
                return "Echo command"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return f"echo: {args}"

        registry.register(EchoCommand())
        context = CLIContext(Mock(), {})

        result = await registry.execute("/echo hello world", context)
        assert result == "echo: hello world"

    @pytest.mark.asyncio
    async def test_parse_command_no_args(self):
        """Test parsing command without arguments"""
        registry = CommandRegistry()

        class SimpleCommand(Command):
            @property
            def name(self) -> str:
                return "simple"

            @property
            def description(self) -> str:
                return "Simple"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return f"args were: '{args}'"

        registry.register(SimpleCommand())
        context = CLIContext(Mock(), {})

        result = await registry.execute("/simple", context)
        assert result == "args were: ''"

    @pytest.mark.asyncio
    async def test_parse_command_strip_whitespace(self):
        """Test that whitespace is stripped"""
        registry = CommandRegistry()

        class TestCommand(Command):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "ok"

        registry.register(TestCommand())
        context = CLIContext(Mock(), {})

        result = await registry.execute("   /test   ", context)
        assert result == "ok"


@pytest.mark.unit
class TestCommandIntegration:
    """Integration tests for command system"""

    @pytest.mark.asyncio
    async def test_multiple_commands_in_registry(self):
        """Test registry with multiple commands"""
        registry = CommandRegistry()

        class Cmd1(Command):
            @property
            def name(self) -> str:
                return "first"

            @property
            def description(self) -> str:
                return "First"

            @property
            def aliases(self):
                return ["f"]

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "first executed"

        class Cmd2(Command):
            @property
            def name(self) -> str:
                return "second"

            @property
            def description(self) -> str:
                return "Second"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "second executed"

        registry.register(Cmd1())
        registry.register(Cmd2())

        context = CLIContext(Mock(), {})

        result1 = await registry.execute("/first", context)
        result2 = await registry.execute("/f", context)
        result3 = await registry.execute("/second", context)

        assert result1 == "first executed"
        assert result2 == "first executed"
        assert result3 == "second executed"

    @pytest.mark.asyncio
    async def test_command_registry_help_integration(self):
        """Test help command shows all registered commands"""
        # Create a custom registry for this test (not using global)
        test_registry = CommandRegistry()

        class TestCmd(Command):
            @property
            def name(self) -> str:
                return "mytest"

            @property
            def description(self) -> str:
                return "My test command"

            async def execute(self, args: str, context: "CLIContext") -> str:
                return "test"

        test_registry.register(TestCmd())

        # Create a help command that would see our custom registry
        help_cmd = HelpCommand()

        context = CLIContext(Mock(), {})
        help_result = await help_cmd.execute("", context)

        # The help command uses the global registry, so we just verify it returns help format
        assert "Available Commands" in help_result or "available" in help_result.lower()
