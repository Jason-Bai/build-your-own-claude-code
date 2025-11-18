"""
Unit tests for Agent Context Manager

Tests message management, token estimation, context compression, and metadata handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.context_manager import AgentContextManager


@pytest.fixture
def manager():
    """Provides a fresh AgentContextManager instance for each test."""
    return AgentContextManager()


@pytest.mark.unit
class TestContextManagerInitialization:
    """Tests for AgentContextManager initialization."""

    @pytest.mark.parametrize("max_tokens, expected_tokens", [
        (None, 150000),
        (50000, 50000),
        (1000, 1000),
    ])
    def test_initialization(self, max_tokens, expected_tokens):
        """Test AgentContextManager initialization with default and custom max_tokens."""
        if max_tokens is None:
            mgr = AgentContextManager()
        else:
            mgr = AgentContextManager(max_tokens=max_tokens)

        assert mgr.max_tokens == expected_tokens
        assert len(mgr.messages) == 0
        assert mgr.system_prompt == ""
        assert mgr.summary == ""
        assert mgr.metadata == {}


@pytest.mark.unit
class TestContextManagerMessages:
    """Tests for message management."""

    def test_set_system_prompt(self, manager):
        """Test setting system prompt."""
        manager.set_system_prompt("You are a helpful assistant")
        assert manager.system_prompt == "You are a helpful assistant"

    def test_add_user_messages(self, manager):
        """Test adding single and multiple user messages."""
        manager.add_user_message("Hello, assistant")
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"
        assert manager.messages[0].content[0]["text"] == "Hello, assistant"

        manager.add_user_message("Second message")
        assert len(manager.messages) == 2
        assert manager.messages[1].content[0]["text"] == "Second message"

    def test_add_assistant_message(self, manager):
        """Test adding assistant message."""
        content = [{"type": "text", "text": "Response"}]
        manager.add_assistant_message(content)
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "assistant"
        assert manager.messages[0].content == content

    def test_add_tool_results(self, manager):
        """Test adding tool results."""
        tool_results = [
            {"type": "tool_result", "tool_name": "bash", "result": "output"}
        ]
        manager.add_tool_results(tool_results)
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"
        assert manager.messages[0].content == tool_results

    def test_add_tool_results_empty_list(self, manager):
        """Test adding empty tool results does nothing."""
        manager.add_tool_results([])
        assert len(manager.messages) == 0

    def test_get_messages(self, manager):
        """Test getting messages as dicts."""
        manager.add_user_message("Test")
        messages = manager.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_get_last_message(self, manager):
        """Test getting the last message."""
        manager.add_user_message("First")
        manager.add_user_message("Second")
        last = manager.get_last_message()
        assert last.role == "user"
        assert last.content[0]['text'] == "Second"

    def test_get_last_message_empty(self, manager):
        """Test getting last message when context is empty."""
        last = manager.get_last_message()
        assert last is None


@pytest.mark.unit
class TestContextManagerTokenEstimation:
    """Tests for token estimation."""

    def test_estimate_tokens_empty_context(self, manager):
        """Test token estimation for an empty context."""
        assert manager.estimate_tokens() == 0

    def test_estimate_tokens_with_content(self, manager):
        """Test token estimation with various content."""
        manager.set_system_prompt("You are helpful" * 10)
        manager.summary = "Previous conversation summary" * 10
        manager.add_user_message("Test message" * 10)
        
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_token_estimation_formula(self, manager):
        """Test token estimation formula (1 token ≈ 3 chars)."""
        manager.set_system_prompt("a" * 300)  # 300 chars = ~100 tokens
        assert manager.estimate_tokens() == 100


@pytest.mark.unit
class TestContextManagerMetadata:
    """Tests for metadata management."""

    def test_set_and_get_metadata(self, manager):
        """Test setting and getting metadata."""
        manager.set_metadata("key1", "value1")
        manager.set_metadata("key2", [1, 2])
        
        assert manager.get_metadata("key1") == "value1"
        assert manager.get_metadata("key2") == [1, 2]

    def test_get_metadata_with_default(self, manager):
        """Test getting metadata with a default value."""
        assert manager.get_metadata("nonexistent", "default") == "default"


@pytest.mark.unit
class TestContextManagerClear:
    """Tests for clearing context."""

    def test_clear(self, manager):
        """Test that clear resets messages, summary, and metadata."""
        manager.set_system_prompt("System")
        manager.add_user_message("Message")
        manager.summary = "Summary"
        manager.set_metadata("key", "value")

        manager.clear()

        assert len(manager.messages) == 0
        assert manager.summary == ""
        assert len(manager.metadata) == 0
        # System prompt should not be cleared
        assert manager.system_prompt == "System"


@pytest.mark.unit
class TestContextManagerInfo:
    """Tests for context info."""

    def test_get_context_info_empty(self, manager):
        """Test context info for an empty manager."""
        info = manager.get_context_info()
        assert info["message_count"] == 0
        assert info["estimated_tokens"] == 0
        assert info["max_tokens"] == 150000
        assert info["usage_percentage"] == 0
        assert not info["has_summary"]
        assert info["summary_length"] == 0

    def test_get_context_info_with_content(self, manager):
        """Test context info with messages and summary."""
        manager.add_user_message("Test")
        manager.summary = "Summary text"
        info = manager.get_context_info()
        assert info["message_count"] == 1
        assert info["has_summary"]
        assert info["summary_length"] == 12

    def test_get_context_info_usage_percentage(self):
        """Test context info usage percentage calculation."""
        manager = AgentContextManager(max_tokens=1000)
        manager.set_system_prompt("a" * 300)  # ~100 tokens
        info = manager.get_context_info()
        assert info["usage_percentage"] == pytest.approx(10.0)


@pytest.mark.unit
class TestContextManagerFormatting:
    """Tests for message formatting for summary."""

    def test_format_messages_for_summary(self, manager):
        """Test formatting various messages for summary."""
        messages = [
            Mock(role="user", content=[{"type": "text", "text": "First"}]),
            Mock(role="assistant", content=[{"type": "text", "text": "Response"}]),
            Mock(role="assistant", content=[
                {"type": "tool_use", "tool_name": "bash"},
                {"type": "text", "text": "Result"}
            ])
        ]
        formatted = manager._format_messages_for_summary(messages)
        assert "user: First" in formatted
        assert "assistant: Response" in formatted
        assert "assistant: Result" in formatted
        assert "tool_use" not in formatted

    def test_format_messages_for_summary_empty(self, manager):
        """Test formatting empty messages returns an empty string."""
        assert manager._format_messages_for_summary([]) == ""

    def test_format_messages_truncates_long_text(self, manager):
        """Test formatting truncates long text to 200 characters."""
        long_text = "a" * 500
        msg = Mock(role="user", content=[{"type": "text", "text": long_text}])
        formatted = manager._format_messages_for_summary([msg])
        assert len(formatted) < 250
        assert long_text[:200] in formatted
        assert long_text[201:] not in formatted


@pytest.mark.unit
class TestContextManagerCompression:
    """Tests for context compression."""

    @pytest.mark.asyncio
    async def test_compress_if_needed_skips_when_not_needed(self, manager):
        """Test compression is skipped when token count is below max."""
        manager.add_user_message("Short message")
        mock_client = AsyncMock()
        
        await manager.compress_if_needed(mock_client)
        
        mock_client.generate_summary.assert_not_called()

    @pytest.mark.asyncio
    async def test_compress_if_needed_generates_summary(self, manager):
        """Test compression generates a summary when token count exceeds max."""
        manager.max_tokens = 500
        for i in range(20):
            manager.add_user_message("a" * 50)

        mock_client = AsyncMock()
        mock_client.generate_summary.return_value = "Generated summary"

        with patch('src.agents.context_manager.get_summarization_prompt', return_value="prompt"):
            await manager.compress_if_needed(mock_client)

        mock_client.generate_summary.assert_called_once()
        assert manager.summary == "Generated summary"
        assert len(manager.messages) == 10


@pytest.mark.unit
class TestContextManagerEdgeCases:
    """Tests for edge cases."""

    def test_usage_percentage_with_zero_max_tokens(self):
        """Test usage percentage is 0 when max_tokens is 0."""
        manager = AgentContextManager(max_tokens=0)
        manager.add_user_message("Test")
        info = manager.get_context_info()
        assert info["usage_percentage"] == 0

    def test_add_assistant_message_with_empty_content(self, manager):
        """Test adding an assistant message with an empty content list."""
        manager.add_assistant_message([])
        assert len(manager.messages) == 1
        assert len(manager.messages[0].content) == 0

    def test_message_with_unicode_content(self, manager):
        """Test messages handle unicode content correctly."""
        manager.add_user_message("你好，世界 🌍")
        msg = manager.get_messages()[0]
        assert "你好，世界 🌍" in msg["content"][0]["text"]

    def test_metadata_with_complex_values(self, manager):
        """Test metadata handles complex dictionary and list values."""
        value = {"nested": {"key": [1, 2, 3]}}
        manager.set_metadata("complex", value)
        assert manager.get_metadata("complex") == value


@pytest.mark.unit
class TestContextManagerIntegration:
    """Higher-level tests for typical conversation flows."""

    def test_typical_conversation_flow(self, manager):
        """Test a typical multi-turn conversation flow."""
        manager.set_system_prompt("You are helpful")
        manager.add_user_message("What is Python?")
        manager.add_assistant_message([{"type": "text", "text": "A programming language"}])
        manager.add_user_message("How do I learn it?")
        manager.add_assistant_message([{"type": "text", "text": "Practice"}])

        assert len(manager.messages) == 4
        assert manager.get_context_info()["message_count"] == 4

    def test_conversation_with_tools(self, manager):
        """Test a conversation flow involving tool use and results."""
        manager.add_user_message("Run ls")
        manager.add_assistant_message([{"type": "tool_use", "tool_name": "bash"}])
        manager.add_tool_results([{"type": "tool_result", "result": "file.txt"}])
        manager.add_assistant_message([{"type": "text", "text": "Found 1 file"}])

        assert len(manager.messages) == 4
        assert manager.get_last_message().role == "assistant"
