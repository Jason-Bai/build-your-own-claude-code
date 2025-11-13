"""
Integration tests for the hooks system with EnhancedAgent

Tests hook integration with the agent lifecycle
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from src.hooks import HookEvent, HookManager, HookContextBuilder
from src.agents.enhanced_agent import EnhancedAgent
from src.agents.state import AgentState
from src.agents.permission_manager import PermissionMode


@pytest.fixture
def mock_client():
    """Create a mock LLM client"""
    client = AsyncMock()
    client.create_message = AsyncMock()
    return client


@pytest.fixture
def hook_manager():
    """Create a HookManager instance"""
    return HookManager()


@pytest.fixture
def agent(mock_client, hook_manager):
    """Create an EnhancedAgent with mock client and hook manager"""
    return EnhancedAgent(
        client=mock_client,
        system_prompt="You are a helpful assistant.",
        max_turns=3,
        permission_mode=PermissionMode.AUTO_APPROVE_SAFE,
        hook_manager=hook_manager,
    )


class TestHooksIntegrationWithAgent:
    """Integration tests for hooks with EnhancedAgent"""

    @pytest.mark.asyncio
    async def test_agent_triggers_on_user_input_hook(self, agent, hook_manager, mock_client):
        """Test that agent triggers on_user_input hook"""
        hook_called = []

        async def user_input_hook(context):
            hook_called.append(("on_user_input", context.data.get("input")))

        hook_manager.register(HookEvent.ON_USER_INPUT, user_input_hook)

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "Hello!"}]
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_client.create_message.return_value = mock_response

        user_input = "What is 2+2?"
        await agent.run(user_input, verbose=False)

        assert len(hook_called) == 1
        assert hook_called[0][0] == "on_user_input"
        assert hook_called[0][1] == user_input

    @pytest.mark.asyncio
    async def test_agent_triggers_on_agent_start_hook(self, agent, hook_manager, mock_client):
        """Test that agent triggers on_agent_start hook"""
        hook_called = []

        async def agent_start_hook(context):
            hook_called.append("on_agent_start")

        hook_manager.register(HookEvent.ON_AGENT_START, agent_start_hook)

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "Hello!"}]
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_client.create_message.return_value = mock_response

        await agent.run("Hello", verbose=False)

        assert "on_agent_start" in hook_called

    @pytest.mark.asyncio
    async def test_agent_triggers_on_agent_end_hook(self, agent, hook_manager, mock_client):
        """Test that agent triggers on_agent_end hook"""
        hook_called = []

        async def agent_end_hook(context):
            hook_called.append(("on_agent_end", context.data.get("success")))

        hook_manager.register(HookEvent.ON_AGENT_END, agent_end_hook)

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "Hello!"}]
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_client.create_message.return_value = mock_response

        await agent.run("Hello", verbose=False)

        assert len(hook_called) == 1
        assert hook_called[0][0] == "on_agent_end"
        assert hook_called[0][1] is True

    @pytest.mark.asyncio
    async def test_agent_triggers_on_shutdown_hook(self, agent, hook_manager, mock_client):
        """Test that agent triggers on_shutdown hook"""
        hook_called = []

        async def shutdown_hook(context):
            hook_called.append(("on_shutdown", context.data.get("final_state")))

        hook_manager.register(HookEvent.ON_SHUTDOWN, shutdown_hook)

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "Hello!"}]
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_client.create_message.return_value = mock_response

        await agent.run("Hello", verbose=False)

        assert len(hook_called) == 1
        assert hook_called[0][0] == "on_shutdown"
        assert hook_called[0][1] == "completed"

    @pytest.mark.asyncio
    async def test_agent_triggers_on_error_hook_on_failure(self, agent, hook_manager, mock_client):
        """Test that agent triggers on_error hook when an error occurs"""
        hook_called = []

        async def error_hook(context):
            hook_called.append(("on_error", context.data.get("error_type")))

        hook_manager.register(HookEvent.ON_ERROR, error_hook)

        # Mock the LLM to raise an error
        mock_client.create_message.side_effect = Exception("Test error")

        await agent.run("Hello", verbose=False)

        assert any(hook[0] == "on_error" for hook in hook_called)

    @pytest.mark.asyncio
    async def test_agent_triggers_tool_selection_hooks(self, agent, hook_manager, mock_client):
        """Test that agent triggers tool-related hooks"""
        hook_called = []

        async def tool_select_hook(context):
            hook_called.append(("on_tool_select", context.data.get("tool_name")))

        async def tool_execute_hook(context):
            hook_called.append(("on_tool_execute", context.data.get("tool_name")))

        hook_manager.register(HookEvent.ON_TOOL_SELECT, tool_select_hook)
        hook_manager.register(HookEvent.ON_TOOL_EXECUTE, tool_execute_hook)

        # Mock the LLM response with a tool call
        mock_response = MagicMock()
        mock_response.content = [
            {"type": "text", "text": "Let me use a tool"},
            {
                "type": "tool_use",
                "id": "tool-1",
                "name": "Read",
                "input": {"file_path": "/test.txt"},
            },
        ]
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_client.create_message.return_value = mock_response

        # Mock the tool execution
        with patch.object(agent.tool_manager, "execute_tool") as mock_execute:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.output = "File content"
            mock_execute.return_value = mock_result

            # Mock permission check to approve
            with patch.object(
                agent.permission_manager, "request_permission"
            ) as mock_permission:
                mock_permission.return_value = (True, None)

                await agent.run("Read a file", verbose=False)

                # Check that tool hooks were triggered
                assert any(hook[0] == "on_tool_select" for hook in hook_called)
                assert any(hook[0] == "on_tool_execute" for hook in hook_called)

    @pytest.mark.asyncio
    async def test_hook_context_maintains_request_id_across_events(
        self, agent, hook_manager, mock_client
    ):
        """Test that hook context maintains request_id across events"""
        request_ids = []

        async def capture_request_id(context):
            request_ids.append(context.request_id)

        hook_manager.register(HookEvent.ON_USER_INPUT, capture_request_id)
        hook_manager.register(HookEvent.ON_AGENT_START, capture_request_id)
        hook_manager.register(HookEvent.ON_AGENT_END, capture_request_id)
        hook_manager.register(HookEvent.ON_SHUTDOWN, capture_request_id)

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "Hello!"}]
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_client.create_message.return_value = mock_response

        await agent.run("Hello", verbose=False)

        # All request_ids should be the same
        assert len(request_ids) > 0
        assert all(req_id == request_ids[0] for req_id in request_ids)

    @pytest.mark.asyncio
    async def test_multiple_handlers_for_same_event(self, agent, hook_manager, mock_client):
        """Test multiple handlers for the same event"""
        call_order = []

        async def handler1(context):
            call_order.append(1)

        async def handler2(context):
            call_order.append(2)

        async def handler3(context):
            call_order.append(3)

        hook_manager.register(HookEvent.ON_USER_INPUT, handler1, priority=1)
        hook_manager.register(HookEvent.ON_USER_INPUT, handler2, priority=3)
        hook_manager.register(HookEvent.ON_USER_INPUT, handler3, priority=2)

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "Hello!"}]
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_client.create_message.return_value = mock_response

        await agent.run("Hello", verbose=False)

        # Handlers should execute in priority order
        assert call_order == [2, 3, 1]

    @pytest.mark.asyncio
    async def test_hook_error_does_not_interrupt_agent(self, agent, hook_manager, mock_client):
        """Test that hook handler errors don't interrupt agent execution"""
        executed_hooks = []

        async def failing_hook(context):
            raise RuntimeError("Hook error")

        async def successful_hook(context):
            executed_hooks.append("success")

        hook_manager.register(HookEvent.ON_USER_INPUT, failing_hook, priority=10)
        hook_manager.register(HookEvent.ON_USER_INPUT, successful_hook, priority=1)

        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = [{"type": "text", "text": "Hello!"}]
        mock_response.usage = {"input_tokens": 10, "output_tokens": 5}
        mock_client.create_message.return_value = mock_response

        # Agent should complete successfully even with hook error
        result = await agent.run("Hello", verbose=False)

        assert result is not None
        assert agent.get_current_state() == AgentState.COMPLETED
        assert "success" in executed_hooks


class TestHookEventTypes:
    """Test that all important hook events are accessible"""

    def test_all_hook_events_defined(self):
        """Test that all hook events are properly defined"""
        expected_events = [
            HookEvent.ON_USER_INPUT,
            HookEvent.ON_AGENT_START,
            HookEvent.ON_AGENT_END,
            HookEvent.ON_ERROR,
            HookEvent.ON_SHUTDOWN,
            HookEvent.ON_TOOL_SELECT,
            HookEvent.ON_TOOL_EXECUTE,
            HookEvent.ON_TOOL_RESULT,
            HookEvent.ON_TOOL_ERROR,
            HookEvent.ON_PERMISSION_CHECK,
        ]

        for event in expected_events:
            assert isinstance(event, HookEvent)
            assert event.value is not None


class TestHookManagerStatistics:
    """Test hook manager statistics and introspection"""

    def test_hook_stats_tracking(self, hook_manager):
        """Test hook statistics tracking"""

        async def dummy_handler(context):
            pass

        hook_manager.register(HookEvent.ON_USER_INPUT, dummy_handler)
        hook_manager.register(HookEvent.ON_USER_INPUT, dummy_handler)
        hook_manager.register(HookEvent.ON_AGENT_START, dummy_handler)

        stats = hook_manager.get_stats()

        assert stats["user.input"] == 2
        assert stats["agent.start"] == 1
        assert len(stats) == 2
