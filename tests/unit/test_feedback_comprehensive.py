"""
Unit tests for Agent Feedback System

Tests feedback levels, message collection, and feedback lifecycle.
"""

import pytest
from src.agents.feedback import FeedbackLevel, AgentFeedback


@pytest.mark.unit
class TestFeedbackLevel:
    """Tests for FeedbackLevel enum"""

    def test_feedback_level_silent(self):
        """Test SILENT level"""
        assert FeedbackLevel.SILENT.value == 0

    def test_feedback_level_minimal(self):
        """Test MINIMAL level"""
        assert FeedbackLevel.MINIMAL.value == 1

    def test_feedback_level_verbose(self):
        """Test VERBOSE level"""
        assert FeedbackLevel.VERBOSE.value == 2

    def test_feedback_level_ordering(self):
        """Test feedback levels ordered by value"""
        assert FeedbackLevel.SILENT.value < FeedbackLevel.MINIMAL.value
        assert FeedbackLevel.MINIMAL.value < FeedbackLevel.VERBOSE.value

    def test_feedback_level_iteration(self):
        """Test can iterate over feedback levels"""
        levels = list(FeedbackLevel)
        assert len(levels) == 3


@pytest.mark.unit
class TestAgentFeedbackInitialization:
    """Tests for AgentFeedback initialization"""

    def test_initialization_default_level(self):
        """Test initialization with default level"""
        feedback = AgentFeedback()

        assert feedback.level == FeedbackLevel.MINIMAL
        assert isinstance(feedback.messages, list)
        assert len(feedback.messages) == 0

    def test_initialization_silent_level(self):
        """Test initialization with SILENT level"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        assert feedback.level == FeedbackLevel.SILENT

    def test_initialization_verbose_level(self):
        """Test initialization with VERBOSE level"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)

        assert feedback.level == FeedbackLevel.VERBOSE


@pytest.mark.unit
class TestToolCallFeedback:
    """Tests for tool call feedback"""

    def test_add_tool_call_verbose(self):
        """Test adding tool call in VERBOSE mode"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)

        feedback.add_tool_call("bash", "ls -la")

        assert len(feedback.messages) == 1
        assert "bash" in feedback.messages[0]
        assert "ls -la" in feedback.messages[0]

    def test_add_tool_call_minimal(self):
        """Test adding tool call in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_call("read", "/etc/hosts")

        assert len(feedback.messages) == 1

    def test_add_tool_call_silent(self):
        """Test adding tool call in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        feedback.add_tool_call("bash", "pwd")

        # Should not add message in SILENT mode
        assert len(feedback.messages) == 0

    def test_tool_call_format(self):
        """Test tool call message format"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_call("grep", "pattern in file")

        msg = feedback.messages[0]
        assert msg.startswith("🔧")
        assert "grep" in msg


@pytest.mark.unit
class TestToolCompleted:
    """Tests for tool completion feedback"""

    def test_add_tool_completed_minimal(self):
        """Test adding tool completed in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_completed("bash")

        assert len(feedback.messages) == 1
        assert "bash" in feedback.messages[0]
        assert "completed" in feedback.messages[0]

    def test_add_tool_completed_silent(self):
        """Test adding tool completed in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        feedback.add_tool_completed("read")

        assert len(feedback.messages) == 0

    def test_tool_completed_format(self):
        """Test tool completed message format"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_completed("write")

        msg = feedback.messages[0]
        assert msg.startswith("✓")
        assert "write" in msg


@pytest.mark.unit
class TestStatusFeedback:
    """Tests for status feedback"""

    def test_add_status_minimal(self):
        """Test adding status in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_status("Processing...")

        assert len(feedback.messages) == 1
        assert "Processing..." in feedback.messages[0]

    def test_add_status_verbose(self):
        """Test adding status in VERBOSE mode"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)

        feedback.add_status("Analyzing results")

        assert len(feedback.messages) == 1

    def test_add_status_silent(self):
        """Test adding status in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        feedback.add_status("Status update")

        assert len(feedback.messages) == 0

    def test_status_format(self):
        """Test status message format"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_status("Thinking...")

        msg = feedback.messages[0]
        assert msg.startswith("ℹ️")
        assert "Thinking..." in msg


@pytest.mark.unit
class TestErrorFeedback:
    """Tests for error feedback"""

    def test_add_error_minimal(self):
        """Test adding error in MINIMAL mode"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_error("Tool failed")

        assert len(feedback.messages) == 1

    def test_add_error_silent(self):
        """Test adding error in SILENT mode - errors always show"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        feedback.add_error("Critical error")

        # Errors should be added even in SILENT mode
        assert len(feedback.messages) == 1

    def test_error_format(self):
        """Test error message format"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_error("Something went wrong")

        msg = feedback.messages[0]
        assert msg.startswith("❌")
        assert "Something went wrong" in msg

    def test_error_always_shows(self):
        """Test errors show regardless of level"""
        for level in [FeedbackLevel.SILENT, FeedbackLevel.MINIMAL, FeedbackLevel.VERBOSE]:
            feedback = AgentFeedback(level=level)
            feedback.add_error("Error")
            assert len(feedback.messages) == 1


@pytest.mark.unit
class TestThinkingFeedback:
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

        # Should not add in SILENT mode
        assert len(feedback.messages) == 0

    def test_thinking_format(self):
        """Test thinking message format"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_thinking()

        msg = feedback.messages[0]
        assert msg.startswith("💭")
        assert "Thinking" in msg


@pytest.mark.unit
class TestMessageCollection:
    """Tests for message collection"""

    def test_get_all_empty(self):
        """Test getting all messages when empty"""
        feedback = AgentFeedback()

        messages = feedback.get_all()

        assert isinstance(messages, list)
        assert len(messages) == 0

    def test_get_all_multiple_messages(self):
        """Test getting all messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_tool_call("bash", "ls")
        feedback.add_status("Processing")
        feedback.add_tool_completed("bash")

        messages = feedback.get_all()

        assert len(messages) == 3

    def test_get_all_includes_errors(self):
        """Test get_all includes errors"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_error("Test error")

        messages = feedback.get_all()

        assert len(messages) == 1

    def test_has_messages_empty(self):
        """Test has_messages when empty"""
        feedback = AgentFeedback()

        assert feedback.has_messages() is False

    def test_has_messages_with_content(self):
        """Test has_messages with content"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Status")

        assert feedback.has_messages() is True

    def test_has_messages_only_errors_silent(self):
        """Test has_messages with only errors in SILENT mode"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)
        feedback.add_error("Error")

        assert feedback.has_messages() is True


@pytest.mark.unit
class TestClear:
    """Tests for clearing feedback"""

    def test_clear_removes_messages(self):
        """Test clearing removes all messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Status")
        feedback.add_tool_call("bash", "cmd")

        feedback.clear()

        assert len(feedback.messages) == 0

    def test_clear_resets_has_messages(self):
        """Test clear resets has_messages"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Status")

        feedback.clear()

        assert feedback.has_messages() is False

    def test_clear_allows_new_messages(self):
        """Test new messages can be added after clear"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback.add_status("Status 1")
        feedback.clear()
        feedback.add_status("Status 2")

        messages = feedback.get_all()
        assert len(messages) == 1
        assert "Status 2" in messages[0]


@pytest.mark.unit
class TestFeedbackWorkflow:
    """Tests for complete feedback workflows"""

    def test_verbose_workflow(self):
        """Test complete verbose workflow"""
        feedback = AgentFeedback(level=FeedbackLevel.VERBOSE)

        feedback.add_thinking()
        feedback.add_tool_call("bash", "ls -la")
        feedback.add_status("Running command")
        feedback.add_tool_completed("bash")

        assert len(feedback.get_all()) == 4

    def test_minimal_workflow(self):
        """Test complete minimal workflow"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_thinking()
        feedback.add_tool_call("read", "file.txt")
        feedback.add_tool_completed("read")

        messages = feedback.get_all()
        assert len(messages) == 3

    def test_silent_with_error_workflow(self):
        """Test SILENT mode with error"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        feedback.add_thinking()  # Should not add
        feedback.add_status("Processing")  # Should not add
        feedback.add_error("Failed")  # Should add

        messages = feedback.get_all()
        assert len(messages) == 1
        assert "Failed" in messages[0]

    def test_multiple_tool_operations(self):
        """Test multiple tool operations"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        for i in range(3):
            feedback.add_tool_call(f"tool_{i}", f"operation_{i}")
            feedback.add_tool_completed(f"tool_{i}")

        messages = feedback.get_all()
        assert len(messages) == 6  # 3 calls + 3 completions


@pytest.mark.unit
class TestFeedbackLevelThresholds:
    """Tests for feedback level thresholds"""

    def test_minimal_threshold(self):
        """Test MINIMAL threshold blocking"""
        feedback_minimal = AgentFeedback(level=FeedbackLevel.MINIMAL)
        feedback_verbose = AgentFeedback(level=FeedbackLevel.VERBOSE)

        feedback_minimal.add_thinking()
        feedback_verbose.add_thinking()

        # Both should have message (MINIMAL >= MINIMAL, VERBOSE >= MINIMAL)
        assert len(feedback_minimal.messages) == 1
        assert len(feedback_verbose.messages) == 1

    def test_silent_threshold(self):
        """Test SILENT threshold"""
        feedback = AgentFeedback(level=FeedbackLevel.SILENT)

        feedback.add_thinking()
        feedback.add_status("Status")
        feedback.add_tool_call("bash", "cmd")

        # All should be blocked except errors
        assert len(feedback.messages) == 0


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    def test_empty_strings(self):
        """Test with empty strings"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_call("", "")
        feedback.add_status("")

        assert len(feedback.messages) == 2

    def test_very_long_description(self):
        """Test with very long description"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)
        long_desc = "x" * 1000

        feedback.add_tool_call("bash", long_desc)

        assert len(feedback.messages) == 1

    def test_special_characters(self):
        """Test with special characters"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_call("bash", "ls | grep '*.txt'")
        feedback.add_status("Status: 100% done!")

        assert len(feedback.messages) == 2

    def test_unicode_in_feedback(self):
        """Test unicode in feedback"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_tool_call("translate", "翻译这个文本")
        feedback.add_status("处理中... 🌍")

        assert len(feedback.messages) == 2

    def test_newlines_in_feedback(self):
        """Test newlines in feedback"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_status("Line 1\nLine 2")

        msg = feedback.get_all()[0]
        assert "\n" in msg

    def test_clear_multiple_times(self):
        """Test clearing multiple times"""
        feedback = AgentFeedback(level=FeedbackLevel.MINIMAL)

        feedback.add_status("Message")
        feedback.clear()
        feedback.clear()
        feedback.clear()

        assert len(feedback.messages) == 0
