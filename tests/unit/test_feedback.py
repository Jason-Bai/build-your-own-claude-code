"""
Unit tests for Agent Feedback System

Tests feedback levels, message collection, and feedback formatting.
"""

import pytest
from src.agents.feedback import AgentFeedback, FeedbackLevel


@pytest.mark.unit
class TestFeedbackLevel:
    """Tests for FeedbackLevel enum"""

    def test_feedback_level_values(self):
        """Test FeedbackLevel enum values"""
        assert FeedbackLevel.SILENT.value == 0
        assert FeedbackLevel.MINIMAL.value == 1
        assert FeedbackLevel.VERBOSE.value == 2

    def test_feedback_level_ordering(self):
        """Test FeedbackLevel ordering"""
        assert FeedbackLevel.SILENT.value < FeedbackLevel.MINIMAL.value
        assert FeedbackLevel.MINIMAL.value < FeedbackLevel.VERBOSE.value

    def test_feedback_level_comparison(self):
        """Test FeedbackLevel comparison"""
        assert FeedbackLevel.SILENT.value < 1
        assert FeedbackLevel.MINIMAL.value == 1
        assert FeedbackLevel.VERBOSE.value > 1


@pytest.mark.unit
class TestAgentFeedbackInitialization:
    """Tests for AgentFeedback initialization"""

    def test_initialization_with_default_level(self):
        """Test initialization with default level"""
        feedback = AgentFeedback()
        assert feedback.level == FeedbackLevel.MINIMAL
        assert feedback.messages == []

    def test_initialization_with_silent_level(self):
        """Test initialization with SILENT level"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        assert feedback.level == FeedbackLevel.SILENT

    def test_initialization_with_minimal_level(self):
        """Test initialization with MINIMAL level"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        assert feedback.level == FeedbackLevel.MINIMAL

    def test_initialization_with_verbose_level(self):
        """Test initialization with VERBOSE level"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        assert feedback.level == FeedbackLevel.VERBOSE


@pytest.mark.unit
class TestAgentFeedbackToolCall:
    """Tests for tool call feedback"""

    def test_add_tool_call_minimal(self):
        """Test adding tool call in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("bash", "execute: ls -la")
        assert len(feedback.messages) == 1
        assert "Using bash" in feedback.messages[0]
        assert "execute: ls -la" in feedback.messages[0]

    def test_add_tool_call_verbose(self):
        """Test adding tool call in VERBOSE mode"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_tool_call("grep", "search for pattern")
        assert len(feedback.messages) == 1
        assert "Using grep" in feedback.messages[0]

    def test_add_tool_call_silent(self):
        """Test adding tool call in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_tool_call("read", "open file")
        assert len(feedback.messages) == 0

    def test_add_multiple_tool_calls(self):
        """Test adding multiple tool calls"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("bash", "execute: pwd")
        feedback.add_tool_call("read", "read: /etc/hosts")
        assert len(feedback.messages) == 2

    def test_tool_call_formatting(self):
        """Test tool call message formatting"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("write", "create file")
        msg = feedback.messages[0]
        assert msg.startswith("🔧")
        assert "write" in msg
        assert "create file" in msg


@pytest.mark.unit
class TestAgentFeedbackToolCompleted:
    """Tests for tool completed feedback"""

    def test_add_tool_completed_minimal(self):
        """Test adding tool completed in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_completed("bash")
        assert len(feedback.messages) == 1
        assert "bash completed" in feedback.messages[0]

    def test_add_tool_completed_verbose(self):
        """Test adding tool completed in VERBOSE mode"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_tool_completed("grep")
        assert len(feedback.messages) == 1

    def test_add_tool_completed_silent(self):
        """Test adding tool completed in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_tool_completed("read")
        assert len(feedback.messages) == 0

    def test_tool_completed_formatting(self):
        """Test tool completed message formatting"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_completed("write")
        msg = feedback.messages[0]
        assert msg.startswith("✓")


@pytest.mark.unit
class TestAgentFeedbackStatus:
    """Tests for status feedback"""

    def test_add_status_minimal(self):
        """Test adding status in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Processing files")
        assert len(feedback.messages) == 1
        assert "Processing files" in feedback.messages[0]

    def test_add_status_verbose(self):
        """Test adding status in VERBOSE mode"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_status("Analyzing results")
        assert len(feedback.messages) == 1

    def test_add_status_silent(self):
        """Test adding status in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_status("Waiting")
        assert len(feedback.messages) == 0

    def test_status_formatting(self):
        """Test status message formatting"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Validating input")
        msg = feedback.messages[0]
        assert msg.startswith("ℹ️")
        assert "Validating input" in msg

    def test_add_multiple_statuses(self):
        """Test adding multiple statuses"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Starting")
        feedback.add_status("In progress")
        feedback.add_status("Complete")
        assert len(feedback.messages) == 3


@pytest.mark.unit
class TestAgentFeedbackError:
    """Tests for error feedback"""

    def test_add_error_minimal(self):
        """Test adding error in MINIMAL mode (always shown)"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_error("Tool failed")
        assert len(feedback.messages) == 1

    def test_add_error_silent(self):
        """Test adding error in SILENT mode (always shown)"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_error("Critical error")
        assert len(feedback.messages) == 1

    def test_add_error_verbose(self):
        """Test adding error in VERBOSE mode (always shown)"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_error("Error occurred")
        assert len(feedback.messages) == 1

    def test_error_formatting(self):
        """Test error message formatting"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_error("Connection refused")
        msg = feedback.messages[0]
        assert msg.startswith("❌")
        assert "Connection refused" in msg

    def test_error_override_silent_mode(self):
        """Test that errors are shown even in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_status("This should not show")
        feedback.add_error("This should show")
        # Only the error should be shown
        assert len(feedback.messages) == 1


@pytest.mark.unit
class TestAgentFeedbackThinking:
    """Tests for thinking feedback"""

    def test_add_thinking_minimal(self):
        """Test adding thinking in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()
        assert len(feedback.messages) == 1
        assert "Thinking" in feedback.messages[0]

    def test_add_thinking_verbose(self):
        """Test adding thinking in VERBOSE mode"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_thinking()
        assert len(feedback.messages) == 1

    def test_add_thinking_silent(self):
        """Test adding thinking in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_thinking()
        assert len(feedback.messages) == 0

    def test_thinking_formatting(self):
        """Test thinking message formatting"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()
        msg = feedback.messages[0]
        assert msg.startswith("💭")
        assert "Thinking" in msg


@pytest.mark.unit
class TestAgentFeedbackRetrieval:
    """Tests for feedback retrieval"""

    def test_get_all_empty(self):
        """Test getting all messages when empty"""
        feedback = AgentFeedback()
        messages = feedback.get_all()
        assert messages == []

    def test_get_all_single_message(self):
        """Test getting all messages with single message"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("bash", "ls")
        messages = feedback.get_all()
        assert len(messages) == 1

    def test_get_all_multiple_messages(self):
        """Test getting all messages with multiple messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()
        feedback.add_tool_call("bash", "pwd")
        feedback.add_tool_completed("bash")
        messages = feedback.get_all()
        assert len(messages) == 3

    def test_get_all_returns_copy(self):
        """Test that get_all returns messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("read", "file.txt")
        messages = feedback.get_all()
        assert len(messages) == 1
        assert "read" in messages[0]


@pytest.mark.unit
class TestAgentFeedbackClear:
    """Tests for clearing feedback"""

    def test_clear_empty_feedback(self):
        """Test clearing empty feedback"""
        feedback = AgentFeedback()
        feedback.clear()
        assert feedback.messages == []

    def test_clear_with_messages(self):
        """Test clearing feedback with messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("bash", "ls")
        feedback.add_status("Done")
        assert len(feedback.messages) == 2
        feedback.clear()
        assert len(feedback.messages) == 0

    def test_clear_allows_new_messages(self):
        """Test that clearing allows new messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("bash", "ls")
        feedback.clear()
        feedback.add_status("New message")
        assert len(feedback.messages) == 1
        assert "New message" in feedback.messages[0]


@pytest.mark.unit
class TestAgentFeedbackHasMessages:
    """Tests for has_messages check"""

    def test_has_messages_empty(self):
        """Test has_messages when empty"""
        feedback = AgentFeedback()
        assert feedback.has_messages() is False

    def test_has_messages_with_single(self):
        """Test has_messages with single message"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("read", "file")
        assert feedback.has_messages() is True

    def test_has_messages_after_clear(self):
        """Test has_messages after clearing"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Status")
        feedback.clear()
        assert feedback.has_messages() is False

    def test_has_messages_silent_mode_empty(self):
        """Test has_messages in SILENT mode when no errors"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_status("Won't show")
        assert feedback.has_messages() is False

    def test_has_messages_silent_mode_with_error(self):
        """Test has_messages in SILENT mode with error"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_error("Error occurred")
        assert feedback.has_messages() is True


@pytest.mark.unit
class TestAgentFeedbackLevelInteraction:
    """Tests for feedback level interactions"""

    def test_mixed_feedback_minimal(self):
        """Test mixed feedback in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()
        feedback.add_tool_call("bash", "ls")
        feedback.add_tool_completed("bash")
        feedback.add_status("Done")
        assert len(feedback.messages) == 4

    def test_mixed_feedback_verbose(self):
        """Test mixed feedback in VERBOSE mode"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)
        feedback.add_thinking()
        feedback.add_tool_call("grep", "search")
        feedback.add_tool_completed("grep")
        feedback.add_status("Analyzing")
        assert len(feedback.messages) == 4

    def test_mixed_feedback_with_error_minimal(self):
        """Test mixed feedback with error in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_thinking()
        feedback.add_tool_call("bash", "failing command")
        feedback.add_error("Tool failed")
        # All messages should be present
        assert len(feedback.messages) == 3

    def test_level_change_effect(self):
        """Test that level affects what gets recorded"""
        feedback_silent = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback_minimal = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback_silent.add_status("Silent status")
        feedback_minimal.add_status("Minimal status")

        assert len(feedback_silent.messages) == 0
        assert len(feedback_minimal.messages) == 1


@pytest.mark.unit
class TestAgentFeedbackEdgeCases:
    """Tests for edge cases"""

    def test_empty_tool_name(self):
        """Test with empty tool name"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("", "description")
        assert len(feedback.messages) == 1

    def test_empty_description(self):
        """Test with empty description"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("bash", "")
        assert len(feedback.messages) == 1
        assert "bash" in feedback.messages[0]

    def test_long_messages(self):
        """Test with very long messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        long_desc = "x" * 1000
        feedback.add_tool_call("bash", long_desc)
        assert len(feedback.messages) == 1
        assert long_desc in feedback.messages[0]

    def test_special_characters_in_messages(self):
        """Test with special characters"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Processing: file@#$%.txt")
        feedback.add_error("Error: 404 Not Found!")
        assert len(feedback.messages) == 2

    def test_unicode_in_messages(self):
        """Test with unicode characters"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("处理中文 🚀")
        feedback.add_tool_call("bash", "执行命令")
        assert len(feedback.messages) == 2


@pytest.mark.unit
class TestAgentFeedbackIntegration:
    """Integration tests for feedback system"""

    def test_typical_workflow_minimal(self):
        """Test typical workflow in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_thinking()
        feedback.add_status("Starting analysis")
        feedback.add_tool_call("bash", "find files")
        feedback.add_tool_completed("bash")
        feedback.add_status("Analysis complete")

        messages = feedback.get_all()
        assert len(messages) == 5
        assert feedback.has_messages() is True

    def test_typical_workflow_with_error(self):
        """Test workflow with error handling"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_thinking()
        feedback.add_tool_call("bash", "failing command")
        feedback.add_error("Command timed out")
        feedback.add_status("Retrying")
        feedback.add_tool_call("bash", "retry command")
        feedback.add_tool_completed("bash")

        messages = feedback.get_all()
        assert len(messages) == 6
        # Verify error is in messages
        error_msg = [m for m in messages if "timed out" in m]
        assert len(error_msg) == 1

    def test_silent_mode_only_shows_errors(self):
        """Test that SILENT mode only shows errors"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        feedback.add_thinking()
        feedback.add_status("Starting")
        feedback.add_tool_call("bash", "ls")
        feedback.add_tool_completed("bash")
        feedback.add_error("Something went wrong")
        feedback.add_status("Recovering")

        messages = feedback.get_all()
        # Only error should be shown
        assert len(messages) == 1
        assert "Something went wrong" in messages[0]
