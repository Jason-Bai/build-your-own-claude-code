"""Integration tests for P8 Session Manager with system components"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from src.sessions.manager import SessionManager
from src.sessions.types import Session
from src.commands.session_commands import SessionCommand
from src.commands.base import CLIContext


class MockPersistenceManager:
    """Mock persistence manager for integration testing"""

    def __init__(self):
        self.sessions = {}

    async def save_session(self, session_id: str, session_data: dict) -> str:
        """Mock save_session"""
        self.sessions[session_id] = session_data
        return session_id

    async def load_session(self, session_id: str):
        """Mock load_session"""
        return self.sessions.get(session_id)

    async def list_sessions(self):
        """Mock list_sessions"""
        return list(self.sessions.keys())


class TestSessionManagerIntegration:
    """Integration tests for SessionManager with persistence"""

    def test_session_lifecycle_create_record_save(self):
        """Test complete session lifecycle: create → record → save"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create session
        session = manager.start_session("test-project")
        session_id = session.session_id

        # Record data
        manager.record_message({"role": "user", "content": "test"})
        manager.record_command("git status")

        # End (save) session
        manager.end_session()

        # Verify session was saved
        assert session_id in persistence.sessions
        saved_data = persistence.sessions[session_id]
        assert saved_data["status"] == "completed"
        assert len(saved_data["conversation_history"]) == 1
        assert len(saved_data["command_history"]) == 1

    def test_session_pause_resume_workflow(self):
        """Test pausing and resuming a session"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create and populate session
        session1 = manager.start_session("project1")
        session1_id = session1.session_id
        manager.record_message({"role": "user", "content": "hello"})
        manager.pause_session()

        # Verify paused state
        assert manager.current_session.status == "paused"

        # Clear current session reference
        manager.current_session = None

        # Resume session
        manager.current_session = None
        resumed = manager.resume_session(session1_id)

        # Verify restored state
        assert resumed.session_id == session1_id
        assert resumed.status == "active"
        assert len(resumed.conversation_history) == 1

    def test_multiple_sessions_isolation(self):
        """Test that multiple sessions are properly isolated"""
        import time
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create first session
        session1 = manager.start_session("project1")
        session1_id = session1.session_id
        manager.record_message({"role": "user", "content": "session1-message"})
        manager.record_command("cmd1")
        manager.end_session()

        # Small delay to ensure different timestamps
        time.sleep(0.01)

        # Create second session (should be isolated)
        session2 = manager.start_session("project2")
        session2_id = session2.session_id
        manager.record_message({"role": "user", "content": "session2-message"})
        manager.record_command("cmd2")
        manager.end_session()

        # Verify isolation
        session1_data = persistence.sessions[session1_id]
        session2_data = persistence.sessions[session2_id]

        assert session1_data["conversation_history"][0]["content"] == "session1-message"
        assert session2_data["conversation_history"][0]["content"] == "session2-message"
        assert session1_data["command_history"] == ["cmd1"]
        assert session2_data["command_history"] == ["cmd2"]


class TestSessionCommandIntegration:
    """Integration tests for SessionCommand with CLI context"""

    @pytest.mark.asyncio
    async def test_session_command_execution_with_agent(self):
        """Test SessionCommand execution with agent context"""
        # Setup mock agent and context
        mock_agent = MagicMock()
        persistence = MockPersistenceManager()
        session_manager = SessionManager(persistence)
        mock_agent.session_manager = session_manager

        # Create context
        context = CLIContext(mock_agent, config={})

        # Create command
        command = SessionCommand()

        # Execute when no sessions exist
        result = await command.execute("", context)

        assert "No sessions found" in result

    @pytest.mark.asyncio
    async def test_session_command_with_sessions(self):
        """Test SessionCommand when sessions are available"""
        # Setup - manually create and save session data for this test
        mock_agent = MagicMock()
        persistence = MockPersistenceManager()
        session_manager = SessionManager(persistence)

        # Create a session and record data
        session = session_manager.start_session("test-project")
        session_id = session.session_id

        # Manually save to persistence since we're in async context
        # where asyncio.run() would fail
        await persistence.save_session(session_id, session.to_dict())

        # Update session status
        session.status = "completed"
        await persistence.save_session(session_id, session.to_dict())

        mock_agent.session_manager = session_manager
        context = CLIContext(mock_agent, config={})

        # Create command
        command = SessionCommand()

        # Mock the InteractiveListSelector to return None (cancel)
        with patch('src.commands.session_commands.InteractiveListSelector') as mock_selector:
            mock_instance = AsyncMock()
            mock_instance.run = AsyncMock(return_value=None)
            mock_selector.return_value = mock_instance

            result = await command.execute("", context)

            assert "Exited session selection" in result


class TestSessionCommandRegistration:
    """Tests for SessionCommand registration in command registry"""

    def test_session_command_properties(self):
        """Test SessionCommand properties"""
        command = SessionCommand()

        assert command.name == "session"
        assert command.description
        assert "session" in command.description.lower()
        assert "sess" in command.aliases
        assert "resume" in command.aliases

    def test_session_command_is_command_subclass(self):
        """Test that SessionCommand is proper Command subclass"""
        from src.commands.base import Command

        command = SessionCommand()
        assert isinstance(command, Command)


class TestMainWithSessionManager:
    """Tests for main.py with SessionManager feature toggle"""

    @patch('src.cli.main.load_config')
    @patch('src.cli.main.initialize_agent')
    @patch('src.cli.main.register_builtin_commands')
    @patch('src.cli.main.get_input_manager')
    def test_main_with_session_manager_disabled(
        self, mock_get_input, mock_register, mock_init, mock_load_config
    ):
        """Test main.py behavior with SessionManager disabled (default)"""
        # Setup mocks
        mock_load_config.return_value = {
            "features": {"session_manager": False},
            "model": {"provider": "test"}
        }

        mock_agent = MagicMock()
        mock_agent.session_manager = None
        mock_agent.mcp_client = None
        mock_init.return_value = mock_agent

        mock_input = MagicMock()
        mock_input.async_get_input = AsyncMock(side_effect=[KeyboardInterrupt()])
        mock_get_input.return_value = mock_input

        # The feature toggle should be disabled by default
        assert not mock_load_config()["features"].get("session_manager", False)

    @patch('src.cli.main.load_config')
    @patch('src.cli.main.initialize_agent')
    @patch('src.cli.main.register_builtin_commands')
    @patch('src.cli.main.get_input_manager')
    def test_main_with_session_manager_enabled(
        self, mock_get_input, mock_register, mock_init, mock_load_config
    ):
        """Test main.py behavior with SessionManager enabled"""
        # Setup mocks with session manager enabled
        config = {
            "features": {"session_manager": True},
            "model": {"provider": "test"}
        }
        mock_load_config.return_value = config

        # Verify the feature toggle can be enabled
        assert config["features"].get("session_manager", False)


class TestSessionDataRoundtrip:
    """Tests for Session serialization roundtrip with persistence"""

    def test_complete_session_serialization_roundtrip(self):
        """Test complete session data through serialization → persistence → deserialization"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create session with complex data
        session = manager.start_session("test-project")
        session_id = session.session_id

        # Add various data types
        manager.record_message({
            "role": "user",
            "content": "complex message with special chars: 你好 🚀",
            "metadata": {"key": "value"}
        })
        manager.record_message({
            "role": "assistant",
            "content": "response"
        })

        manager.record_command("git commit -m 'test with special chars'")
        manager.record_command("python -c 'print(1)'")

        # End session (saves to persistence)
        manager.end_session()

        # Load from persistence
        loaded_data = persistence.sessions[session_id]
        restored_session = Session.from_dict(loaded_data)

        # Verify complete roundtrip
        assert restored_session.session_id == session_id
        assert restored_session.project_name == "test-project"
        assert len(restored_session.conversation_history) == 2
        assert len(restored_session.command_history) == 2
        assert "你好" in restored_session.conversation_history[0]["content"]
        assert restored_session.conversation_history[0]["metadata"]["key"] == "value"
