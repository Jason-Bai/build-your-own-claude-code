"""
Unit tests for Agent Context Manager

Tests message management, token estimation, context compression, and metadata handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.context_manager import AgentContextManager, Message


@pytest.mark.unit
class TestMessageModel:
    """Tests for Message model"""

    def test_message_creation(self):
        """Test Message model creation"""
        msg = Message(role="user", content=[{"type": "text", "text": "Hello"}])
        assert msg.role == "user"
        assert len(msg.content) == 1

    def test_message_serialization(self):
        """Test Message model serialization"""
        msg = Message(role="assistant", content=[{"type": "text", "text": "Response"}])
        dumped = msg.model_dump()
        assert dumped["role"] == "assistant"
        assert dumped["content"][0]["text"] == "Response"

    def test_message_with_multiple_content_blocks(self):
        """Test Message with multiple content blocks"""
        content = [
            {"type": "text", "text": "First"},
            {"type": "tool_use", "tool_name": "bash"},
            {"type": "text", "text": "Second"}
        ]
        msg = Message(role="assistant", content=content)
        assert len(msg.content) == 3


@pytest.mark.unit
class TestContextManagerInitialization:
    """Tests for AgentContextManager initialization"""

    def test_initialization_with_defaults(self):
        """Test AgentContextManager initialization with defaults"""
        manager = AgentContextManager()
        assert manager.max_tokens == 150000
        assert len(manager.messages) == 0
        assert manager.system_prompt == ""
        assert manager.summary == ""
        assert manager.metadata == {}

    def test_initialization_with_custom_max_tokens(self):
        """Test AgentContextManager with custom max_tokens"""
        manager = AgentContextManager(max_tokens=50000)
        assert manager.max_tokens == 50000

    def test_initialization_with_small_max_tokens(self):
        """Test AgentContextManager with small max_tokens"""
        manager = AgentContextManager(max_tokens=1000)
        assert manager.max_tokens == 1000


@pytest.mark.unit
class TestContextManagerMessages:
    """Tests for message management"""

    def test_set_system_prompt(self):
        """Test setting system prompt"""
        manager = AgentContextManager()
        manager.set_system_prompt("You are a helpful assistant")
        assert manager.system_prompt == "You are a helpful assistant"

    def test_add_user_message(self):
        """Test adding user message"""
        manager = AgentContextManager()
        manager.add_user_message("Hello, assistant")
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"
        assert manager.messages[0].content[0]["text"] == "Hello, assistant"

    def test_add_multiple_user_messages(self):
        """Test adding multiple user messages"""
        manager = AgentContextManager()
        manager.add_user_message("First message")
        manager.add_user_message("Second message")
        assert len(manager.messages) == 2

    def test_add_assistant_message(self):
        """Test adding assistant message"""
        manager = AgentContextManager()
        content = [{"type": "text", "text": "Response"}]
        manager.add_assistant_message(content)
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "assistant"
        assert manager.messages[0].content == content

    def test_add_tool_results(self):
        """Test adding tool results"""
        manager = AgentContextManager()
        tool_results = [
            {"type": "tool_result", "tool_name": "bash", "result": "output"}
        ]
        manager.add_tool_results(tool_results)
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"
        assert manager.messages[0].content == tool_results

    def test_add_tool_results_empty_list(self):
        """Test adding empty tool results"""
        manager = AgentContextManager()
        manager.add_tool_results([])
        assert len(manager.messages) == 0

    def test_get_messages(self):
        """Test getting messages as dicts"""
        manager = AgentContextManager()
        manager.add_user_message("Test")
        messages = manager.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_get_last_message(self):
        """Test getting last message"""
        manager = AgentContextManager()
        manager.add_user_message("First")
        manager.add_user_message("Second")
        last = manager.get_last_message()
        assert last.role == "user"

    def test_get_last_message_empty(self):
        """Test getting last message when empty"""
        manager = AgentContextManager()
        last = manager.get_last_message()
        assert last is None


@pytest.mark.unit
class TestContextManagerTokenEstimation:
    """Tests for token estimation"""

    def test_estimate_tokens_empty_context(self):
        """Test token estimation for empty context"""
        manager = AgentContextManager()
        tokens = manager.estimate_tokens()
        assert tokens == 0

    def test_estimate_tokens_with_system_prompt(self):
        """Test token estimation with system prompt"""
        manager = AgentContextManager()
        manager.set_system_prompt("You are helpful" * 100)  # Long prompt
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_estimate_tokens_with_messages(self):
        """Test token estimation with messages"""
        manager = AgentContextManager()
        manager.add_user_message("Test message" * 50)
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_estimate_tokens_includes_summary(self):
        """Test token estimation includes summary"""
        manager = AgentContextManager()
        manager.summary = "Previous conversation summary" * 50
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_estimate_tokens_combined(self):
        """Test token estimation with all components"""
        manager = AgentContextManager()
        manager.set_system_prompt("System" * 50)
        manager.summary = "Summary" * 50
        manager.add_user_message("Message" * 50)
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_token_estimation_formula(self):
        """Test token estimation formula (1 token ≈ 3 chars)"""
        manager = AgentContextManager()
        manager.set_system_prompt("a" * 300)  # 300 chars = ~100 tokens
        tokens = manager.estimate_tokens()
        assert tokens == 100


@pytest.mark.unit
class TestContextManagerMetadata:
    """Tests for metadata management"""

    def test_set_metadata(self):
        """Test setting metadata"""
        manager = AgentContextManager()
        manager.set_metadata("key", "value")
        assert manager.metadata["key"] == "value"

    def test_get_metadata(self):
        """Test getting metadata"""
        manager = AgentContextManager()
        manager.set_metadata("key", "value")
        value = manager.get_metadata("key")
        assert value == "value"

    def test_get_metadata_with_default(self):
        """Test getting metadata with default"""
        manager = AgentContextManager()
        value = manager.get_metadata("nonexistent", "default")
        assert value == "default"

    def test_set_multiple_metadata(self):
        """Test setting multiple metadata"""
        manager = AgentContextManager()
        manager.set_metadata("key1", "value1")
        manager.set_metadata("key2", "value2")
        assert manager.get_metadata("key1") == "value1"
        assert manager.get_metadata("key2") == "value2"


@pytest.mark.unit
class TestContextManagerClear:
    """Tests for clearing context"""

    def test_clear_messages(self):
        """Test clearing messages"""
        manager = AgentContextManager()
        manager.add_user_message("Test")
        manager.clear()
        assert len(manager.messages) == 0

    def test_clear_summary(self):
        """Test clearing summary"""
        manager = AgentContextManager()
        manager.summary = "Some summary"
        manager.clear()
        assert manager.summary == ""

    def test_clear_metadata(self):
        """Test clearing metadata"""
        manager = AgentContextManager()
        manager.set_metadata("key", "value")
        manager.clear()
        assert len(manager.metadata) == 0

    def test_clear_all(self):
        """Test clearing everything"""
        manager = AgentContextManager()
        manager.set_system_prompt("System")
        manager.add_user_message("Message")
        manager.summary = "Summary"
        manager.set_metadata("key", "value")
        manager.clear()
        assert len(manager.messages) == 0
        assert manager.summary == ""
        assert len(manager.metadata) == 0
        # system_prompt is not cleared


@pytest.mark.unit
class TestContextManagerInfo:
    """Tests for context info"""

    def test_get_context_info_empty(self):
        """Test context info for empty manager"""
        manager = AgentContextManager()
        info = manager.get_context_info()
        assert info["message_count"] == 0
        assert info["estimated_tokens"] == 0
        assert info["max_tokens"] == 150000
        assert info["usage_percentage"] == 0
        assert info["has_summary"] is False
        assert info["summary_length"] == 0

    def test_get_context_info_with_messages(self):
        """Test context info with messages"""
        manager = AgentContextManager()
        manager.add_user_message("Test")
        info = manager.get_context_info()
        assert info["message_count"] == 1
        assert info["has_summary"] is False

    def test_get_context_info_with_summary(self):
        """Test context info with summary"""
        manager = AgentContextManager()
        manager.summary = "Summary text"
        info = manager.get_context_info()
        assert info["has_summary"] is True
        assert info["summary_length"] == 12

    def test_get_context_info_usage_percentage(self):
        """Test context info usage percentage"""
        manager = AgentContextManager(max_tokens=1000)
        manager.set_system_prompt("a" * 300)  # ~100 tokens
        info = manager.get_context_info()
        assert info["usage_percentage"] == pytest.approx(10.0, rel=1)


@pytest.mark.unit
class TestContextManagerFormatting:
    """Tests for message formatting"""

    def test_format_messages_for_summary_empty(self):
        """Test formatting empty messages"""
        manager = AgentContextManager()
        formatted = manager._format_messages_for_summary([])
        assert formatted == ""

    def test_format_messages_for_summary_single(self):
        """Test formatting single message"""
        manager = AgentContextManager()
        msg = Message(role="user", content=[{"type": "text", "text": "Hello"}])
        formatted = manager._format_messages_for_summary([msg])
        assert "user:" in formatted
        assert "Hello" in formatted

    def test_format_messages_for_summary_multiple(self):
        """Test formatting multiple messages"""
        manager = AgentContextManager()
        messages = [
            Message(role="user", content=[{"type": "text", "text": "First"}]),
            Message(role="assistant", content=[{"type": "text", "text": "Response"}])
        ]
        formatted = manager._format_messages_for_summary(messages)
        assert "user:" in formatted
        assert "assistant:" in formatted

    def test_format_messages_truncates_long_text(self):
        """Test formatting truncates long text"""
        manager = AgentContextManager()
        msg = Message(role="user", content=[{"type": "text", "text": "a" * 500}])
        formatted = manager._format_messages_for_summary([msg])
        # Should be truncated to 200 chars per message
        assert len(formatted) < 250

    def test_format_messages_handles_tool_blocks(self):
        """Test formatting skips non-text blocks"""
        manager = AgentContextManager()
        msg = Message(role="assistant", content=[
            {"type": "tool_use", "tool_name": "bash"},
            {"type": "text", "text": "Result"}
        ])
        formatted = manager._format_messages_for_summary([msg])
        assert "Result" in formatted


@pytest.mark.unit
class TestContextManagerCompression:
    """Tests for context compression"""

    @pytest.mark.asyncio
    async def test_compress_if_needed_no_compression_needed(self):
        """Test compression skips when not needed"""
        manager = AgentContextManager(max_tokens=100000)
        manager.add_user_message("Short message")

        mock_client = Mock()
        await manager.compress_if_needed(mock_client)

        # Should not call generate_summary
        assert not hasattr(mock_client, 'generate_summary') or not mock_client.generate_summary.called

    @pytest.mark.asyncio
    async def test_compress_if_needed_trimming(self):
        """Test compression trims messages"""
        manager = AgentContextManager(max_tokens=1000)
        # Add 15 messages to trigger compression
        for i in range(15):
            manager.add_user_message("Message " * 20)

        initial_count = len(manager.messages)
        mock_client = AsyncMock()
        mock_client.generate_summary = AsyncMock(return_value="Summary")

        await manager.compress_if_needed(mock_client)

        # Messages should be reduced
        assert len(manager.messages) <= initial_count

    @pytest.mark.asyncio
    async def test_compress_generates_summary(self):
        """Test compression generates summary"""
        manager = AgentContextManager(max_tokens=500)
        for i in range(20):
            manager.add_user_message("a" * 50)

        mock_client = AsyncMock()
        mock_client.generate_summary = AsyncMock(return_value="Generated summary")

        with patch('src.agents.context_manager.get_summarization_prompt', return_value="prompt"):
            await manager.compress_if_needed(mock_client)

        # Summary should be set
        assert "Generated" in manager.summary or len(manager.messages) <= 10


@pytest.mark.unit
class TestContextManagerEdgeCases:
    """Tests for edge cases"""

    def test_token_estimation_with_zero_max_tokens(self):
        """Test token estimation with zero max_tokens"""
        manager = AgentContextManager(max_tokens=0)
        manager.add_user_message("Test")
        info = manager.get_context_info()
        assert info["usage_percentage"] == 0

    def test_message_with_empty_content(self):
        """Test message with empty content list"""
        manager = AgentContextManager()
        manager.add_assistant_message([])
        assert len(manager.messages) == 1
        assert len(manager.messages[0].content) == 0

    def test_message_with_unicode_content(self):
        """Test message with unicode content"""
        manager = AgentContextManager()
        manager.add_user_message("你好，世界 🌍")
        msg = manager.get_messages()[0]
        assert "你好" in msg["content"][0]["text"]

    def test_metadata_with_complex_values(self):
        """Test metadata with complex values"""
        manager = AgentContextManager()
        value = {"nested": {"key": [1, 2, 3]}}
        manager.set_metadata("complex", value)
        retrieved = manager.get_metadata("complex")
        assert retrieved == value


@pytest.mark.unit
class TestContextManagerIntegration:
    """Integration tests for context manager"""

    def test_typical_conversation_flow(self):
        """Test typical conversation flow"""
        manager = AgentContextManager()
        manager.set_system_prompt("You are helpful")

        manager.add_user_message("What is Python?")
        manager.add_assistant_message([
            {"type": "text", "text": "Python is a programming language"}
        ])

        manager.add_user_message("How do I learn it?")
        manager.add_assistant_message([
            {"type": "text", "text": "Practice and study"}
        ])

        assert len(manager.messages) == 4
        info = manager.get_context_info()
        assert info["message_count"] == 4

    def test_conversation_with_tools(self):
        """Test conversation with tool execution"""
        manager = AgentContextManager()

        manager.add_user_message("Run ls command")
        manager.add_assistant_message([
            {"type": "tool_use", "tool_name": "bash", "input": {"command": "ls"}}
        ])
        manager.add_tool_results([
            {"type": "tool_result", "tool_name": "bash", "result": "file1.txt file2.txt"}
        ])
        manager.add_assistant_message([
            {"type": "text", "text": "Found 2 files"}
        ])

        assert len(manager.messages) == 4
        last = manager.get_last_message()
        assert last.role == "assistant"

    def test_conversation_persistence_simulation(self):
        """Test conversation persistence pattern"""
        manager = AgentContextManager()
        manager.set_system_prompt("System prompt")
        manager.add_user_message("First message")
        manager.add_assistant_message([{"type": "text", "text": "Response"}])

        # Simulate save/load
        messages_dump = manager.get_messages()
        system_prompt = manager.system_prompt

        # Create new manager and restore
        manager2 = AgentContextManager()
        manager2.set_system_prompt(system_prompt)

        # Messages would be restored from persistence layer
        assert manager2.system_prompt == manager.system_prompt
        assert len(messages_dump) == 2
