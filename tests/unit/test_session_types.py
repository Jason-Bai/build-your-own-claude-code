"""Unit tests for Session data model"""

import pytest
from datetime import datetime
from src.sessions.types import Session
from src.checkpoint.types import ExecutionHistory, StepRecord


class TestSessionCreation:
    """Tests for Session instantiation"""

    def test_session_creation_with_required_fields(self):
        """Test creating a session with required fields"""
        now = datetime.now()
        session = Session(
            session_id="test-1",
            project_name="test-project",
            start_time=now
        )

        assert session.session_id == "test-1"
        assert session.project_name == "test-project"
        assert session.start_time == now
        assert session.status == "active"
        assert session.end_time is None
        assert session.conversation_history == []
        assert session.command_history == []
        assert session.execution_histories == []
        assert session.metadata == {}

    def test_session_creation_with_all_fields(self):
        """Test creating a session with all fields"""
        now = datetime.now()
        end = datetime.now()
        conv_history = [{"role": "user", "content": "hello"}]
        cmd_history = ["git status"]
        metadata = {"key": "value"}

        session = Session(
            session_id="test-2",
            project_name="test-project",
            start_time=now,
            status="completed",
            end_time=end,
            conversation_history=conv_history,
            command_history=cmd_history,
            metadata=metadata
        )

        assert session.status == "completed"
        assert session.end_time == end
        assert session.conversation_history == conv_history
        assert session.command_history == cmd_history
        assert session.metadata == metadata


class TestSessionState:
    """Tests for session state management"""

    def test_is_active(self):
        """Test is_active() method"""
        session = Session(
            session_id="test",
            project_name="test",
            start_time=datetime.now(),
            status="active"
        )
        assert session.is_active() is True
        assert session.is_completed() is False
        assert session.is_paused() is False

    def test_is_completed(self):
        """Test is_completed() method"""
        session = Session(
            session_id="test",
            project_name="test",
            start_time=datetime.now(),
            status="completed"
        )
        assert session.is_completed() is True
        assert session.is_active() is False

    def test_is_paused(self):
        """Test is_paused() method"""
        session = Session(
            session_id="test",
            project_name="test",
            start_time=datetime.now(),
            status="paused"
        )
        assert session.is_paused() is True
        assert session.is_active() is False


class TestSessionSerialization:
    """Tests for Session to_dict() and from_dict()"""

    def test_session_to_dict_basic(self):
        """Test basic serialization"""
        now = datetime.now()
        session = Session(
            session_id="test-1",
            project_name="test-project",
            start_time=now
        )

        data = session.to_dict()

        assert data["session_id"] == "test-1"
        assert data["project_name"] == "test-project"
        assert data["start_time"] == now.isoformat()
        assert data["status"] == "active"
        assert data["end_time"] is None
        assert data["conversation_history"] == []
        assert data["command_history"] == []
        assert data["execution_histories"] == []
        assert data["metadata"] == {}

    def test_session_to_dict_with_conversation(self):
        """Test serialization with conversation history"""
        session = Session(
            session_id="test-2",
            project_name="test",
            start_time=datetime.now(),
            conversation_history=[
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"}
            ]
        )

        data = session.to_dict()
        assert len(data["conversation_history"]) == 2
        assert data["conversation_history"][0]["role"] == "user"

    def test_session_to_dict_with_commands(self):
        """Test serialization with command history"""
        session = Session(
            session_id="test-3",
            project_name="test",
            start_time=datetime.now(),
            command_history=["git status", "git add ."]
        )

        data = session.to_dict()
        assert len(data["command_history"]) == 2
        assert "git status" in data["command_history"]

    def test_session_from_dict_basic(self):
        """Test basic deserialization"""
        now = datetime.now()
        data = {
            "session_id": "test-1",
            "project_name": "test-project",
            "start_time": now.isoformat(),
            "status": "active",
            "end_time": None,
            "conversation_history": [],
            "command_history": [],
            "execution_histories": [],
            "metadata": {}
        }

        session = Session.from_dict(data)

        assert session.session_id == "test-1"
        assert session.project_name == "test-project"
        assert session.start_time == now
        assert session.status == "active"
        assert session.end_time is None

    def test_session_roundtrip_serialization(self):
        """Test serialization and deserialization roundtrip"""
        original = Session(
            session_id="test-roundtrip",
            project_name="test",
            start_time=datetime.now(),
            status="active",
            conversation_history=[
                {"role": "user", "content": "test"}
            ],
            command_history=["cmd1", "cmd2"],
            metadata={"key": "value"}
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = Session.from_dict(data)

        # Verify
        assert restored.session_id == original.session_id
        assert restored.project_name == original.project_name
        assert restored.status == original.status
        assert len(restored.conversation_history) == len(original.conversation_history)
        assert restored.command_history == original.command_history
        assert restored.metadata == original.metadata

    def test_session_from_dict_with_execution_histories(self):
        """Test deserialization with execution histories"""
        now = datetime.now()
        execution_data = {
            "execution_id": "exec-001",
            "start_time": now.isoformat(),
            "end_time": now.isoformat(),
            "steps": [],
            "checkpoints": [],
            "total_duration": 1.5,
            "status": "completed",
            "recovery_attempts": 0,
            "last_checkpoint": None
        }

        data = {
            "session_id": "test-exec",
            "project_name": "test",
            "start_time": now.isoformat(),
            "status": "active",
            "end_time": None,
            "conversation_history": [],
            "command_history": [],
            "execution_histories": [execution_data],
            "metadata": {}
        }

        session = Session.from_dict(data)

        assert len(session.execution_histories) == 1
        assert session.execution_histories[0].execution_id == "exec-001"
        assert session.execution_histories[0].status == "completed"


class TestSessionWithExecutionHistory:
    """Tests for Session with ExecutionHistory"""

    def test_session_with_execution_history_serialization(self):
        """Test full serialization roundtrip with execution history"""
        now = datetime.now()

        # Create execution history
        step = StepRecord(
            execution_id="exec-001",
            step_name="test-step",
            step_index=0,
            status="completed",
            timestamp=now,
            result="test result"
        )

        execution = ExecutionHistory(
            execution_id="exec-001",
            start_time=now,
            steps=[step]
        )

        # Create session with execution history
        session = Session(
            session_id="test-exec-full",
            project_name="test",
            start_time=now,
            execution_histories=[execution]
        )

        # Serialize and deserialize
        data = session.to_dict()
        restored = Session.from_dict(data)

        # Verify
        assert len(restored.execution_histories) == 1
        assert restored.execution_histories[0].execution_id == "exec-001"
        assert len(restored.execution_histories[0].steps) == 1
        assert restored.execution_histories[0].steps[0].step_name == "test-step"
