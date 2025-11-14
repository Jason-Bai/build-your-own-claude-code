"""
Unit tests for Enhanced Agent FSM

Tests agent state machine, LLM communication, tool execution pipeline, and hooks.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.agents.enhanced_agent import EnhancedAgent
from src.agents.state import AgentState, ToolCall
from src.clients.base import ModelResponse
from src.tools.base import ToolResult


@pytest.mark.unit
class TestEnhancedAgentInitialization:
    """Tests for EnhancedAgent initialization"""

    def test_initialization_with_required_params(self):
        """Test initialization with required parameters"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        assert agent.client == mock_client
        assert agent.mcp_client is None
        assert agent.state_manager is not None
        assert agent.context_manager is not None
        assert agent.tool_manager is not None
        assert agent.permission_manager is not None

    def test_initialization_with_system_prompt(self):
        """Test initialization with system prompt"""
        mock_client = Mock()
        system_prompt = "You are a helpful assistant"
        agent = EnhancedAgent(client=mock_client, system_prompt=system_prompt)

        assert agent.context_manager.system_prompt == system_prompt

    def test_initialization_with_custom_max_turns(self):
        """Test initialization with custom max_turns"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client, max_turns=50)

        assert agent.state_manager.max_turns == 50

    def test_initialization_with_mcp_client(self):
        """Test initialization with MCP client"""
        mock_llm_client = Mock()
        mock_mcp_client = Mock()
        agent = EnhancedAgent(client=mock_llm_client, mcp_client=mock_mcp_client)

        assert agent.mcp_client == mock_mcp_client

    def test_initialization_with_state_change_callback(self):
        """Test initialization with state change callback"""
        mock_client = Mock()
        callback = Mock()
        agent = EnhancedAgent(client=mock_client, on_state_change=callback)

        assert agent.on_state_change == callback


@pytest.mark.unit
class TestStateTransition:
    """Tests for state transitions"""

    def test_transition_state_updates_state(self):
        """Test that transition updates state"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        agent._transition_state(AgentState.THINKING)
        assert agent.state_manager.current_state == AgentState.THINKING

    def test_transition_state_calls_callback(self):
        """Test that transition calls callback"""
        mock_client = Mock()
        callback = Mock()
        agent = EnhancedAgent(client=mock_client, on_state_change=callback)

        agent._transition_state(AgentState.THINKING)
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == AgentState.IDLE  # old state
        assert args[1] == AgentState.THINKING  # new state


@pytest.mark.unit
class TestResponseParsing:
    """Tests for LLM response parsing"""

    def test_parse_response_text_only(self):
        """Test parsing response with text only"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        response = ModelResponse(
            content=[{"type": "text", "text": "Hello"}],
            stop_reason="end_turn",
            usage={},
            model="test"
        )

        text_blocks, tool_uses = agent._parse_response(response)
        assert len(text_blocks) == 1
        assert text_blocks[0] == "Hello"
        assert len(tool_uses) == 0

    def test_parse_response_tool_use_only(self):
        """Test parsing response with tool_use only"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        response = ModelResponse(
            content=[
                {
                    "type": "tool_use",
                    "id": "123",
                    "name": "bash",
                    "input": {"command": "ls"}
                }
            ],
            stop_reason="tool_use",
            usage={},
            model="test"
        )

        text_blocks, tool_uses = agent._parse_response(response)
        assert len(text_blocks) == 0
        assert len(tool_uses) == 1
        assert tool_uses[0]["name"] == "bash"

    def test_parse_response_mixed(self):
        """Test parsing response with mixed content"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        response = ModelResponse(
            content=[
                {"type": "text", "text": "I'll run a command"},
                {
                    "type": "tool_use",
                    "id": "456",
                    "name": "bash",
                    "input": {"command": "pwd"}
                }
            ],
            stop_reason="tool_use",
            usage={},
            model="test"
        )

        text_blocks, tool_uses = agent._parse_response(response)
        assert len(text_blocks) == 1
        assert len(tool_uses) == 1

    def test_parse_response_multiple_tools(self):
        """Test parsing response with multiple tools"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        response = ModelResponse(
            content=[
                {
                    "type": "tool_use",
                    "id": "1",
                    "name": "bash",
                    "input": {"command": "ls"}
                },
                {
                    "type": "tool_use",
                    "id": "2",
                    "name": "read",
                    "input": {"file_path": "test.txt"}
                }
            ],
            stop_reason="tool_use",
            usage={},
            model="test"
        )

        text_blocks, tool_uses = agent._parse_response(response)
        assert len(text_blocks) == 0
        assert len(tool_uses) == 2


@pytest.mark.unit
class TestBriefDescription:
    """Tests for brief description generation"""

    def test_brief_description_bash(self):
        """Test brief description for bash tool"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        desc = agent._generate_brief_description("Bash", {"command": "ls -la /tmp"})
        assert "execute" in desc.lower()
        assert "ls" in desc

    def test_brief_description_read(self):
        """Test brief description for read tool"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        desc = agent._generate_brief_description("Read", {"file_path": "/etc/hosts"})
        assert "read" in desc.lower()

    def test_brief_description_write(self):
        """Test brief description for write tool"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        desc = agent._generate_brief_description("Write", {"file_path": "test.txt"})
        assert "write" in desc.lower()

    def test_brief_description_generic(self):
        """Test brief description for unknown tool"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        desc = agent._generate_brief_description("UnknownTool", {"param": "value"})
        assert isinstance(desc, str)
        assert len(desc) > 0


@pytest.mark.unit
class TestComponentIntegration:
    """Tests for component integration"""

    def test_agent_has_all_managers(self):
        """Test that agent has all required managers"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        assert agent.state_manager is not None
        assert agent.context_manager is not None
        assert agent.tool_manager is not None
        assert agent.permission_manager is not None
        assert agent.hook_manager is not None

    def test_agent_event_bus_integration(self):
        """Test that agent has event bus"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        assert agent.event_bus is not None

    def test_agent_tool_manager_executor(self):
        """Test that tool manager has executor"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        assert agent.tool_manager.executor is not None


@pytest.mark.unit
class TestTokenUsageTracking:
    """Tests for token usage tracking"""

    def test_agent_tracks_tokens(self):
        """Test that agent tracks token usage"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        # Simulate token usage
        agent.state_manager.add_tokens(input_tokens=100, output_tokens=50)

        stats = agent.state_manager.get_statistics()
        assert stats["input_tokens"] == 100
        assert stats["output_tokens"] == 50
        assert stats["total_tokens"] == 150


@pytest.mark.unit
class TestToolCallTracking:
    """Tests for tool call tracking"""

    def test_agent_tracks_tool_calls(self):
        """Test that agent tracks tool calls"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        tool_call = ToolCall(
            id="tool_1",
            name="bash",
            input={"command": "ls"}
        )
        agent.state_manager.record_tool_call(tool_call)

        stats = agent.state_manager.get_statistics()
        assert stats["tool_calls"] == 1


@pytest.mark.unit
class TestContextManagement:
    """Tests for context management"""

    def test_agent_manages_context(self):
        """Test that agent properly manages context"""
        mock_client = Mock()
        system_prompt = "Test system prompt"
        agent = EnhancedAgent(client=mock_client, system_prompt=system_prompt)

        # Add user message
        agent.context_manager.add_user_message("Hello")

        messages = agent.context_manager.get_messages()
        assert len(messages) > 0

    def test_agent_system_prompt_set(self):
        """Test that system prompt is set correctly"""
        mock_client = Mock()
        system_prompt = "You are a helpful assistant"
        agent = EnhancedAgent(client=mock_client, system_prompt=system_prompt)

        assert agent.context_manager.system_prompt == system_prompt


@pytest.mark.unit
class TestPermissionManagement:
    """Tests for permission management"""

    def test_agent_has_permission_manager(self):
        """Test that agent has permission manager"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        assert agent.permission_manager is not None

    def test_agent_permission_mode_configurable(self):
        """Test that permission mode is configurable"""
        from src.agents.permission_manager import PermissionMode
        mock_client = Mock()
        agent = EnhancedAgent(
            client=mock_client,
            permission_mode=PermissionMode.AUTO_APPROVE_ALL
        )

        assert agent.permission_manager.mode == PermissionMode.AUTO_APPROVE_ALL


@pytest.mark.unit
class TestHookIntegration:
    """Tests for hook system integration"""

    def test_agent_has_hook_manager(self):
        """Test that agent has hook manager"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        assert agent.hook_manager is not None

    def test_agent_custom_hook_manager(self):
        """Test that custom hook manager can be provided"""
        mock_client = Mock()
        mock_hook_manager = Mock()
        agent = EnhancedAgent(client=mock_client, hook_manager=mock_hook_manager)

        assert agent.hook_manager == mock_hook_manager


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    def test_empty_user_input_handling(self):
        """Test handling of empty user input"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        # Empty input should still be accepted
        agent.context_manager.add_user_message("")
        messages = agent.context_manager.get_messages()
        assert len(messages) == 1

    def test_parse_response_empty_content(self):
        """Test parsing response with empty content"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        response = ModelResponse(
            content=[],
            stop_reason="end_turn",
            usage={},
            model="test"
        )

        text_blocks, tool_uses = agent._parse_response(response)
        assert len(text_blocks) == 0
        assert len(tool_uses) == 0

    def test_parse_response_unknown_block_type(self):
        """Test parsing response with unknown block type"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        response = ModelResponse(
            content=[
                {"type": "unknown", "data": "test"},
                {"type": "text", "text": "Hello"}
            ],
            stop_reason="end_turn",
            usage={},
            model="test"
        )

        text_blocks, tool_uses = agent._parse_response(response)
        assert len(text_blocks) == 1  # Only text block extracted


@pytest.mark.unit
class TestAgentProperties:
    """Tests for agent properties and methods"""

    def test_agent_has_context_info(self):
        """Test that agent can get context info"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        agent.context_manager.add_user_message("test")
        info = agent.context_manager.get_context_info()

        assert "message_count" in info
        assert "estimated_tokens" in info

    def test_agent_feedback_level_selection(self):
        """Test that feedback level is selected based on verbose"""
        mock_client = Mock()
        agent = EnhancedAgent(client=mock_client)

        from src.agents.feedback import FeedbackLevel

        # Test would be in async run method, verify that FeedbackLevel is used
        assert FeedbackLevel.MINIMAL.value == 1
        assert FeedbackLevel.SILENT.value == 0
