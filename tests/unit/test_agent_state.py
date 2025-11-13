"""
Unit tests for Agent State Management

Tests AgentStateManager and AgentState classes covering:
- State transitions (FSM)
- Tool call recording and result updates
- Token tracking and statistics
- Turn management
- State reset functionality
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.agents.state import AgentState, ToolCall, AgentStateManager


@pytest.mark.unit
class TestAgentStateEnum:
    """Tests for AgentState enum"""

    def test_agent_state_idle_value(self):
        """Test IDLE state value"""
        assert AgentState.IDLE.value == "idle"

    def test_agent_state_thinking_value(self):
        """Test THINKING state value"""
        assert AgentState.THINKING.value == "thinking"

    def test_agent_state_using_tool_value(self):
        """Test USING_TOOL state value"""
        assert AgentState.USING_TOOL.value == "using_tool"

    def test_agent_state_waiting_for_result_value(self):
        """Test WAITING_FOR_RESULT state value"""
        assert AgentState.WAITING_FOR_RESULT.value == "waiting_for_result"

    def test_agent_state_completed_value(self):
        """Test COMPLETED state value"""
        assert AgentState.COMPLETED.value == "completed"

    def test_agent_state_error_value(self):
        """Test ERROR state value"""
        assert AgentState.ERROR.value == "error"

    def test_agent_state_all_states_exist(self):
        """Test all required states exist"""
        states = [s.value for s in AgentState]
        assert len(states) == 6
        assert "idle" in states
        assert "thinking" in states
        assert "using_tool" in states


@pytest.mark.unit
class TestToolCall:
    """Tests for ToolCall dataclass"""

    def test_tool_call_initialization(self):
        """Test creating a ToolCall"""
        call = ToolCall(
            id="call-123",
            name="read_file",
            input={"path": "/tmp/test.txt"}
        )
        assert call.id == "call-123"
        assert call.name == "read_file"
        assert call.input == {"path": "/tmp/test.txt"}
        assert call.status == "pending"
        assert call.result is None
        assert call.error is None

    def test_tool_call_with_result(self):
        """Test ToolCall with result set"""
        call = ToolCall(
            id="call-123",
            name="read_file",
            input={"path": "/tmp/test.txt"},
            result="File content"
        )
        assert call.result == "File content"
        assert call.error is None

    def test_tool_call_with_error(self):
        """Test ToolCall with error"""
        call = ToolCall(
            id="call-123",
            name="read_file",
            input={"path": "/tmp/test.txt"},
            error="File not found"
        )
        assert call.error == "File not found"
        assert call.result is None

    def test_tool_call_timestamp_created(self):
        """Test that ToolCall timestamp is set"""
        before = datetime.now()
        call = ToolCall(
            id="call-123",
            name="read_file",
            input={}
        )
        after = datetime.now()
        assert before <= call.timestamp <= after

    def test_tool_call_status_pending(self):
        """Test ToolCall default status is pending"""
        call = ToolCall(
            id="call-123",
            name="read_file",
            input={}
        )
        assert call.status == "pending"


@pytest.mark.unit
class TestAgentStateManagerInitialization:
    """Tests for AgentStateManager initialization"""

    def test_agent_state_manager_default_initialization(self):
        """Test default AgentStateManager initialization"""
        manager = AgentStateManager()
        assert manager.current_state == AgentState.IDLE
        assert manager.current_turn == 0
        assert manager.max_turns == 20
        assert manager.tool_calls == []
        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0
        assert manager.start_time is None
        assert manager.end_time is None

    def test_agent_state_manager_custom_max_turns(self):
        """Test AgentStateManager with custom max_turns"""
        manager = AgentStateManager(max_turns=50)
        assert manager.max_turns == 50

    def test_agent_state_manager_custom_initial_state(self):
        """Test AgentStateManager with custom initial state"""
        manager = AgentStateManager(current_state=AgentState.THINKING)
        assert manager.current_state == AgentState.THINKING


@pytest.mark.unit
class TestAgentStateTransitions:
    """Tests for state transitions"""

    def test_transition_from_idle_to_thinking(self):
        """Test transition from IDLE to THINKING"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        assert manager.current_state == AgentState.THINKING
        assert manager.start_time is not None

    def test_transition_from_thinking_to_using_tool(self):
        """Test transition from THINKING to USING_TOOL"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        start_time = manager.start_time

        manager.transition_to(AgentState.USING_TOOL)
        assert manager.current_state == AgentState.USING_TOOL
        assert manager.start_time == start_time  # Should not change

    def test_transition_from_using_tool_to_completed(self):
        """Test transition from USING_TOOL to COMPLETED"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.transition_to(AgentState.USING_TOOL)

        manager.transition_to(AgentState.COMPLETED)
        assert manager.current_state == AgentState.COMPLETED
        assert manager.end_time is not None

    def test_transition_to_error_sets_end_time(self):
        """Test that transitioning to ERROR sets end_time"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.transition_to(AgentState.ERROR)

        assert manager.current_state == AgentState.ERROR
        assert manager.end_time is not None

    def test_start_time_set_only_on_first_thinking(self):
        """Test that start_time is set only on first THINKING transition"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        first_start_time = manager.start_time

        manager.transition_to(AgentState.USING_TOOL)
        manager.transition_to(AgentState.THINKING)

        # Start time should not change
        assert manager.start_time == first_start_time

    def test_multiple_state_transitions(self):
        """Test a full workflow of state transitions"""
        manager = AgentStateManager()

        # IDLE -> THINKING
        manager.transition_to(AgentState.THINKING)
        assert manager.current_state == AgentState.THINKING

        # THINKING -> USING_TOOL
        manager.transition_to(AgentState.USING_TOOL)
        assert manager.current_state == AgentState.USING_TOOL

        # USING_TOOL -> COMPLETED
        manager.transition_to(AgentState.COMPLETED)
        assert manager.current_state == AgentState.COMPLETED
        assert manager.end_time is not None


@pytest.mark.unit
class TestToolCallRecording:
    """Tests for tool call recording"""

    def test_record_single_tool_call(self):
        """Test recording a single tool call"""
        manager = AgentStateManager()
        tool_call = ToolCall(
            id="call-1",
            name="read_file",
            input={"path": "/tmp/test.txt"}
        )

        manager.record_tool_call(tool_call)
        assert len(manager.tool_calls) == 1
        assert manager.tool_calls[0].id == "call-1"

    def test_record_multiple_tool_calls(self):
        """Test recording multiple tool calls"""
        manager = AgentStateManager()

        for i in range(5):
            call = ToolCall(
                id=f"call-{i}",
                name="tool",
                input={}
            )
            manager.record_tool_call(call)

        assert len(manager.tool_calls) == 5

    def test_tool_calls_maintain_order(self):
        """Test that tool calls maintain insertion order"""
        manager = AgentStateManager()

        call_ids = ["call-1", "call-2", "call-3"]
        for call_id in call_ids:
            call = ToolCall(id=call_id, name="tool", input={})
            manager.record_tool_call(call)

        recorded_ids = [c.id for c in manager.tool_calls]
        assert recorded_ids == call_ids

    def test_record_tool_call_preserves_metadata(self):
        """Test that recording preserves all tool call metadata"""
        manager = AgentStateManager()
        call = ToolCall(
            id="call-1",
            name="read_file",
            input={"path": "/tmp/test.txt"},
            result="content",
            status="completed"
        )

        manager.record_tool_call(call)
        recorded_call = manager.tool_calls[0]

        assert recorded_call.name == "read_file"
        assert recorded_call.input == {"path": "/tmp/test.txt"}
        assert recorded_call.result == "content"
        assert recorded_call.status == "completed"


@pytest.mark.unit
class TestToolCallResultUpdate:
    """Tests for updating tool call results"""

    def test_update_tool_call_result(self):
        """Test updating a tool call with result"""
        manager = AgentStateManager()
        call = ToolCall(id="call-1", name="read_file", input={})
        manager.record_tool_call(call)

        manager.update_tool_call_result("call-1", result="file content")

        assert manager.tool_calls[0].result == "file content"
        assert manager.tool_calls[0].status == "completed"
        assert manager.tool_calls[0].error is None

    def test_update_tool_call_error(self):
        """Test updating a tool call with error"""
        manager = AgentStateManager()
        call = ToolCall(id="call-1", name="read_file", input={})
        manager.record_tool_call(call)

        manager.update_tool_call_result("call-1", error="File not found")

        assert manager.tool_calls[0].error == "File not found"
        assert manager.tool_calls[0].status == "failed"
        assert manager.tool_calls[0].result is None

    def test_update_nonexistent_tool_call(self):
        """Test updating nonexistent tool call does nothing"""
        manager = AgentStateManager()

        # Should not raise error
        manager.update_tool_call_result("nonexistent-id", result="result")
        assert len(manager.tool_calls) == 0

    def test_update_specific_tool_call_among_many(self):
        """Test updating specific tool call among many"""
        manager = AgentStateManager()

        # Add 5 tool calls
        for i in range(5):
            call = ToolCall(id=f"call-{i}", name="tool", input={})
            manager.record_tool_call(call)

        # Update the middle one
        manager.update_tool_call_result("call-2", result="success")

        # Check that only call-2 was updated
        assert manager.tool_calls[2].result == "success"
        assert manager.tool_calls[2].status == "completed"
        assert manager.tool_calls[0].result is None
        assert manager.tool_calls[4].result is None


@pytest.mark.unit
class TestTurnManagement:
    """Tests for turn management"""

    def test_increment_turn_initial(self):
        """Test incrementing turn from initial state"""
        manager = AgentStateManager()
        exceeded = manager.increment_turn()

        assert manager.current_turn == 1
        assert exceeded is False

    def test_increment_turn_multiple(self):
        """Test incrementing turn multiple times"""
        manager = AgentStateManager()

        for i in range(1, 11):
            exceeded = manager.increment_turn()
            assert manager.current_turn == i
            assert exceeded is False

    def test_increment_turn_reaches_max(self):
        """Test incrementing turn reaches max limit"""
        manager = AgentStateManager(max_turns=5)

        for i in range(1, 6):
            exceeded = manager.increment_turn()
            if i < 5:
                assert exceeded is False
            else:
                assert exceeded is True

    def test_increment_turn_exceeds_max(self):
        """Test incrementing turn exceeds max limit"""
        manager = AgentStateManager(max_turns=5)

        # Reach exactly max
        for _ in range(5):
            manager.increment_turn()

        assert manager.current_turn == 5

        # Try to exceed
        manager.increment_turn()
        assert manager.current_turn == 6

    def test_turn_counter_starts_at_zero(self):
        """Test that turn counter starts at 0"""
        manager = AgentStateManager()
        assert manager.current_turn == 0


@pytest.mark.unit
class TestTokenTracking:
    """Tests for token tracking"""

    def test_add_tokens_initial(self):
        """Test adding tokens to fresh manager"""
        manager = AgentStateManager()
        manager.add_tokens(100, 50)

        assert manager.total_input_tokens == 100
        assert manager.total_output_tokens == 50

    def test_add_tokens_multiple(self):
        """Test adding tokens multiple times"""
        manager = AgentStateManager()

        manager.add_tokens(100, 50)
        manager.add_tokens(200, 100)

        assert manager.total_input_tokens == 300
        assert manager.total_output_tokens == 150

    def test_add_zero_tokens(self):
        """Test adding zero tokens"""
        manager = AgentStateManager()
        manager.add_tokens(0, 0)

        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0

    def test_add_large_token_counts(self):
        """Test adding large token counts"""
        manager = AgentStateManager()
        manager.add_tokens(100000, 50000)

        assert manager.total_input_tokens == 100000
        assert manager.total_output_tokens == 50000


@pytest.mark.unit
class TestStatisticsGeneration:
    """Tests for statistics generation"""

    def test_get_statistics_fresh_manager(self):
        """Test statistics from fresh manager"""
        manager = AgentStateManager()
        stats = manager.get_statistics()

        assert stats["state"] == "idle"
        assert stats["turns"] == 0
        assert stats["tool_calls"] == 0
        assert stats["successful_calls"] == 0
        assert stats["failed_calls"] == 0
        assert stats["input_tokens"] == 0
        assert stats["output_tokens"] == 0
        assert stats["total_tokens"] == 0
        assert stats["duration_seconds"] is None

    def test_get_statistics_with_tokens(self):
        """Test statistics with token data"""
        manager = AgentStateManager()
        manager.add_tokens(1000, 500)
        stats = manager.get_statistics()

        assert stats["input_tokens"] == 1000
        assert stats["output_tokens"] == 500
        assert stats["total_tokens"] == 1500

    def test_get_statistics_with_tool_calls(self):
        """Test statistics with tool calls"""
        manager = AgentStateManager()

        # Add successful calls
        for i in range(3):
            call = ToolCall(id=f"call-{i}", name="tool", input={}, status="completed")
            manager.record_tool_call(call)

        # Add failed calls
        for i in range(3, 5):
            call = ToolCall(id=f"call-{i}", name="tool", input={}, status="failed")
            manager.record_tool_call(call)

        stats = manager.get_statistics()
        assert stats["tool_calls"] == 5
        assert stats["successful_calls"] == 3
        assert stats["failed_calls"] == 2

    def test_get_statistics_with_duration(self):
        """Test statistics includes duration"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)

        # Mock time passage
        manager.start_time = datetime.now() - timedelta(seconds=5)
        manager.transition_to(AgentState.COMPLETED)

        stats = manager.get_statistics()
        assert stats["duration_seconds"] is not None
        assert stats["duration_seconds"] >= 5

    def test_get_statistics_with_turns(self):
        """Test statistics includes turns"""
        manager = AgentStateManager()

        for _ in range(5):
            manager.increment_turn()

        stats = manager.get_statistics()
        assert stats["turns"] == 5

    def test_get_statistics_state_reflects_current(self):
        """Test statistics state reflects current state"""
        manager = AgentStateManager()

        manager.transition_to(AgentState.THINKING)
        stats = manager.get_statistics()
        assert stats["state"] == "thinking"

        manager.transition_to(AgentState.USING_TOOL)
        stats = manager.get_statistics()
        assert stats["state"] == "using_tool"


@pytest.mark.unit
class TestStateReset:
    """Tests for state reset functionality"""

    def test_reset_clears_state(self):
        """Test reset returns to IDLE state"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.reset()

        assert manager.current_state == AgentState.IDLE

    def test_reset_clears_turns(self):
        """Test reset clears turn counter"""
        manager = AgentStateManager()
        manager.increment_turn()
        manager.increment_turn()
        manager.reset()

        assert manager.current_turn == 0

    def test_reset_clears_tool_calls(self):
        """Test reset clears tool calls"""
        manager = AgentStateManager()
        manager.record_tool_call(ToolCall(id="call-1", name="tool", input={}))
        manager.reset()

        assert len(manager.tool_calls) == 0

    def test_reset_clears_tokens(self):
        """Test reset clears token counts"""
        manager = AgentStateManager()
        manager.add_tokens(1000, 500)
        manager.reset()

        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0

    def test_reset_clears_timestamps(self):
        """Test reset clears start and end times"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.transition_to(AgentState.COMPLETED)
        manager.reset()

        assert manager.start_time is None
        assert manager.end_time is None

    def test_reset_complete_cleanup(self):
        """Test reset completely cleans up manager state"""
        manager = AgentStateManager()

        # Use all features
        manager.transition_to(AgentState.THINKING)
        manager.record_tool_call(ToolCall(id="call-1", name="tool", input={}))
        manager.add_tokens(1000, 500)
        manager.increment_turn()
        manager.transition_to(AgentState.COMPLETED)

        # Reset
        manager.reset()

        # Verify all cleaned up
        fresh_manager = AgentStateManager()
        assert manager.current_state == fresh_manager.current_state
        assert manager.current_turn == fresh_manager.current_turn
        assert manager.tool_calls == fresh_manager.tool_calls
        assert manager.total_input_tokens == fresh_manager.total_input_tokens
        assert manager.total_output_tokens == fresh_manager.total_output_tokens
        assert manager.start_time == fresh_manager.start_time
        assert manager.end_time == fresh_manager.end_time


@pytest.mark.unit
class TestCompleteWorkflow:
    """Tests for complete agent workflows"""

    def test_simple_workflow(self):
        """Test a simple complete workflow"""
        manager = AgentStateManager()

        # Start
        manager.transition_to(AgentState.THINKING)
        manager.increment_turn()

        # Use tool
        manager.transition_to(AgentState.USING_TOOL)
        tool_call = ToolCall(id="call-1", name="read_file", input={})
        manager.record_tool_call(tool_call)

        # Tool result
        manager.update_tool_call_result("call-1", result="content")

        # Complete
        manager.add_tokens(100, 50)
        manager.transition_to(AgentState.COMPLETED)

        # Verify final state
        stats = manager.get_statistics()
        assert stats["state"] == "completed"
        assert stats["turns"] == 1
        assert stats["tool_calls"] == 1
        assert stats["successful_calls"] == 1
        assert stats["total_tokens"] == 150

    def test_multi_turn_workflow(self):
        """Test a multi-turn workflow"""
        manager = AgentStateManager(max_turns=5)

        for turn in range(1, 6):
            manager.transition_to(AgentState.THINKING)
            manager.increment_turn()

            # Tool call
            tool_call = ToolCall(id=f"call-{turn}", name="tool", input={})
            manager.record_tool_call(tool_call)
            manager.update_tool_call_result(f"call-{turn}", result="result")

            manager.add_tokens(100, 50)

            if turn == 5:
                manager.transition_to(AgentState.COMPLETED)

        stats = manager.get_statistics()
        assert stats["turns"] == 5
        assert stats["tool_calls"] == 5
        assert stats["total_tokens"] == 750  # 5 turns * 150 tokens

    def test_error_workflow(self):
        """Test a workflow that encounters error"""
        manager = AgentStateManager()

        manager.transition_to(AgentState.THINKING)
        manager.increment_turn()

        tool_call = ToolCall(id="call-1", name="tool", input={})
        manager.record_tool_call(tool_call)
        manager.update_tool_call_result("call-1", error="Tool failed")

        manager.transition_to(AgentState.ERROR)

        stats = manager.get_statistics()
        assert stats["state"] == "error"
        assert stats["failed_calls"] == 1
        assert stats["duration_seconds"] is not None  # end_time is set, duration calculated
