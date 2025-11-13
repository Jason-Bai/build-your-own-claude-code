"""
Unit tests for Agent Context Manager module

Tests the AgentContextManager class which manages conversation context,
message accumulation, token estimation, and context compression.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.context_manager import AgentContextManager, Message


@pytest.mark.unit
class TestMessageModel:
    """Tests for Message Pydantic model"""

    def test_message_creation_with_text(self):
        """Test creating a message with text content"""
        msg = Message(
            role="user",
            content=[{"type": "text", "text": "Hello"}]
        )
        assert msg.role == "user"
        assert len(msg.content) == 1
        assert msg.content[0]["type"] == "text"
        assert msg.content[0]["text"] == "Hello"

    def test_message_creation_with_multiple_blocks(self):
        """Test creating a message with multiple content blocks"""
        msg = Message(
            role="assistant",
            content=[
                {"type": "text", "text": "Response"},
                {"type": "tool_use", "id": "123", "name": "read"}
            ]
        )
        assert msg.role == "assistant"
        assert len(msg.content) == 2
        assert msg.content[0]["type"] == "text"
        assert msg.content[1]["type"] == "tool_use"

    def test_message_model_dump(self):
        """Test serializing message to dict"""
        msg = Message(
            role="user",
            content=[{"type": "text", "text": "Test"}]
        )
        data = msg.model_dump()
        assert isinstance(data, dict)
        assert data["role"] == "user"
        assert isinstance(data["content"], list)


@pytest.mark.unit
class TestAgentContextManagerInitialization:
    """Tests for AgentContextManager initialization"""

    def test_initialization_with_defaults(self):
        """Test initializing context manager with default values"""
        manager = AgentContextManager()
        assert manager.messages == []
        assert manager.system_prompt == ""
        assert manager.max_tokens == 150000
        assert manager.summary == ""
        assert manager.metadata == {}

    def test_initialization_with_custom_max_tokens(self):
        """Test initializing with custom max_tokens"""
        manager = AgentContextManager(max_tokens=50000)
        assert manager.max_tokens == 50000

    def test_initialization_with_small_max_tokens(self):
        """Test initializing with small max_tokens for testing"""
        manager = AgentContextManager(max_tokens=100)
        assert manager.max_tokens == 100


@pytest.mark.unit
class TestSystemPromptManagement:
    """Tests for system prompt setting"""

    def test_set_system_prompt(self):
        """Test setting a system prompt"""
        manager = AgentContextManager()
        prompt = "You are a helpful assistant."
        manager.set_system_prompt(prompt)
        assert manager.system_prompt == prompt

    def test_set_system_prompt_overwrites_previous(self):
        """Test that setting system prompt overwrites previous"""
        manager = AgentContextManager()
        manager.set_system_prompt("First prompt")
        manager.set_system_prompt("Second prompt")
        assert manager.system_prompt == "Second prompt"

    def test_set_empty_system_prompt(self):
        """Test setting an empty system prompt"""
        manager = AgentContextManager()
        manager.set_system_prompt("")
        assert manager.system_prompt == ""


@pytest.mark.unit
class TestUserMessageAddition:
    """Tests for adding user messages"""

    def test_add_user_message(self):
        """Test adding a simple user message"""
        manager = AgentContextManager()
        manager.add_user_message("Hello, assistant!")
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"
        assert manager.messages[0].content[0]["type"] == "text"
        assert manager.messages[0].content[0]["text"] == "Hello, assistant!"

    def test_add_multiple_user_messages(self):
        """Test adding multiple user messages"""
        manager = AgentContextManager()
        manager.add_user_message("First message")
        manager.add_user_message("Second message")
        assert len(manager.messages) == 2
        assert manager.messages[0].content[0]["text"] == "First message"
        assert manager.messages[1].content[0]["text"] == "Second message"

    def test_add_user_message_with_empty_text(self):
        """Test adding a user message with empty text"""
        manager = AgentContextManager()
        manager.add_user_message("")
        assert len(manager.messages) == 1
        assert manager.messages[0].content[0]["text"] == ""

    def test_add_user_message_with_long_text(self):
        """Test adding a user message with very long text"""
        manager = AgentContextManager()
        long_text = "x" * 10000
        manager.add_user_message(long_text)
        assert len(manager.messages) == 1
        assert manager.messages[0].content[0]["text"] == long_text


@pytest.mark.unit
class TestAssistantMessageAddition:
    """Tests for adding assistant messages"""

    def test_add_assistant_message_with_text(self):
        """Test adding an assistant message with text content"""
        manager = AgentContextManager()
        content = [{"type": "text", "text": "Here is my response"}]
        manager.add_assistant_message(content)
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "assistant"
        assert manager.messages[0].content == content

    def test_add_assistant_message_with_tool_use(self):
        """Test adding an assistant message with tool use"""
        manager = AgentContextManager()
        content = [
            {"type": "tool_use", "id": "123", "name": "read", "input": {"path": "/tmp/file"}}
        ]
        manager.add_assistant_message(content)
        assert len(manager.messages) == 1
        assert manager.messages[0].content[0]["type"] == "tool_use"

    def test_add_assistant_message_with_mixed_content(self):
        """Test adding an assistant message with mixed text and tool use"""
        manager = AgentContextManager()
        content = [
            {"type": "text", "text": "I'll read the file"},
            {"type": "tool_use", "id": "123", "name": "read", "input": {"path": "/tmp/file"}}
        ]
        manager.add_assistant_message(content)
        assert len(manager.messages[0].content) == 2


@pytest.mark.unit
class TestToolResultsAddition:
    """Tests for adding tool results"""

    def test_add_tool_results_single_result(self):
        """Test adding a single tool result"""
        manager = AgentContextManager()
        results = [
            {"type": "tool_result", "tool_use_id": "123", "content": "File content"}
        ]
        manager.add_tool_results(results)
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"
        assert manager.messages[0].content == results

    def test_add_tool_results_multiple_results(self):
        """Test adding multiple tool results"""
        manager = AgentContextManager()
        results = [
            {"type": "tool_result", "tool_use_id": "123", "content": "Content 1"},
            {"type": "tool_result", "tool_use_id": "456", "content": "Content 2"}
        ]
        manager.add_tool_results(results)
        assert len(manager.messages) == 1
        assert len(manager.messages[0].content) == 2

    def test_add_tool_results_empty_list(self):
        """Test that adding empty tool results doesn't create a message"""
        manager = AgentContextManager()
        manager.add_tool_results([])
        assert len(manager.messages) == 0

    def test_add_tool_results_with_error(self):
        """Test adding tool results with error flag"""
        manager = AgentContextManager()
        results = [
            {"type": "tool_result", "tool_use_id": "123", "is_error": True, "content": "Error message"}
        ]
        manager.add_tool_results(results)
        assert len(manager.messages) == 1
        assert manager.messages[0].content[0]["is_error"] is True


@pytest.mark.unit
class TestMessageRetrieval:
    """Tests for retrieving messages"""

    def test_get_messages_empty(self):
        """Test getting messages when none exist"""
        manager = AgentContextManager()
        messages = manager.get_messages()
        assert messages == []

    def test_get_messages_returns_list_of_dicts(self):
        """Test that get_messages returns dicts, not Message objects"""
        manager = AgentContextManager()
        manager.add_user_message("Test")
        messages = manager.get_messages()
        assert isinstance(messages, list)
        assert isinstance(messages[0], dict)
        assert "role" in messages[0]
        assert "content" in messages[0]

    def test_get_messages_with_multiple_messages(self):
        """Test retrieving multiple messages in order"""
        manager = AgentContextManager()
        manager.add_user_message("First")
        manager.add_assistant_message([{"type": "text", "text": "Second"}])
        manager.add_user_message("Third")
        messages = manager.get_messages()
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"

    def test_get_last_message_when_empty(self):
        """Test getting last message when no messages exist"""
        manager = AgentContextManager()
        assert manager.get_last_message() is None

    def test_get_last_message_returns_most_recent(self):
        """Test that get_last_message returns the most recent message"""
        manager = AgentContextManager()
        manager.add_user_message("First")
        manager.add_assistant_message([{"type": "text", "text": "Second"}])
        last = manager.get_last_message()
        assert last.role == "assistant"
        assert last.content[0]["text"] == "Second"


@pytest.mark.unit
class TestTokenEstimation:
    """Tests for token estimation"""

    def test_estimate_tokens_empty_context(self):
        """Test token estimation with empty context"""
        manager = AgentContextManager()
        tokens = manager.estimate_tokens()
        assert tokens == 0

    def test_estimate_tokens_with_system_prompt(self):
        """Test token estimation includes system prompt"""
        manager = AgentContextManager()
        system_prompt = "x" * 300  # ~100 tokens
        manager.set_system_prompt(system_prompt)
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_estimate_tokens_with_messages(self):
        """Test token estimation includes messages"""
        manager = AgentContextManager()
        manager.add_user_message("x" * 300)
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_estimate_tokens_with_summary(self):
        """Test token estimation includes summary"""
        manager = AgentContextManager()
        manager.summary = "x" * 300
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_estimate_tokens_accumulates(self):
        """Test that token estimation accumulates from all sources"""
        manager = AgentContextManager()
        manager.set_system_prompt("x" * 300)
        manager.add_user_message("y" * 300)
        manager.summary = "z" * 300
        tokens = manager.estimate_tokens()
        # Should be roughly: 300/3 + 300/3 + 300/3 = 300 tokens
        assert tokens >= 250  # Allow some variance in calculation

    def test_estimate_tokens_long_messages(self):
        """Test token estimation with very long messages"""
        manager = AgentContextManager()
        manager.add_user_message("x" * 10000)
        tokens = manager.estimate_tokens()
        # 10000 chars / 3 ≈ 3333 tokens
        assert tokens > 3000


@pytest.mark.unit
class TestContextInfo:
    """Tests for context information retrieval"""

    def test_get_context_info_empty(self):
        """Test context info for empty context"""
        manager = AgentContextManager()
        info = manager.get_context_info()
        assert info["message_count"] == 0
        assert info["estimated_tokens"] == 0
        assert info["max_tokens"] == 150000
        assert info["usage_percentage"] == 0.0
        assert info["has_summary"] is False
        assert info["summary_length"] == 0

    def test_get_context_info_with_messages(self):
        """Test context info includes message count"""
        manager = AgentContextManager()
        manager.add_user_message("Test 1")
        manager.add_user_message("Test 2")
        info = manager.get_context_info()
        assert info["message_count"] == 2

    def test_get_context_info_usage_percentage(self):
        """Test context info calculates usage percentage"""
        manager = AgentContextManager(max_tokens=1000)
        manager.add_user_message("x" * 900)  # ~300 tokens
        info = manager.get_context_info()
        assert info["usage_percentage"] > 0
        assert info["usage_percentage"] < 100

    def test_get_context_info_with_summary(self):
        """Test context info detects summary presence"""
        manager = AgentContextManager()
        assert manager.get_context_info()["has_summary"] is False
        manager.summary = "This is a summary"
        info = manager.get_context_info()
        assert info["has_summary"] is True
        assert info["summary_length"] > 0


@pytest.mark.unit
class TestMetadataManagement:
    """Tests for metadata operations"""

    def test_set_metadata(self):
        """Test setting metadata"""
        manager = AgentContextManager()
        manager.set_metadata("key1", "value1")
        assert manager.metadata["key1"] == "value1"

    def test_get_metadata_existing(self):
        """Test retrieving existing metadata"""
        manager = AgentContextManager()
        manager.set_metadata("key1", "value1")
        value = manager.get_metadata("key1")
        assert value == "value1"

    def test_get_metadata_missing_with_default(self):
        """Test retrieving missing metadata returns default"""
        manager = AgentContextManager()
        value = manager.get_metadata("nonexistent", "default")
        assert value == "default"

    def test_get_metadata_missing_without_default(self):
        """Test retrieving missing metadata returns None"""
        manager = AgentContextManager()
        value = manager.get_metadata("nonexistent")
        assert value is None

    def test_metadata_multiple_values(self):
        """Test storing multiple metadata values"""
        manager = AgentContextManager()
        manager.set_metadata("key1", "value1")
        manager.set_metadata("key2", 42)
        manager.set_metadata("key3", {"nested": "object"})
        assert manager.get_metadata("key1") == "value1"
        assert manager.get_metadata("key2") == 42
        assert manager.get_metadata("key3") == {"nested": "object"}

    def test_metadata_overwrite(self):
        """Test overwriting metadata value"""
        manager = AgentContextManager()
        manager.set_metadata("key", "original")
        manager.set_metadata("key", "updated")
        assert manager.get_metadata("key") == "updated"


@pytest.mark.unit
class TestContextClear:
    """Tests for clearing context"""

    def test_clear_empties_messages(self):
        """Test that clear removes all messages"""
        manager = AgentContextManager()
        manager.add_user_message("Message 1")
        manager.add_user_message("Message 2")
        manager.clear()
        assert len(manager.messages) == 0

    def test_clear_removes_summary(self):
        """Test that clear removes summary"""
        manager = AgentContextManager()
        manager.summary = "Some summary"
        manager.clear()
        assert manager.summary == ""

    def test_clear_removes_metadata(self):
        """Test that clear removes all metadata"""
        manager = AgentContextManager()
        manager.set_metadata("key1", "value1")
        manager.set_metadata("key2", "value2")
        manager.clear()
        assert len(manager.metadata) == 0

    def test_clear_preserves_system_prompt(self):
        """Test that clear doesn't remove system prompt"""
        manager = AgentContextManager()
        manager.set_system_prompt("System prompt")
        manager.clear()
        assert manager.system_prompt == "System prompt"

    def test_clear_preserves_max_tokens(self):
        """Test that clear preserves max_tokens setting"""
        manager = AgentContextManager(max_tokens=50000)
        manager.clear()
        assert manager.max_tokens == 50000


@pytest.mark.unit
class TestFormatMessagesForSummary:
    """Tests for message formatting for summarization"""

    def test_format_messages_single_text_message(self):
        """Test formatting a single text message"""
        manager = AgentContextManager()
        messages = [
            Message(role="user", content=[{"type": "text", "text": "Hello"}])
        ]
        formatted = manager._format_messages_for_summary(messages)
        assert "user:" in formatted
        assert "Hello" in formatted

    def test_format_messages_multiple_messages(self):
        """Test formatting multiple messages"""
        manager = AgentContextManager()
        messages = [
            Message(role="user", content=[{"type": "text", "text": "Message 1"}]),
            Message(role="assistant", content=[{"type": "text", "text": "Response 1"}])
        ]
        formatted = manager._format_messages_for_summary(messages)
        assert "user:" in formatted
        assert "assistant:" in formatted

    def test_format_messages_ignores_non_text(self):
        """Test that formatting ignores non-text blocks"""
        manager = AgentContextManager()
        messages = [
            Message(
                role="assistant",
                content=[
                    {"type": "text", "text": "Text part"},
                    {"type": "tool_use", "id": "123", "name": "read"}
                ]
            )
        ]
        formatted = manager._format_messages_for_summary(messages)
        assert "Text part" in formatted
        assert "tool_use" not in formatted

    def test_format_messages_truncates_long_text(self):
        """Test that formatting truncates very long messages"""
        manager = AgentContextManager()
        long_text = "x" * 500
        messages = [
            Message(role="user", content=[{"type": "text", "text": long_text}])
        ]
        formatted = manager._format_messages_for_summary(messages)
        # Should be truncated to ~200 chars based on code
        assert len(formatted) < len(long_text)


@pytest.mark.asyncio
@pytest.mark.unit
class TestContextCompression:
    """Tests for context compression"""

    async def test_compress_when_not_needed(self, mock_llm_client):
        """Test that compression doesn't run when under token limit"""
        manager = AgentContextManager(max_tokens=100000)
        manager.add_user_message("Short message")
        initial_count = len(manager.messages)
        await manager.compress_if_needed(mock_llm_client)
        assert len(manager.messages) == initial_count
        # Mock client should not be called
        mock_llm_client.generate_summary.assert_not_called()

    async def test_compress_removes_old_messages(self, mock_llm_client):
        """Test that compression keeps recent messages"""
        manager = AgentContextManager(max_tokens=100)
        # Add enough messages to trigger compression
        for i in range(20):
            manager.add_user_message(f"Message {i}")
        await manager.compress_if_needed(mock_llm_client)
        # Should keep last 10 messages
        assert len(manager.messages) <= 10

    async def test_compress_generates_summary(self, mock_llm_client):
        """Test that compression generates a summary"""
        manager = AgentContextManager(max_tokens=100)
        for i in range(20):
            manager.add_user_message(f"Message {i}")
        await manager.compress_if_needed(mock_llm_client)
        # Summary should be generated
        mock_llm_client.generate_summary.assert_called()
        assert manager.summary != ""

    async def test_compress_few_long_messages(self, mock_llm_client):
        """Test compression with few but long messages"""
        manager = AgentContextManager(max_tokens=100)
        # Add a few very long messages
        manager.add_user_message("x" * 5000)
        manager.add_user_message("y" * 5000)
        await manager.compress_if_needed(mock_llm_client)
        # Should keep only the most recent 10
        assert len(manager.messages) <= 10

    async def test_compress_preserves_recent_messages(self, mock_llm_client):
        """Test that compression preserves the most recent messages"""
        manager = AgentContextManager(max_tokens=100)
        # Add many messages with distinguishable content
        for i in range(20):
            manager.add_user_message(f"Message {i}")

        await manager.compress_if_needed(mock_llm_client)

        # Last message should still be present
        last = manager.get_last_message()
        assert last.content[0]["text"] == "Message 19"


@pytest.mark.unit
class TestMessageConversationFlow:
    """Tests for realistic conversation flows"""

    def test_simple_conversation(self):
        """Test a simple user-assistant conversation"""
        manager = AgentContextManager()
        manager.set_system_prompt("You are helpful")
        manager.add_user_message("What is 2+2?")
        manager.add_assistant_message([{"type": "text", "text": "4"}])
        manager.add_user_message("What about 3+3?")
        manager.add_assistant_message([{"type": "text", "text": "6"}])

        messages = manager.get_messages()
        assert len(messages) == 4
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["role"] == "user"
        assert messages[3]["role"] == "assistant"

    def test_conversation_with_tool_use(self):
        """Test conversation involving tool use"""
        manager = AgentContextManager()
        manager.add_user_message("Read the file")
        manager.add_assistant_message([
            {"type": "text", "text": "I'll read it"},
            {"type": "tool_use", "id": "123", "name": "read", "input": {"path": "/tmp/file"}}
        ])
        manager.add_tool_results([
            {"type": "tool_result", "tool_use_id": "123", "content": "File contents"}
        ])
        manager.add_assistant_message([
            {"type": "text", "text": "Here's what was in the file"}
        ])

        messages = manager.get_messages()
        assert len(messages) == 4
        # Find tool_use block
        assistant_msg = messages[1]
        tool_blocks = [b for b in assistant_msg["content"] if b["type"] == "tool_use"]
        assert len(tool_blocks) == 1

    def test_multi_turn_context_accumulation(self):
        """Test that context properly accumulates over multiple turns"""
        manager = AgentContextManager()

        for turn in range(5):
            manager.add_user_message(f"User turn {turn}")
            manager.add_assistant_message([{"type": "text", "text": f"Assistant turn {turn}"}])

        info = manager.get_context_info()
        assert info["message_count"] == 10  # 5 user + 5 assistant
        assert info["estimated_tokens"] > 0


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_very_small_max_tokens(self):
        """Test handling of very small max_tokens"""
        manager = AgentContextManager(max_tokens=1)
        manager.add_user_message("Test")
        info = manager.get_context_info()
        # Usage percentage should be high or handle division
        assert isinstance(info["usage_percentage"], (int, float))

    def test_zero_max_tokens(self):
        """Test handling of zero max_tokens"""
        manager = AgentContextManager(max_tokens=0)
        info = manager.get_context_info()
        # Should handle division by zero gracefully
        assert info["usage_percentage"] == 0

    def test_messages_list_operations(self):
        """Test that messages can be manipulated directly if needed"""
        manager = AgentContextManager()
        manager.add_user_message("First")
        manager.add_user_message("Second")
        # Test that messages list is accessible
        assert isinstance(manager.messages, list)
        assert len(manager.messages) == 2

    def test_metadata_with_various_types(self):
        """Test metadata with various Python types"""
        manager = AgentContextManager()
        manager.set_metadata("string", "value")
        manager.set_metadata("number", 42)
        manager.set_metadata("float", 3.14)
        manager.set_metadata("list", [1, 2, 3])
        manager.set_metadata("dict", {"key": "value"})
        manager.set_metadata("none", None)

        assert manager.get_metadata("string") == "value"
        assert manager.get_metadata("number") == 42
        assert manager.get_metadata("float") == 3.14
        assert manager.get_metadata("list") == [1, 2, 3]
        assert manager.get_metadata("dict") == {"key": "value"}
        assert manager.get_metadata("none") is None

    def test_content_with_empty_blocks(self):
        """Test handling of messages with empty content blocks"""
        manager = AgentContextManager()
        # Should handle empty text
        manager.add_user_message("")
        assert len(manager.messages) == 1
