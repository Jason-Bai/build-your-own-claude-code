"""
Unit tests for Agent Context Manager

Tests message management, token estimation, context compression,
and metadata handling.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from src.agents.context_manager import Message, AgentContextManager


@pytest.mark.unit
class TestMessageInitialization:
    """Tests for Message creation"""

    def test_message_creation_user(self):
        """Test creating user message"""
        msg = Message(
            role="user",
            content=[{"type": "text", "text": "Hello"}]
        )

        assert msg.role == "user"
        assert len(msg.content) == 1
        assert msg.content[0]["text"] == "Hello"

    def test_message_creation_assistant(self):
        """Test creating assistant message"""
        msg = Message(
            role="assistant",
            content=[{"type": "text", "text": "Hi there"}]
        )

        assert msg.role == "assistant"
        assert msg.content[0]["text"] == "Hi there"

    def test_message_with_multiple_content_blocks(self):
        """Test message with multiple content blocks"""
        content = [
            {"type": "text", "text": "First block"},
            {"type": "tool_use", "id": "123", "name": "bash"}
        ]
        msg = Message(role="assistant", content=content)

        assert len(msg.content) == 2

    def test_message_model_dump(self):
        """Test message model_dump"""
        msg = Message(
            role="user",
            content=[{"type": "text", "text": "test"}]
        )

        dumped = msg.model_dump()
        assert dumped["role"] == "user"
        assert dumped["content"][0]["text"] == "test"


@pytest.mark.unit
class TestContextManagerInitialization:
    """Tests for ContextManager initialization"""

    def test_initialization_default(self):
        """Test ContextManager default initialization"""
        manager = AgentContextManager()

        assert isinstance(manager.messages, list)
        assert len(manager.messages) == 0
        assert manager.system_prompt == ""
        assert manager.max_tokens == 150000
        assert manager.summary == ""
        assert isinstance(manager.metadata, dict)

    def test_initialization_custom_max_tokens(self):
        """Test initialization with custom max_tokens"""
        manager = AgentContextManager(max_tokens=50000)

        assert manager.max_tokens == 50000

    def test_initialization_empty_metadata(self):
        """Test metadata initialized empty"""
        manager = AgentContextManager()

        assert manager.metadata == {}


@pytest.mark.unit
class TestSystemPrompt:
    """Tests for system prompt management"""

    def test_set_system_prompt(self):
        """Test setting system prompt"""
        manager = AgentContextManager()
        prompt = "You are a helpful assistant"

        manager.set_system_prompt(prompt)

        assert manager.system_prompt == prompt

    def test_set_system_prompt_multiple_times(self):
        """Test overwriting system prompt"""
        manager = AgentContextManager()

        manager.set_system_prompt("Prompt 1")
        manager.set_system_prompt("Prompt 2")

        assert manager.system_prompt == "Prompt 2"


@pytest.mark.unit
class TestMessageManagement:
    """Tests for message management"""

    def test_add_user_message(self):
        """Test adding user message"""
        manager = AgentContextManager()

        manager.add_user_message("Hello")

        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"
        assert manager.messages[0].content[0]["text"] == "Hello"

    def test_add_multiple_user_messages(self):
        """Test adding multiple user messages"""
        manager = AgentContextManager()

        manager.add_user_message("First")
        manager.add_user_message("Second")

        assert len(manager.messages) == 2

    def test_add_assistant_message(self):
        """Test adding assistant message"""
        manager = AgentContextManager()
        content = [{"type": "text", "text": "Response"}]

        manager.add_assistant_message(content)

        assert len(manager.messages) == 1
        assert manager.messages[0].role == "assistant"

    def test_add_tool_results(self):
        """Test adding tool results"""
        manager = AgentContextManager()
        tool_results = [
            {"type": "tool_result", "tool_use_id": "123", "content": "result"}
        ]

        manager.add_tool_results(tool_results)

        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"

    def test_add_empty_tool_results(self):
        """Test adding empty tool results does nothing"""
        manager = AgentContextManager()

        manager.add_tool_results([])

        assert len(manager.messages) == 0


@pytest.mark.unit
class TestMessageRetrieval:
    """Tests for retrieving messages"""

    def test_get_messages_format(self):
        """Test get_messages returns proper format"""
        manager = AgentContextManager()
        manager.add_user_message("Test")

        messages = manager.get_messages()

        assert isinstance(messages, list)
        assert isinstance(messages[0], dict)
        assert "role" in messages[0]
        assert "content" in messages[0]

    def test_get_last_message_exists(self):
        """Test getting last message"""
        manager = AgentContextManager()
        manager.add_user_message("First")
        manager.add_user_message("Second")

        last = manager.get_last_message()

        assert last is not None
        assert last.content[0]["text"] == "Second"

    def test_get_last_message_empty(self):
        """Test getting last message when empty"""
        manager = AgentContextManager()

        last = manager.get_last_message()

        assert last is None

    def test_get_messages_multiple(self):
        """Test getting all messages"""
        manager = AgentContextManager()
        manager.add_user_message("User")
        manager.add_assistant_message([{"type": "text", "text": "Assistant"}])

        messages = manager.get_messages()

        assert len(messages) == 2


@pytest.mark.unit
class TestTokenEstimation:
    """Tests for token estimation"""

    def test_estimate_tokens_empty(self):
        """Test token estimation when empty"""
        manager = AgentContextManager()

        tokens = manager.estimate_tokens()

        assert tokens == 0

    def test_estimate_tokens_with_user_message(self):
        """Test token estimation with user message"""
        manager = AgentContextManager()
        manager.add_user_message("Hello world")

        tokens = manager.estimate_tokens()

        assert tokens > 0

    def test_estimate_tokens_includes_system_prompt(self):
        """Test token estimation includes system prompt"""
        manager = AgentContextManager()
        manager.set_system_prompt("You are helpful" * 100)  # Long prompt

        tokens_without_msg = manager.estimate_tokens()
        manager.add_user_message("Test")
        tokens_with_msg = manager.estimate_tokens()

        assert tokens_with_msg > tokens_without_msg

    def test_estimate_tokens_includes_summary(self):
        """Test token estimation includes summary"""
        manager = AgentContextManager()
        manager.summary = "This is a summary" * 100

        tokens = manager.estimate_tokens()

        assert tokens > 0

    def test_token_estimation_formula(self):
        """Test token estimation formula (1 token ≈ 3 chars)"""
        manager = AgentContextManager()
        manager.add_user_message("123")  # 3 chars

        tokens = manager.estimate_tokens()

        # Should be at least 1 token
        assert tokens >= 1


@pytest.mark.unit
class TestClear:
    """Tests for clearing context"""

    def test_clear_messages(self):
        """Test clearing messages"""
        manager = AgentContextManager()
        manager.add_user_message("Test")
        manager.summary = "Summary"
        manager.metadata["key"] = "value"

        manager.clear()

        assert len(manager.messages) == 0
        assert manager.summary == ""
        assert len(manager.metadata) == 0

    def test_clear_leaves_system_prompt(self):
        """Test clear doesn't remove system prompt"""
        manager = AgentContextManager()
        manager.set_system_prompt("System")
        manager.add_user_message("User")

        manager.clear()

        assert manager.system_prompt == "System"


@pytest.mark.unit
class TestContextInfo:
    """Tests for context information"""

    def test_get_context_info(self):
        """Test getting context info"""
        manager = AgentContextManager()
        manager.add_user_message("Test")

        info = manager.get_context_info()

        assert "message_count" in info
        assert "estimated_tokens" in info
        assert "max_tokens" in info
        assert "usage_percentage" in info
        assert "has_summary" in info
        assert "summary_length" in info

    def test_context_info_message_count(self):
        """Test message count in context info"""
        manager = AgentContextManager()
        manager.add_user_message("1")
        manager.add_user_message("2")

        info = manager.get_context_info()

        assert info["message_count"] == 2

    def test_context_info_usage_percentage(self):
        """Test usage percentage calculation"""
        manager = AgentContextManager(max_tokens=100)

        info = manager.get_context_info()

        assert 0 <= info["usage_percentage"] <= 100

    def test_context_info_has_summary(self):
        """Test summary flag in context info"""
        manager = AgentContextManager()

        info = manager.get_context_info()
        assert info["has_summary"] is False

        manager.summary = "Test summary"
        info = manager.get_context_info()
        assert info["has_summary"] is True

    def test_context_info_summary_length(self):
        """Test summary length in context info"""
        manager = AgentContextManager()
        manager.summary = "Summary text"

        info = manager.get_context_info()

        assert info["summary_length"] == len("Summary text")


@pytest.mark.unit
class TestMetadata:
    """Tests for metadata management"""

    def test_set_metadata(self):
        """Test setting metadata"""
        manager = AgentContextManager()

        manager.set_metadata("key", "value")

        assert manager.metadata["key"] == "value"

    def test_get_metadata_existing(self):
        """Test getting existing metadata"""
        manager = AgentContextManager()
        manager.set_metadata("key", "value")

        result = manager.get_metadata("key")

        assert result == "value"

    def test_get_metadata_missing_default_none(self):
        """Test getting missing metadata returns None by default"""
        manager = AgentContextManager()

        result = manager.get_metadata("nonexistent")

        assert result is None

    def test_get_metadata_missing_default_custom(self):
        """Test getting missing metadata returns custom default"""
        manager = AgentContextManager()

        result = manager.get_metadata("nonexistent", "default")

        assert result == "default"

    def test_metadata_multiple_keys(self):
        """Test multiple metadata keys"""
        manager = AgentContextManager()
        manager.set_metadata("key1", "value1")
        manager.set_metadata("key2", "value2")

        assert manager.get_metadata("key1") == "value1"
        assert manager.get_metadata("key2") == "value2"


@pytest.mark.unit
class TestCompression:
    """Tests for context compression"""

    @pytest.mark.asyncio
    async def test_compress_if_needed_not_needed(self):
        """Test compress_if_needed when under limit"""
        manager = AgentContextManager(max_tokens=100000)
        client = AsyncMock()

        manager.add_user_message("Short message")
        await manager.compress_if_needed(client)

        # Client should not be called
        client.generate_summary.assert_not_called()
        assert len(manager.messages) == 1

    @pytest.mark.asyncio
    async def test_compress_if_needed_over_limit(self):
        """Test compress_if_needed when over limit"""
        manager = AgentContextManager(max_tokens=100)
        client = AsyncMock()
        client.generate_summary = AsyncMock(return_value="Summary")

        # Add many messages to exceed limit
        for i in range(20):
            manager.add_user_message("Message " * 100)

        await manager.compress_if_needed(client)

        # Should have called client and updated summary
        client.generate_summary.assert_called_once()
        assert manager.summary != ""

    @pytest.mark.asyncio
    async def test_compress_keeps_recent_messages(self):
        """Test compression keeps recent messages"""
        manager = AgentContextManager(max_tokens=100)
        client = AsyncMock()
        client.generate_summary = AsyncMock(return_value="Summary")

        # Add messages
        for i in range(15):
            manager.add_user_message(f"Message {i}" * 100)

        await manager.compress_if_needed(client)

        # Should keep recent messages (up to 10)
        assert len(manager.messages) <= 10


@pytest.mark.unit
class TestIntegration:
    """Integration tests"""

    def test_complete_conversation_flow(self):
        """Test complete conversation flow"""
        manager = AgentContextManager()
        manager.set_system_prompt("You are helpful")

        manager.add_user_message("Hi")
        manager.add_assistant_message([{"type": "text", "text": "Hello"}])
        manager.add_user_message("How are you?")

        messages = manager.get_messages()
        assert len(messages) == 3

        info = manager.get_context_info()
        assert info["message_count"] == 3

    def test_metadata_with_messages(self):
        """Test metadata alongside messages"""
        manager = AgentContextManager()
        manager.set_metadata("session_id", "123")
        manager.set_metadata("user_id", "user_1")
        manager.add_user_message("Test")

        assert manager.get_metadata("session_id") == "123"
        assert len(manager.messages) == 1

    def test_context_info_comprehensive(self):
        """Test comprehensive context info"""
        manager = AgentContextManager(max_tokens=10000)
        manager.set_system_prompt("System prompt")
        manager.add_user_message("User message")
        manager.add_assistant_message([{"type": "text", "text": "Assistant response"}])
        manager.summary = "Conversation summary"

        info = manager.get_context_info()

        assert info["message_count"] == 2
        assert info["has_summary"] is True
        assert info["max_tokens"] == 10000


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    def test_add_empty_user_message(self):
        """Test adding empty user message"""
        manager = AgentContextManager()

        manager.add_user_message("")

        assert len(manager.messages) == 1
        assert manager.messages[0].content[0]["text"] == ""

    def test_very_long_message(self):
        """Test with very long message"""
        manager = AgentContextManager()
        long_text = "x" * 10000

        manager.add_user_message(long_text)
        tokens = manager.estimate_tokens()

        assert tokens > 0

    def test_many_messages(self):
        """Test with many messages"""
        manager = AgentContextManager()

        for i in range(100):
            manager.add_user_message(f"Message {i}")

        assert len(manager.messages) == 100

    def test_unicode_in_message(self):
        """Test unicode in messages"""
        manager = AgentContextManager()

        manager.add_user_message("你好世界 🌍")

        assert len(manager.messages) == 1

    def test_json_in_content(self):
        """Test JSON in message content"""
        manager = AgentContextManager()
        content = [{"type": "text", "text": json.dumps({"key": "value"})}]

        manager.add_assistant_message(content)

        messages = manager.get_messages()
        assert json.dumps({"key": "value"}) in messages[0]["content"][0]["text"]

    def test_max_tokens_zero(self):
        """Test with max_tokens = 0"""
        manager = AgentContextManager(max_tokens=0)
        manager.add_user_message("Test")

        info = manager.get_context_info()

        # Should handle division gracefully
        assert "usage_percentage" in info
