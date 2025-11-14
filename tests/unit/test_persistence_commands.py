"""
Unit tests for Persistence Commands

Tests save, load, list, and delete operations for conversation persistence.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from src.commands.persistence_commands import (
    SaveCommand,
    LoadCommand,
    ListConversationsCommand,
    DeleteConversationCommand,
)
from src.commands.base import CLIContext


@pytest.mark.unit
class TestSaveCommandProperties:
    """Tests for SaveCommand properties"""

    def test_save_command_name(self):
        """Test SaveCommand name"""
        cmd = SaveCommand()
        assert cmd.name == "save"

    def test_save_command_description(self):
        """Test SaveCommand description"""
        cmd = SaveCommand()
        assert cmd.description == "Save current conversation"

    def test_save_command_aliases(self):
        """Test SaveCommand aliases"""
        cmd = SaveCommand()
        assert cmd.aliases == []


@pytest.mark.unit
class TestSaveCommandExecution:
    """Tests for SaveCommand execution"""

    @pytest.mark.asyncio
    async def test_save_command_without_persistence(self):
        """Test SaveCommand when persistence not available"""
        cmd = SaveCommand()
        agent = Mock()
        context = CLIContext(agent, {})

        result = await cmd.execute("", context)
        assert "Persistence not available" in result

    @pytest.mark.asyncio
    async def test_save_command_with_explicit_id(self):
        """Test SaveCommand with explicit conversation ID"""
        cmd = SaveCommand()
        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.messages = [Mock(model_dump=Mock(return_value={"role": "user"}))]
        agent.context_manager.system_prompt = "System prompt"
        agent.context_manager.summary = "Summary"
        agent.todo_manager = Mock()
        agent.todo_manager.get_all = Mock(return_value=[])

        persistence = Mock()
        persistence.save_conversation = Mock(return_value="/path/to/conv.json")

        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("test_conv_id", context)

        assert "Conversation saved: test_conv_id" in result
        assert "/path/to/conv.json" in result
        persistence.save_conversation.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_command_auto_generates_id(self):
        """Test SaveCommand auto-generates ID when not provided"""
        cmd = SaveCommand()
        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.messages = []
        agent.context_manager.system_prompt = ""
        agent.context_manager.summary = ""
        agent.todo_manager = Mock()
        agent.todo_manager.get_all = Mock(return_value=[])

        persistence = Mock()
        persistence.auto_save_id = Mock(return_value="auto_20250114_120000")
        persistence.save_conversation = Mock(return_value="/path/to/auto.json")

        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("", context)

        assert "Conversation saved" in result
        persistence.auto_save_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_command_serializes_messages(self):
        """Test SaveCommand serializes messages correctly"""
        cmd = SaveCommand()
        agent = Mock()
        mock_message = Mock()
        mock_message.model_dump = Mock(return_value={"role": "user", "content": "test"})
        agent.context_manager = Mock()
        agent.context_manager.messages = [mock_message]
        agent.context_manager.system_prompt = "System"
        agent.context_manager.summary = "Summary"
        agent.todo_manager = Mock()
        agent.todo_manager.get_all = Mock(return_value=[{"status": "pending"}])

        persistence = Mock()
        persistence.auto_save_id = Mock(return_value="conv_id")
        persistence.save_conversation = Mock(return_value="/path/file.json")

        context = CLIContext(agent, {"persistence": persistence})

        await cmd.execute("", context)

        call_args = persistence.save_conversation.call_args
        assert call_args[0][1] == [{"role": "user", "content": "test"}]  # messages
        assert call_args[0][2] == "System"  # system_prompt
        assert call_args[0][3] == "Summary"  # summary
        assert call_args[0][4] == {"todos": [{"status": "pending"}]}  # metadata

    @pytest.mark.asyncio
    async def test_save_command_strips_whitespace_from_id(self):
        """Test SaveCommand strips whitespace from conversation ID"""
        cmd = SaveCommand()
        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.messages = []
        agent.context_manager.system_prompt = ""
        agent.context_manager.summary = ""
        agent.todo_manager = Mock()
        agent.todo_manager.get_all = Mock(return_value=[])

        persistence = Mock()
        persistence.save_conversation = Mock(return_value="/path/file.json")

        context = CLIContext(agent, {"persistence": persistence})

        await cmd.execute("  my_conv_id  ", context)

        call_args = persistence.save_conversation.call_args
        assert call_args[0][0] == "my_conv_id"


@pytest.mark.unit
class TestLoadCommandProperties:
    """Tests for LoadCommand properties"""

    def test_load_command_name(self):
        """Test LoadCommand name"""
        cmd = LoadCommand()
        assert cmd.name == "load"

    def test_load_command_description(self):
        """Test LoadCommand description"""
        cmd = LoadCommand()
        assert cmd.description == "Load a saved conversation"

    def test_load_command_aliases(self):
        """Test LoadCommand aliases"""
        cmd = LoadCommand()
        assert cmd.aliases == []


@pytest.mark.unit
class TestLoadCommandExecution:
    """Tests for LoadCommand execution"""

    @pytest.mark.asyncio
    async def test_load_command_without_persistence(self):
        """Test LoadCommand when persistence not available"""
        cmd = LoadCommand()
        agent = Mock()
        context = CLIContext(agent, {})

        result = await cmd.execute("conv_id", context)
        assert "Persistence not available" in result

    @pytest.mark.asyncio
    async def test_load_command_without_id(self):
        """Test LoadCommand without conversation ID"""
        cmd = LoadCommand()
        agent = Mock()
        persistence = Mock()
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("", context)
        assert "Usage: /load <conversation_id>" in result

    @pytest.mark.asyncio
    async def test_load_command_conversation_not_found(self):
        """Test LoadCommand when conversation doesn't exist"""
        cmd = LoadCommand()
        agent = Mock()
        persistence = Mock()
        persistence.load_conversation = Mock(return_value=None)
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("nonexistent", context)
        assert "Conversation not found: nonexistent" in result

    @pytest.mark.asyncio
    async def test_load_command_restores_conversation(self):
        """Test LoadCommand restores conversation data"""
        cmd = LoadCommand()
        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.clear = Mock()
        agent.context_manager.set_system_prompt = Mock()
        agent.context_manager.messages = []
        agent.context_manager.summary = ""
        agent.todo_manager = Mock()
        agent.todo_manager.update = Mock()

        conversation_data = {
            "system_prompt": "System",
            "summary": "Summary",
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello"}
            ],
            "metadata": {"todos": [{"status": "pending"}]}
        }

        persistence = Mock()
        persistence.load_conversation = Mock(return_value=conversation_data)
        context = CLIContext(agent, {"persistence": persistence})

        with patch('src.agents.context_manager.Message') as mock_message:
            mock_message.return_value = Mock()
            result = await cmd.execute("test_conv", context)

            assert "Conversation loaded: test_conv" in result
            assert "Messages: 2" in result
            agent.context_manager.clear.assert_called_once()
            agent.context_manager.set_system_prompt.assert_called_once_with("System")

    @pytest.mark.asyncio
    async def test_load_command_restores_todos(self):
        """Test LoadCommand restores todos from metadata"""
        cmd = LoadCommand()
        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.clear = Mock()
        agent.context_manager.set_system_prompt = Mock()
        agent.context_manager.messages = []
        agent.context_manager.summary = ""
        agent.todo_manager = Mock()

        conversation_data = {
            "system_prompt": "",
            "summary": "",
            "messages": [],
            "metadata": {"todos": [{"content": "Task 1", "status": "pending"}]}
        }

        persistence = Mock()
        persistence.load_conversation = Mock(return_value=conversation_data)
        context = CLIContext(agent, {"persistence": persistence})

        await cmd.execute("conv_id", context)

        agent.todo_manager.update.assert_called_once_with([{"content": "Task 1", "status": "pending"}])

    @pytest.mark.asyncio
    async def test_load_command_handles_missing_metadata(self):
        """Test LoadCommand handles missing metadata gracefully"""
        cmd = LoadCommand()
        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.clear = Mock()
        agent.context_manager.set_system_prompt = Mock()
        agent.context_manager.messages = []
        agent.context_manager.summary = ""
        agent.todo_manager = Mock()

        conversation_data = {
            "system_prompt": "System",
            "summary": "Summary",
            "messages": []
        }

        persistence = Mock()
        persistence.load_conversation = Mock(return_value=conversation_data)
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("conv_id", context)
        assert "Conversation loaded" in result
        agent.todo_manager.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_command_strips_whitespace_from_id(self):
        """Test LoadCommand strips whitespace from conversation ID"""
        cmd = LoadCommand()
        agent = Mock()
        persistence = Mock()
        persistence.load_conversation = Mock(return_value=None)
        context = CLIContext(agent, {"persistence": persistence})

        await cmd.execute("  conv_id  ", context)

        persistence.load_conversation.assert_called_once_with("conv_id")


@pytest.mark.unit
class TestListConversationsCommandProperties:
    """Tests for ListConversationsCommand properties"""

    def test_list_conversations_command_name(self):
        """Test ListConversationsCommand name"""
        cmd = ListConversationsCommand()
        assert cmd.name == "conversations"

    def test_list_conversations_command_description(self):
        """Test ListConversationsCommand description"""
        cmd = ListConversationsCommand()
        assert cmd.description == "List all saved conversations"

    def test_list_conversations_command_aliases(self):
        """Test ListConversationsCommand aliases"""
        cmd = ListConversationsCommand()
        assert "list" in cmd.aliases
        assert "ls" in cmd.aliases


@pytest.mark.unit
class TestListConversationsCommandExecution:
    """Tests for ListConversationsCommand execution"""

    @pytest.mark.asyncio
    async def test_list_conversations_without_persistence(self):
        """Test ListConversationsCommand when persistence not available"""
        cmd = ListConversationsCommand()
        agent = Mock()
        context = CLIContext(agent, {})

        result = await cmd.execute("", context)
        assert "Persistence not available" in result

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self):
        """Test ListConversationsCommand with no conversations"""
        cmd = ListConversationsCommand()
        agent = Mock()
        persistence = Mock()
        persistence.list_conversations = Mock(return_value=[])
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("", context)
        assert "No saved conversations" in result

    @pytest.mark.asyncio
    async def test_list_conversations_displays_conversations(self):
        """Test ListConversationsCommand displays saved conversations"""
        cmd = ListConversationsCommand()
        agent = Mock()
        persistence = Mock()
        persistence.list_conversations = Mock(return_value=[
            {
                "id": "conv_1",
                "timestamp": "2025-01-14T12:00:00",
                "message_count": 5
            },
            {
                "id": "conv_2",
                "timestamp": "2025-01-14T13:00:00",
                "message_count": 10
            }
        ])
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("", context)

        assert "Saved Conversations" in result
        assert "conv_1" in result
        assert "conv_2" in result
        assert "5" in result
        assert "10" in result

    @pytest.mark.asyncio
    async def test_list_conversations_shows_last_10(self):
        """Test ListConversationsCommand shows only last 10 conversations"""
        cmd = ListConversationsCommand()
        agent = Mock()

        # Create 15 conversations
        conversations = [
            {
                "id": f"conv_{i}",
                "timestamp": f"2025-01-14T{12+i:02d}:00:00",
                "message_count": i
            }
            for i in range(15)
        ]

        persistence = Mock()
        persistence.list_conversations = Mock(return_value=conversations)
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("", context)

        assert "... and 5 more" in result
        assert result.count("\n") > 10  # Should have more than 10 lines

    @pytest.mark.asyncio
    async def test_list_conversations_formats_timestamp(self):
        """Test ListConversationsCommand formats timestamp correctly"""
        cmd = ListConversationsCommand()
        agent = Mock()
        persistence = Mock()
        persistence.list_conversations = Mock(return_value=[
            {
                "id": "test_conv",
                "timestamp": "2025-01-14T12:30:45.123456",
                "message_count": 5
            }
        ])
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("", context)

        assert "2025-01-14T12:30:45" in result
        assert "Messages: 5" in result


@pytest.mark.unit
class TestDeleteConversationCommandProperties:
    """Tests for DeleteConversationCommand properties"""

    def test_delete_command_name(self):
        """Test DeleteConversationCommand name"""
        cmd = DeleteConversationCommand()
        assert cmd.name == "delete"

    def test_delete_command_description(self):
        """Test DeleteConversationCommand description"""
        cmd = DeleteConversationCommand()
        assert cmd.description == "Delete a saved conversation"

    def test_delete_command_aliases(self):
        """Test DeleteConversationCommand aliases"""
        cmd = DeleteConversationCommand()
        assert "rm" in cmd.aliases


@pytest.mark.unit
class TestDeleteConversationCommandExecution:
    """Tests for DeleteConversationCommand execution"""

    @pytest.mark.asyncio
    async def test_delete_command_without_persistence(self):
        """Test DeleteConversationCommand when persistence not available"""
        cmd = DeleteConversationCommand()
        agent = Mock()
        context = CLIContext(agent, {})

        result = await cmd.execute("conv_id", context)
        assert "Persistence not available" in result

    @pytest.mark.asyncio
    async def test_delete_command_without_id(self):
        """Test DeleteConversationCommand without conversation ID"""
        cmd = DeleteConversationCommand()
        agent = Mock()
        persistence = Mock()
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("", context)
        assert "Usage: /delete <conversation_id>" in result

    @pytest.mark.asyncio
    async def test_delete_command_success(self):
        """Test DeleteConversationCommand successfully deletes conversation"""
        cmd = DeleteConversationCommand()
        agent = Mock()
        persistence = Mock()
        persistence.delete_conversation = Mock(return_value=True)
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("conv_to_delete", context)

        assert "Conversation deleted: conv_to_delete" in result
        persistence.delete_conversation.assert_called_once_with("conv_to_delete")

    @pytest.mark.asyncio
    async def test_delete_command_not_found(self):
        """Test DeleteConversationCommand when conversation doesn't exist"""
        cmd = DeleteConversationCommand()
        agent = Mock()
        persistence = Mock()
        persistence.delete_conversation = Mock(return_value=False)
        context = CLIContext(agent, {"persistence": persistence})

        result = await cmd.execute("nonexistent", context)

        assert "Conversation not found: nonexistent" in result

    @pytest.mark.asyncio
    async def test_delete_command_strips_whitespace_from_id(self):
        """Test DeleteConversationCommand strips whitespace from conversation ID"""
        cmd = DeleteConversationCommand()
        agent = Mock()
        persistence = Mock()
        persistence.delete_conversation = Mock(return_value=True)
        context = CLIContext(agent, {"persistence": persistence})

        await cmd.execute("  conv_id  ", context)

        persistence.delete_conversation.assert_called_once_with("conv_id")


@pytest.mark.unit
class TestPersistenceCommandsIntegration:
    """Integration tests for persistence commands"""

    def test_all_persistence_commands_have_required_properties(self):
        """Test all persistence commands have required properties"""
        commands = [
            SaveCommand(),
            LoadCommand(),
            ListConversationsCommand(),
            DeleteConversationCommand(),
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
    async def test_all_persistence_commands_are_async_executable(self):
        """Test all persistence commands are async executable"""
        commands = [
            SaveCommand(),
            LoadCommand(),
            ListConversationsCommand(),
            DeleteConversationCommand(),
        ]

        for cmd in commands:
            import inspect
            assert inspect.iscoroutinefunction(cmd.execute)

    def test_persistence_command_names_are_unique(self):
        """Test persistence command names are unique"""
        commands = [
            SaveCommand(),
            LoadCommand(),
            ListConversationsCommand(),
            DeleteConversationCommand(),
        ]

        names = set()
        for cmd in commands:
            assert cmd.name not in names, f"Duplicate command name: {cmd.name}"
            names.add(cmd.name)

    def test_persistence_command_aliases_no_conflicts(self):
        """Test persistence command aliases don't conflict with names"""
        commands = [
            SaveCommand(),
            LoadCommand(),
            ListConversationsCommand(),
            DeleteConversationCommand(),
        ]

        all_names = {cmd.name for cmd in commands}
        all_aliases = set()

        for cmd in commands:
            for alias in cmd.aliases:
                assert alias not in all_names, f"Alias '{alias}' conflicts with command name"
                assert alias not in all_aliases, f"Duplicate alias '{alias}'"
                all_aliases.add(alias)

    @pytest.mark.asyncio
    async def test_commands_handle_no_persistence_gracefully(self):
        """Test all commands handle missing persistence gracefully"""
        commands = [
            SaveCommand(),
            LoadCommand(),
            ListConversationsCommand(),
            DeleteConversationCommand(),
        ]

        agent = Mock()
        context = CLIContext(agent, {})

        for cmd in commands:
            result = await cmd.execute("test", context)
            assert "Persistence not available" in result or "Usage:" in result or "not found" in result

    @pytest.mark.asyncio
    async def test_save_and_load_workflow(self):
        """Test save and load workflow together"""
        save_cmd = SaveCommand()
        load_cmd = LoadCommand()

        agent = Mock()
        agent.context_manager = Mock()
        agent.context_manager.clear = Mock()
        agent.context_manager.set_system_prompt = Mock()
        agent.context_manager.messages = [Mock(model_dump=Mock(return_value={"role": "user"}))]
        agent.context_manager.system_prompt = "System"
        agent.context_manager.summary = "Summary"
        agent.context_manager.summary = ""
        agent.todo_manager = Mock()
        agent.todo_manager.get_all = Mock(return_value=[])
        agent.todo_manager.update = Mock()

        persistence = Mock()
        persistence.auto_save_id = Mock(return_value="test_conv")
        persistence.save_conversation = Mock(return_value="/path/file.json")
        persistence.load_conversation = Mock(return_value={
            "system_prompt": "System",
            "summary": "Summary",
            "messages": [{"role": "user", "content": "Hi"}],
            "metadata": {"todos": []}
        })

        context = CLIContext(agent, {"persistence": persistence})

        # Save
        save_result = await save_cmd.execute("", context)
        assert "Conversation saved" in save_result

        # Load
        with patch('src.agents.context_manager.Message'):
            load_result = await load_cmd.execute("test_conv", context)
            assert "Conversation loaded" in load_result
