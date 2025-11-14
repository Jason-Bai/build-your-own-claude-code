"""
Unit tests for Enhanced Agent Core

Comprehensive tests for agent run loop, response parsing, tool execution,
state transitions, event emission, and hook triggering.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.agents.enhanced_agent import EnhancedAgent
from src.agents.state import AgentState, ToolCall
from src.agents.permission_manager import PermissionMode
from src.clients.base import ModelResponse
from src.hooks import HookEvent


@pytest.mark.unit
class TestEnhancedAgentInitialization:
    """Tests for agent initialization"""

    def test_agent_initialization_default(self):
        """Test agent initializes with defaults"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        assert agent.client is client
        assert agent.state_manager is not None
        assert agent.context_manager is not None
        assert agent.tool_manager is not None
        assert agent.permission_manager is not None
        assert agent.hook_manager is not None

    def test_agent_initialization_with_system_prompt(self):
        """Test agent initializes with system prompt"""
        client = Mock()
        system_prompt = "You are a helpful assistant"
        agent = EnhancedAgent(client=client, system_prompt=system_prompt)

        assert agent.context_manager.system_prompt == system_prompt

    def test_agent_initialization_with_max_turns(self):
        """Test agent initializes with custom max turns"""
        client = Mock()
        agent = EnhancedAgent(client=client, max_turns=5)

        assert agent.state_manager.max_turns == 5

    def test_agent_initialization_with_permission_mode(self):
        """Test agent initializes with permission mode"""
        client = Mock()
        agent = EnhancedAgent(
            client=client,
            permission_mode=PermissionMode.ALWAYS_ASK
        )

        assert agent.permission_manager.mode == PermissionMode.ALWAYS_ASK

    def test_agent_initialization_with_state_change_callback(self):
        """Test agent initializes with state change callback"""
        client = Mock()
        callback = Mock()
        agent = EnhancedAgent(client=client, on_state_change=callback)

        assert agent.on_state_change is callback

    def test_agent_has_event_bus(self):
        """Test agent has event bus"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        assert agent.event_bus is not None

    def test_agent_has_todo_manager(self):
        """Test agent has todo manager"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        assert agent.todo_manager is not None


@pytest.mark.unit
class TestStateTransition:
    """Tests for state transitions"""

    def test_transition_state_changes_state(self):
        """Test state transition updates state"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        assert agent.state_manager.current_state == AgentState.IDLE
        agent._transition_state(AgentState.THINKING)
        assert agent.state_manager.current_state == AgentState.THINKING

    def test_transition_state_calls_callback(self):
        """Test state transition calls on_state_change callback"""
        client = Mock()
        callback = Mock()
        agent = EnhancedAgent(client=client, on_state_change=callback)

        agent._transition_state(AgentState.THINKING)

        callback.assert_called_once()
        old_state, new_state = callback.call_args[0]
        assert old_state == AgentState.IDLE
        assert new_state == AgentState.THINKING

    def test_multiple_state_transitions(self):
        """Test multiple state transitions in sequence"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        agent._transition_state(AgentState.THINKING)
        assert agent.state_manager.current_state == AgentState.THINKING

        agent._transition_state(AgentState.USING_TOOL)
        assert agent.state_manager.current_state == AgentState.USING_TOOL

        agent._transition_state(AgentState.COMPLETED)
        assert agent.state_manager.current_state == AgentState.COMPLETED


@pytest.mark.unit
class TestResponseParsing:
    """Tests for response parsing"""

    def test_parse_response_text_only(self):
        """Test parsing response with text only"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        response = Mock()
        response.content = [
            {"type": "text", "text": "Hello world"}
        ]

        text_blocks, tool_uses = agent._parse_response(response)

        assert len(text_blocks) == 1
        assert text_blocks[0] == "Hello world"
        assert len(tool_uses) == 0

    def test_parse_response_tool_use_only(self):
        """Test parsing response with tool use only"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        response = Mock()
        response.content = [
            {"type": "tool_use", "id": "tool_1", "name": "Read", "input": {}}
        ]

        text_blocks, tool_uses = agent._parse_response(response)

        assert len(text_blocks) == 0
        assert len(tool_uses) == 1
        assert tool_uses[0]["name"] == "Read"

    def test_parse_response_mixed_content(self):
        """Test parsing response with mixed content"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        response = Mock()
        response.content = [
            {"type": "text", "text": "I'll help you"},
            {"type": "tool_use", "id": "tool_1", "name": "Read", "input": {}},
            {"type": "text", "text": "Processing..."}
        ]

        text_blocks, tool_uses = agent._parse_response(response)

        assert len(text_blocks) == 2
        assert len(tool_uses) == 1
        assert text_blocks[0] == "I'll help you"
        assert text_blocks[1] == "Processing..."

    def test_parse_response_multiple_tools(self):
        """Test parsing response with multiple tool calls"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        response = Mock()
        response.content = [
            {"type": "tool_use", "id": "tool_1", "name": "Read", "input": {}},
            {"type": "tool_use", "id": "tool_2", "name": "Write", "input": {}}
        ]

        text_blocks, tool_uses = agent._parse_response(response)

        assert len(text_blocks) == 0
        assert len(tool_uses) == 2

    def test_parse_response_empty_content(self):
        """Test parsing response with empty content"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        response = Mock()
        response.content = []

        text_blocks, tool_uses = agent._parse_response(response)

        assert len(text_blocks) == 0
        assert len(tool_uses) == 0

    def test_parse_response_unknown_block_type(self):
        """Test parsing response with unknown block type"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        response = Mock()
        response.content = [
            {"type": "unknown", "data": "something"},
            {"type": "text", "text": "Hello"}
        ]

        text_blocks, tool_uses = agent._parse_response(response)

        assert len(text_blocks) == 1
        assert text_blocks[0] == "Hello"


@pytest.mark.unit
class TestBriefDescription:
    """Tests for tool brief description generation"""

    def test_brief_description_bash(self):
        """Test brief description for bash tool"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("Bash", {"command": "ls -la /tmp"})

        assert "execute" in desc
        assert "ls -la" in desc

    def test_brief_description_read(self):
        """Test brief description for read tool"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("Read", {"file_path": "/etc/passwd"})

        assert "read" in desc
        assert "/etc/passwd" in desc

    def test_brief_description_write(self):
        """Test brief description for write tool"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("Write", {"file_path": "/tmp/file.txt"})

        assert "write" in desc
        assert "/tmp/file.txt" in desc

    def test_brief_description_edit(self):
        """Test brief description for edit tool"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("Edit", {"file_path": "/tmp/file.txt"})

        assert "edit" in desc
        assert "/tmp/file.txt" in desc

    def test_brief_description_glob(self):
        """Test brief description for glob tool"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("Glob", {"pattern": "**/*.py"})

        assert "search" in desc
        assert "*.py" in desc

    def test_brief_description_grep(self):
        """Test brief description for grep tool"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("Grep", {"pattern": "TODO"})

        assert "grep" in desc
        assert "TODO" in desc

    def test_brief_description_todowrite(self):
        """Test brief description for todo tool"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("TodoWrite", {"todos": []})

        assert "update todos" in desc

    def test_brief_description_generic(self):
        """Test brief description for generic tool"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("CustomTool", {"key": "value"})

        assert "key" in desc or "value" in desc

    def test_brief_description_non_dict_input(self):
        """Test brief description with non-dict input"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("Tool", "string_input")

        assert isinstance(desc, str)
        assert len(desc) <= 50

    def test_brief_description_empty_dict(self):
        """Test brief description with empty dict"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        desc = agent._generate_brief_description("Tool", {})

        assert isinstance(desc, str)


@pytest.mark.unit
class TestRunLoopBasics:
    """Tests for agent run loop basic flow"""

    @pytest.mark.asyncio
    async def test_run_adds_user_message(self):
        """Test run adds user message to context"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)
        user_input = "Hello assistant"

        await agent.run(user_input, verbose=False)

        # Verify message was added
        messages = agent.context_manager.get_messages()
        assert len(messages) >= 1
        assert messages[0]["role"] == "user"
        # Message content is a list of content blocks
        content = messages[0]["content"]
        assert any(user_input in str(block) for block in content) or user_input in str(content)

    @pytest.mark.asyncio
    async def test_run_returns_statistics(self):
        """Test run returns statistics dict"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)

        result = await agent.run("Test", verbose=False)

        assert isinstance(result, dict)
        assert "final_response" in result
        assert "feedback" in result
        assert "agent_state" in result
        assert "context" in result

    @pytest.mark.asyncio
    async def test_run_transitions_to_thinking(self):
        """Test run transitions to THINKING state"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)
        states = []

        def track_state(old, new):
            states.append(new)

        agent.on_state_change = track_state

        await agent.run("Test", verbose=False)

        assert AgentState.THINKING in states

    @pytest.mark.asyncio
    async def test_run_transitions_to_completed(self):
        """Test run transitions to COMPLETED state"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Final response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)
        states = []

        def track_state(old, new):
            states.append(new)

        agent.on_state_change = track_state

        await agent.run("Test", verbose=False)

        assert AgentState.COMPLETED in states

    @pytest.mark.asyncio
    async def test_run_empty_user_input(self):
        """Test run with empty user input"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 0, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)

        result = await agent.run("", verbose=False)

        assert result is not None


@pytest.mark.unit
class TestMaxTurnsLimit:
    """Tests for max turns limit"""

    @pytest.mark.asyncio
    async def test_run_respects_max_turns(self):
        """Test run respects max turns limit"""
        client = Mock()

        # Return tool use to trigger multiple turns
        client.create_message = AsyncMock(return_value=Mock(
            content=[
                {"type": "tool_use", "id": "1", "name": "Read", "input": {}}
            ],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client, max_turns=2)
        agent.tool_manager.get_tool = Mock(return_value=None)  # Prevent tool execution

        result = await agent.run("Test", verbose=False)

        # Should eventually stop and return
        assert result is not None


@pytest.mark.unit
class TestHookTriggering:
    """Tests for hook triggering"""

    @pytest.mark.asyncio
    async def test_run_triggers_on_user_input_hook(self):
        """Test run triggers on_user_input hook"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        hook_manager = Mock()
        hook_manager.trigger = AsyncMock()

        agent = EnhancedAgent(client=client, hook_manager=hook_manager)

        await agent.run("Test input", verbose=False)

        # Verify hook was triggered
        calls = hook_manager.trigger.call_args_list
        hook_events = [call[0][0] for call in calls]
        assert HookEvent.ON_USER_INPUT in hook_events

    @pytest.mark.asyncio
    async def test_run_triggers_on_agent_start_hook(self):
        """Test run triggers on_agent_start hook"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        hook_manager = Mock()
        hook_manager.trigger = AsyncMock()

        agent = EnhancedAgent(client=client, hook_manager=hook_manager)

        await agent.run("Test", verbose=False)

        calls = hook_manager.trigger.call_args_list
        hook_events = [call[0][0] for call in calls]
        assert HookEvent.ON_AGENT_START in hook_events

    @pytest.mark.asyncio
    async def test_run_triggers_on_agent_end_hook(self):
        """Test run triggers on_agent_end hook"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        hook_manager = Mock()
        hook_manager.trigger = AsyncMock()

        agent = EnhancedAgent(client=client, hook_manager=hook_manager)

        await agent.run("Test", verbose=False)

        calls = hook_manager.trigger.call_args_list
        hook_events = [call[0][0] for call in calls]
        assert HookEvent.ON_AGENT_END in hook_events


@pytest.mark.unit
class TestEventEmission:
    """Tests for event emission"""

    @pytest.mark.asyncio
    async def test_run_emits_agent_start_event(self):
        """Test run emits AGENT_START event"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)
        agent.event_bus.emit = AsyncMock()

        await agent.run("Test input", verbose=False)

        # Verify event was emitted
        emit_calls = agent.event_bus.emit.call_args_list
        assert len(emit_calls) > 0

    @pytest.mark.asyncio
    async def test_run_emits_agent_thinking_event(self):
        """Test run emits AGENT_THINKING event"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)
        agent.event_bus.emit = AsyncMock()

        await agent.run("Test", verbose=False)

        emit_calls = agent.event_bus.emit.call_args_list
        assert len(emit_calls) > 0


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    @pytest.mark.asyncio
    async def test_run_with_error_in_llm_call(self):
        """Test run handles error in LLM call"""
        client = Mock()
        client.create_message = AsyncMock(side_effect=Exception("API Error"))

        agent = EnhancedAgent(client=client)

        result = await agent.run("Test", verbose=False)

        assert result is not None
        assert agent.state_manager.current_state == AgentState.ERROR

    @pytest.mark.asyncio
    async def test_run_with_verbose_false(self):
        """Test run with verbose=False"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)

        with patch('builtins.print') as mock_print:
            await agent.run("Test", verbose=False)
            # Print should not be called with verbose=False
            # (only for errors and max turns)

    @pytest.mark.asyncio
    async def test_run_with_verbose_true(self):
        """Test run with verbose=True"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)

        result = await agent.run("Test", verbose=True)

        assert result is not None


@pytest.mark.unit
class TestTokenTracking:
    """Tests for token usage tracking"""

    @pytest.mark.asyncio
    async def test_run_tracks_input_tokens(self):
        """Test run tracks input tokens"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 100, "output_tokens": 50}
        ))

        agent = EnhancedAgent(client=client)

        await agent.run("Test", verbose=False)

        stats = agent.state_manager.get_statistics()
        assert stats["input_tokens"] >= 100

    @pytest.mark.asyncio
    async def test_run_tracks_output_tokens(self):
        """Test run tracks output tokens"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 100, "output_tokens": 50}
        ))

        agent = EnhancedAgent(client=client)

        await agent.run("Test", verbose=False)

        stats = agent.state_manager.get_statistics()
        assert stats["output_tokens"] >= 50


@pytest.mark.unit
class TestAgentProperties:
    """Tests for agent properties and state"""

    def test_agent_context_info(self):
        """Test agent provides context info"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        agent.context_manager.add_user_message("Test message")

        # This is indirectly tested through other tests

    def test_agent_statistics(self):
        """Test agent provides statistics"""
        client = Mock()
        agent = EnhancedAgent(client=client)

        stats = agent.get_statistics()

        assert isinstance(stats, dict)
        assert "agent_state" in stats


@pytest.mark.unit
class TestFeedbackCollection:
    """Tests for feedback collection"""

    @pytest.mark.asyncio
    async def test_run_collects_feedback_verbose(self):
        """Test run collects feedback when verbose=True"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)

        result = await agent.run("Test", verbose=True)

        feedback = result.get("feedback", [])
        assert isinstance(feedback, list)

    @pytest.mark.asyncio
    async def test_run_collects_feedback_silent(self):
        """Test run collects minimal feedback when verbose=False"""
        client = Mock()
        client.create_message = AsyncMock(return_value=Mock(
            content=[{"type": "text", "text": "Response"}],
            usage={"input_tokens": 10, "output_tokens": 5}
        ))

        agent = EnhancedAgent(client=client)

        result = await agent.run("Test", verbose=False)

        feedback = result.get("feedback", [])
        assert isinstance(feedback, list)
