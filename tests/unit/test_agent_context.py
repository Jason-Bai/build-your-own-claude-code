"""Unit tests for Agent Context Manager"""

import pytest
from src.agents.context_manager import AgentContextManager, Message


@pytest.mark.unit
class TestAgentContextManager:
    """Tests for context manager"""

    def test_initialization(self):
        """Test context manager initialization"""
        manager = AgentContextManager()
        assert manager.messages == []
        assert manager.system_prompt == ""
        assert manager.max_tokens == 150000
        assert manager.summary == ""
        assert manager.metadata == {}

    def test_set_system_prompt(self):
        """Test setting system prompt"""
        manager = AgentContextManager()
        manager.set_system_prompt("You are a helpful assistant")
        assert manager.system_prompt == "You are a helpful assistant"

    def test_add_user_message(self):
        """Test adding user message"""
        manager = AgentContextManager()
        manager.add_user_message("Hello")
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "user"

    def test_add_assistant_message(self):
        """Test adding assistant message"""
        manager = AgentContextManager()
        manager.add_assistant_message([{"type": "text", "text": "Hi"}])
        assert len(manager.messages) == 1
        assert manager.messages[0].role == "assistant"

    def test_add_tool_results(self):
        """Test adding tool results"""
        manager = AgentContextManager()
        results = [{"type": "tool_result", "tool_use_id": "1", "content": "result"}]
        manager.add_tool_results(results)
        assert len(manager.messages) == 1

    def test_get_messages(self):
        """Test getting messages in API format"""
        manager = AgentContextManager()
        manager.add_user_message("test")
        messages = manager.get_messages()
        assert len(messages) == 1
        assert isinstance(messages[0], dict)

    def test_get_last_message(self):
        """Test getting last message"""
        manager = AgentContextManager()
        manager.add_user_message("first")
        manager.add_user_message("second")
        last = manager.get_last_message()
        assert last.role == "user"

    def test_estimate_tokens(self):
        """Test token estimation"""
        manager = AgentContextManager()
        manager.set_system_prompt("x" * 300)
        manager.add_user_message("y" * 300)
        tokens = manager.estimate_tokens()
        assert tokens > 0

    def test_custom_max_tokens(self):
        """Test custom max tokens"""
        manager = AgentContextManager(max_tokens=50000)
        assert manager.max_tokens == 50000
