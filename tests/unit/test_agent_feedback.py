"""
Unit tests for Agent Feedback System

Tests feedback collection, levels, and message formatting.
"""

import pytest
from src.agents.feedback import AgentFeedback, FeedbackLevel


@pytest.mark.unit
class TestFeedbackLevel:
    """Tests for FeedbackLevel enum"""

    def test_feedback_level_values(self):
        """Test feedback level values"""
        assert FeedbackLevel.SILENT.value == 0
        assert FeedbackLevel.MINIMAL.value == 1
        assert FeedbackLevel.VERBOSE.value == 2

    def test_feedback_level_ordering(self):
        """Test that feedback levels are properly ordered"""
        assert FeedbackLevel.SILENT.value < FeedbackLevel.MINIMAL.value
        assert FeedbackLevel.MINIMAL.value < FeedbackLevel.VERBOSE.value


@pytest.mark.unit
class TestAgentFeedbackInitialization:
    """Tests for AgentFeedback initialization"""

    def test_feedback_initialization_default(self):
        """Test feedback initialization with default level"""
        feedback = AgentFeedback()

        assert feedback.level == FeedbackLevel.MINIMAL
        assert feedback.messages == []

    def test_feedback_initialization_silent(self):
        """Test feedback initialization with SILENT level"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        assert feedback.level == FeedbackLevel.SILENT
        assert feedback.messages == []

    def test_feedback_initialization_verbose(self):
        """Test feedback initialization with VERBOSE level"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)

        assert feedback.level == FeedbackLevel.VERBOSE
        assert feedback.messages == []


@pytest.mark.unit
class TestAgentFeedbackToolCalls:
    """Tests for tool call feedback"""

    def test_add_tool_call_minimal(self):
        """Test adding tool call at MINIMAL level"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("bash", "execute: ls -R")

        assert len(feedback.messages) == 1
        assert "🔧 Using bash: execute: ls -R" in feedback.messages[0]

    def test_add_tool_call_verbose(self):
        """Test adding tool call at VERBOSE level"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_tool_call("read", "read: /path/to/file")

        assert len(feedback.messages) == 1
        assert "🔧 Using read: read: /path/to/file" in feedback.messages[0]

    def test_add_tool_call_silent_suppressed(self):
        """Test that tool calls are suppressed at SILENT level"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_tool_call("bash", "execute: ls")

        assert len(feedback.messages) == 0

    def test_add_multiple_tool_calls(self):
        """Test adding multiple tool calls"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_call("read", "read: file1.txt")
        feedback.add_tool_call("write", "write: file2.txt")
        feedback.add_tool_call("bash", "execute: ls")

        assert len(feedback.messages) == 3


@pytest.mark.unit
class TestAgentFeedbackToolCompleted:
    """Tests for tool completion feedback"""

    def test_add_tool_completed_minimal(self):
        """Test adding tool completed at MINIMAL level"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_completed("bash")

        assert len(feedback.messages) == 1
        assert "✓ bash completed" in feedback.messages[0]

    def test_add_tool_completed_verbose(self):
        """Test adding tool completed at VERBOSE level"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_tool_completed("read")

        assert len(feedback.messages) == 1
        assert "✓ read completed" in feedback.messages[0]

    def test_add_tool_completed_silent_suppressed(self):
        """Test that tool completed is suppressed at SILENT level"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_tool_completed("bash")

        assert len(feedback.messages) == 0

    def test_add_multiple_tool_completed(self):
        """Test adding multiple tool completed messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_completed("read")
        feedback.add_tool_completed("write")
        feedback.add_tool_completed("bash")

        assert len(feedback.messages) == 3


@pytest.mark.unit
class TestAgentFeedbackStatus:
    """Tests for status feedback"""

    def test_add_status_minimal(self):
        """Test adding status at MINIMAL level"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Processing results...")

        assert len(feedback.messages) == 1
        assert "ℹ️  Processing results..." in feedback.messages[0]

    def test_add_status_verbose(self):
        """Test adding status at VERBOSE level"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_status("Initializing...")

        assert len(feedback.messages) == 1
        assert "ℹ️  Initializing..." in feedback.messages[0]

    def test_add_status_silent_suppressed(self):
        """Test that status is suppressed at SILENT level"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_status("Some status")

        assert len(feedback.messages) == 0

    def test_add_multiple_statuses(self):
        """Test adding multiple statuses"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_status("Starting...")
        feedback.add_status("Processing...")
        feedback.add_status("Completing...")

        assert len(feedback.messages) == 3


@pytest.mark.unit
class TestAgentFeedbackErrors:
    """Tests for error feedback"""

    def test_add_error_minimal(self):
        """Test adding error at MINIMAL level"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_error("Tool execution failed")

        assert len(feedback.messages) == 1
        assert "❌ Tool execution failed" in feedback.messages[0]

    def test_add_error_verbose(self):
        """Test adding error at VERBOSE level"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_error("Permission denied")

        assert len(feedback.messages) == 1
        assert "❌ Permission denied" in feedback.messages[0]

    def test_add_error_silent_not_suppressed(self):
        """Test that errors are NOT suppressed at SILENT level"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_error("Critical error")

        # Errors should always be shown, even at SILENT level
        assert len(feedback.messages) == 1
        assert "❌ Critical error" in feedback.messages[0]

    def test_add_multiple_errors(self):
        """Test adding multiple errors"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_error("Error 1")
        feedback.add_error("Error 2")
        feedback.add_error("Error 3")

        assert len(feedback.messages) == 3


@pytest.mark.unit
class TestAgentFeedbackThinking:
    """Tests for thinking feedback"""

    def test_add_thinking_minimal(self):
        """Test adding thinking at MINIMAL level"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()

        assert len(feedback.messages) == 1
        assert "💭 Thinking..." in feedback.messages[0]

    def test_add_thinking_verbose(self):
        """Test adding thinking at VERBOSE level"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_thinking()

        assert len(feedback.messages) == 1
        assert "💭 Thinking..." in feedback.messages[0]

    def test_add_thinking_silent_suppressed(self):
        """Test that thinking is suppressed at SILENT level"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_thinking()

        assert len(feedback.messages) == 0

    def test_add_multiple_thinking(self):
        """Test adding multiple thinking messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_thinking()
        feedback.add_thinking()
        feedback.add_thinking()

        assert len(feedback.messages) == 3


@pytest.mark.unit
class TestAgentFeedbackRetrieval:
    """Tests for retrieving feedback messages"""

    def test_get_all_empty(self):
        """Test getting all messages when empty"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        assert feedback.get_all() == []

    def test_get_all_with_messages(self):
        """Test getting all messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()
        feedback.add_tool_call("bash", "execute: ls")
        feedback.add_tool_completed("bash")

        all_messages = feedback.get_all()
        assert len(all_messages) == 3

    def test_has_messages_false(self):
        """Test has_messages when empty"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        assert feedback.has_messages() is False

    def test_has_messages_true(self):
        """Test has_messages when not empty"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()

        assert feedback.has_messages() is True


@pytest.mark.unit
class TestAgentFeedbackClearing:
    """Tests for clearing feedback messages"""

    def test_clear_empty(self):
        """Test clearing when already empty"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.clear()

        assert len(feedback.messages) == 0
        assert feedback.has_messages() is False

    def test_clear_with_messages(self):
        """Test clearing messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()
        feedback.add_tool_call("bash", "test")

        assert feedback.has_messages() is True

        feedback.clear()

        assert len(feedback.messages) == 0
        assert feedback.has_messages() is False

    def test_add_after_clear(self):
        """Test adding messages after clearing"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()
        feedback.clear()
        feedback.add_tool_call("read", "test")

        assert len(feedback.messages) == 1


@pytest.mark.unit
class TestAgentFeedbackIntegration:
    """Integration tests for feedback system"""

    def test_realistic_workflow_minimal(self):
        """Test realistic workflow at MINIMAL level"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_thinking()
        feedback.add_tool_call("read", "read: /path/file.txt")
        feedback.add_tool_completed("read")
        feedback.add_tool_call("bash", "execute: grep pattern /path/file.txt")
        feedback.add_tool_completed("bash")
        feedback.add_status("Analysis complete")

        messages = feedback.get_all()
        assert len(messages) == 6
        assert any("Thinking" in msg for msg in messages)
        assert any("read" in msg for msg in messages)
        assert any("bash" in msg for msg in messages)

    def test_realistic_workflow_with_error(self):
        """Test workflow with error"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_thinking()
        feedback.add_tool_call("read", "read: /nonexistent/file.txt")
        feedback.add_error("File not found: /nonexistent/file.txt")
        feedback.add_status("Retrying with alternative path...")

        messages = feedback.get_all()
        assert any("Thinking" in msg for msg in messages)
        assert any("❌" in msg for msg in messages)
        assert any("Retrying" in msg for msg in messages)

    def test_silent_mode_suppresses_most_messages(self):
        """Test that SILENT mode suppresses most messages except errors"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        feedback.add_thinking()
        feedback.add_tool_call("bash", "ls")
        feedback.add_tool_completed("bash")
        feedback.add_status("Done")
        feedback.add_error("Error occurred")

        messages = feedback.get_all()
        # Only error should be present
        assert len(messages) == 1
        assert "❌ Error occurred" in messages[0]

    def test_verbose_mode_includes_everything(self):
        """Test that VERBOSE mode includes all messages"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)

        feedback.add_thinking()
        feedback.add_tool_call("bash", "ls")
        feedback.add_tool_completed("bash")
        feedback.add_status("Done")
        feedback.add_error("Error")

        messages = feedback.get_all()
        assert len(messages) == 5
        assert all(len(msg) > 0 for msg in messages)

    def test_message_format_consistency(self):
        """Test that messages have consistent emoji format"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)

        feedback.add_thinking()
        feedback.add_tool_call("bash", "test")
        feedback.add_tool_completed("bash")
        feedback.add_status("Status")
        feedback.add_error("Error")

        messages = feedback.get_all()

        # Check emoji presence
        assert "💭" in messages[0]  # Thinking
        assert "🔧" in messages[1]  # Tool call
        assert "✓" in messages[2]   # Completed
        assert "ℹ️" in messages[3]  # Status
        assert "❌" in messages[4]  # Error
