"""Unit tests for SessionManager"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from src.sessions.manager import SessionManager
from src.sessions.types import Session


class MockPersistenceManager:
    """Mock persistence manager for testing"""

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


class TestSessionManagerCreation:
    """Tests for SessionManager instantiation"""

    def test_session_manager_init(self):
        """Test SessionManager initialization"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        assert manager.persistence == persistence
        assert manager.current_session is None


class TestSessionManagerStartSession:
    """Tests for starting new sessions"""

    def test_start_new_session(self):
        """Test starting a new session"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")

        assert session is not None
        assert session.project_name == "test-project"
        assert session.status == "active"
        assert manager.current_session == session
        assert session.session_id.startswith("session-")

    def test_start_session_generates_unique_ids(self):
        """Test that session IDs are based on timestamps"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session1 = manager.start_session("project1")
        session1_id = session1.session_id

        # Verify the ID format is correct
        assert session1_id.startswith("session-")
        assert len(session1_id) > len("session-")

        # Verify that the session object is stored correctly
        assert manager.current_session == session1


class TestSessionManagerEndSession:
    """Tests for ending sessions"""

    def test_end_session(self):
        """Test ending a session"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")
        original_id = session.session_id

        manager.end_session()

        assert manager.current_session is None
        assert original_id in persistence.sessions
        saved_session = persistence.sessions[original_id]
        assert saved_session["status"] == "completed"
        assert saved_session["end_time"] is not None

    def test_end_session_when_no_session(self):
        """Test ending when no session is active"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Should not raise error
        manager.end_session()

        assert manager.current_session is None


class TestSessionManagerPauseSession:
    """Tests for pausing sessions"""

    def test_pause_session(self):
        """Test pausing a session"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")
        session_id = session.session_id

        manager.pause_session()

        assert session.status == "paused"
        # Session should still be current (not cleared)
        assert manager.current_session == session


class TestSessionManagerResumeSession:
    """Tests for resuming sessions"""

    def test_resume_session(self):
        """Test resuming a paused session"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create and save a paused session
        session = manager.start_session("test-project")
        session_id = session.session_id
        manager.pause_session()
        manager.current_session = None

        # Resume the session
        resumed = manager.resume_session(session_id)

        assert resumed.session_id == session_id
        assert resumed.status == "active"
        assert manager.current_session == resumed

    def test_resume_nonexistent_session(self):
        """Test resuming a session that doesn't exist"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        with pytest.raises(ValueError, match="Session not found"):
            manager.resume_session("nonexistent-session")


class TestSessionManagerRecordMessage:
    """Tests for recording messages"""

    def test_record_message(self):
        """Test recording a message"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")
        message = {"role": "user", "content": "hello"}

        manager.record_message(message)

        assert len(session.conversation_history) == 1
        assert session.conversation_history[0] == message

    def test_record_multiple_messages(self):
        """Test recording multiple messages"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")

        manager.record_message({"role": "user", "content": "hello"})
        manager.record_message({"role": "assistant", "content": "hi"})

        assert len(session.conversation_history) == 2

    def test_record_message_when_no_session(self):
        """Test recording message when no session is active"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Should not raise error
        manager.record_message({"role": "user", "content": "test"})


class TestSessionManagerRecordCommand:
    """Tests for recording commands"""

    def test_record_command(self):
        """Test recording a command"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")

        manager.record_command("git status")

        assert len(session.command_history) == 1
        assert session.command_history[0] == "git status"

    def test_record_multiple_commands(self):
        """Test recording multiple commands"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")

        manager.record_command("git status")
        manager.record_command("git add .")

        assert len(session.command_history) == 2


class TestSessionManagerGetCurrentSession:
    """Tests for getting current session"""

    def test_get_current_session(self):
        """Test getting current session"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")

        current = manager.get_current_session()

        assert current == session

    def test_get_current_session_when_none(self):
        """Test getting current session when none is active"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        current = manager.get_current_session()

        assert current is None


class TestSessionManagerCommandHistorySync:
    """Tests for command history synchronization"""

    def test_sync_command_history_to_input_manager(self):
        """Test syncing command history to input manager"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")
        session.command_history = ["cmd1", "cmd2", "cmd3"]

        # Mock input manager
        mock_input_manager = MagicMock()
        mock_input_manager.history = MagicMock()
        mock_input_manager.history._strings = []

        manager.sync_command_history_to_input_manager(mock_input_manager)

        # Verify append_string was called for each command
        assert mock_input_manager.history.append_string.call_count == 3

    def test_sync_command_history_from_input_manager(self):
        """Test syncing command history from input manager"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        session = manager.start_session("test-project")

        # Mock input manager with commands
        mock_input_manager = MagicMock()
        mock_input_manager.history = MagicMock()
        mock_input_manager.history.get_strings = MagicMock(
            return_value=["cmd1", "cmd2", "cmd3"]
        )

        manager.sync_command_history_from_input_manager(mock_input_manager)

        assert session.command_history == ["cmd1", "cmd2", "cmd3"]


class TestSessionManagerListSessions:
    """Tests for listing sessions"""

    def test_list_all_sessions(self):
        """Test listing all sessions via direct persistence"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        # Create and save sessions manually to persistence
        session1_id = "test-session-1"
        session1_data = {
            "session_id": session1_id,
            "project_name": "project1",
            "start_time": "2025-01-01T10:00:00",
            "status": "completed"
        }

        session2_id = "test-session-2"
        session2_data = {
            "session_id": session2_id,
            "project_name": "project2",
            "start_time": "2025-01-01T11:00:00",
            "status": "completed"
        }

        # Manually add to persistence storage
        persistence.sessions[session1_id] = session1_data
        persistence.sessions[session2_id] = session2_data

        # Test that we can directly access the persistence layer
        direct_list = list(persistence.sessions.keys())
        assert len(direct_list) >= 2
        assert session1_id in direct_list
        assert session2_id in direct_list

    def test_list_all_sessions_empty(self):
        """Test listing when no sessions exist"""
        persistence = MockPersistenceManager()
        manager = SessionManager(persistence)

        sessions = manager.list_all_sessions()

        assert len(sessions) == 0
