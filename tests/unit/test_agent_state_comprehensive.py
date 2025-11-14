"""
Unit tests for Agent State Management

Tests state transitions, state tracking, tool call recording, and statistics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from src.agents.state import AgentState, ToolCall, AgentStateManager


@pytest.mark.unit
class TestAgentStateEnum:
    """Tests for AgentState enum"""

    def test_agent_state_values(self):
        """Test AgentState enum values"""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.THINKING.value == "thinking"
        assert AgentState.USING_TOOL.value == "using_tool"
        assert AgentState.WAITING_FOR_RESULT.value == "waiting_for_result"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.ERROR.value == "error"

    def test_agent_state_count(self):
        """Test that all expected states exist"""
        expected_states = {"IDLE", "THINKING", "USING_TOOL", "WAITING_FOR_RESULT", "COMPLETED", "ERROR"}
        actual_states = {state.name for state in AgentState}
        assert expected_states == actual_states


@pytest.mark.unit
class TestToolCall:
    """Tests for ToolCall dataclass"""

    def test_tool_call_creation(self):
        """Test ToolCall creation with required fields"""
        tool_call = ToolCall(
            id="tool_123",
            name="bash",
            input={"command": "ls"}
        )
        assert tool_call.id == "tool_123"
        assert tool_call.name == "bash"
        assert tool_call.input == {"command": "ls"}
        assert tool_call.status == "pending"

    def test_tool_call_with_timestamp(self):
        """Test ToolCall includes timestamp"""
        tool_call = ToolCall(
            id="tool_456",
            name="read",
            input={"file_path": "/etc/hosts"}
        )
        assert tool_call.timestamp is not None
        assert isinstance(tool_call.timestamp, datetime)

    def test_tool_call_result_fields(self):
        """Test ToolCall result and error fields"""
        tool_call = ToolCall(
            id="tool_789",
            name="write",
            input={"file_path": "test.txt", "content": "test"}
        )
        assert tool_call.result is None
        assert tool_call.error is None

    def test_tool_call_with_result(self):
        """Test ToolCall with result"""
        tool_call = ToolCall(
            id="tool_001",
            name="bash",
            input={"command": "pwd"},
            result="/home/user",
            status="completed"
        )
        assert tool_call.result == "/home/user"
        assert tool_call.status == "completed"

    def test_tool_call_with_error(self):
        """Test ToolCall with error"""
        tool_call = ToolCall(
            id="tool_002",
            name="bash",
            input={"command": "invalid_cmd"},
            error="Command not found",
            status="failed"
        )
        assert tool_call.error == "Command not found"
        assert tool_call.status == "failed"


@pytest.mark.unit
class TestAgentStateManagerInitialization:
    """Tests for AgentStateManager initialization"""

    def test_initialization_with_defaults(self):
        """Test AgentStateManager initialization with defaults"""
        manager = AgentStateManager()
        assert manager.current_state == AgentState.IDLE
        assert manager.current_turn == 0
        assert manager.max_turns == 20
        assert len(manager.tool_calls) == 0
        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0
        assert manager.start_time is None
        assert manager.end_time is None

    def test_initialization_with_custom_max_turns(self):
        """Test initialization with custom max_turns"""
        manager = AgentStateManager(max_turns=50)
        assert manager.max_turns == 50

    def test_initialization_with_initial_state(self):
        """Test initialization with custom initial state"""
        manager = AgentStateManager(current_state=AgentState.THINKING)
        assert manager.current_state == AgentState.THINKING


@pytest.mark.unit
class TestStateTransitions:
    """Tests for state transitions"""

    def test_transition_to_valid_state(self):
        """Test transitioning to valid state"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        assert manager.current_state == AgentState.THINKING

    def test_transition_multiple_states(self):
        """Test multiple state transitions"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        assert manager.current_state == AgentState.THINKING

        manager.transition_to(AgentState.USING_TOOL)
        assert manager.current_state == AgentState.USING_TOOL

        manager.transition_to(AgentState.COMPLETED)
        assert manager.current_state == AgentState.COMPLETED

    def test_transition_sets_start_time_on_thinking(self):
        """Test that start_time is set when transitioning to THINKING"""
        manager = AgentStateManager()
        assert manager.start_time is None

        manager.transition_to(AgentState.THINKING)
        assert manager.start_time is not None

    def test_transition_sets_end_time_on_completed(self):
        """Test that end_time is set when transitioning to COMPLETED"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        start = manager.start_time

        manager.transition_to(AgentState.COMPLETED)
        assert manager.end_time is not None
        assert manager.end_time >= start

    def test_transition_sets_end_time_on_error(self):
        """Test that end_time is set when transitioning to ERROR"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.transition_to(AgentState.ERROR)
        assert manager.end_time is not None

    def test_transition_does_not_reset_start_time(self):
        """Test that start_time is not reset on subsequent THINKING transitions"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        first_start = manager.start_time

        manager.transition_to(AgentState.USING_TOOL)
        manager.transition_to(AgentState.THINKING)
        assert manager.start_time == first_start


@pytest.mark.unit
class TestToolCallRecording:
    """Tests for tool call recording"""

    def test_record_single_tool_call(self):
        """Test recording a single tool call"""
        manager = AgentStateManager()
        tool_call = ToolCall(
            id="tool_1",
            name="bash",
            input={"command": "ls"}
        )
        manager.record_tool_call(tool_call)

        assert len(manager.tool_calls) == 1
        assert manager.tool_calls[0].id == "tool_1"

    def test_record_multiple_tool_calls(self):
        """Test recording multiple tool calls"""
        manager = AgentStateManager()
        for i in range(3):
            tool_call = ToolCall(
                id=f"tool_{i}",
                name="bash",
                input={"command": f"cmd_{i}"}
            )
            manager.record_tool_call(tool_call)

        assert len(manager.tool_calls) == 3

    def test_tool_calls_maintain_order(self):
        """Test that tool calls maintain insertion order"""
        manager = AgentStateManager()
        names = ["bash", "read", "write"]
        for i, name in enumerate(names):
            tool_call = ToolCall(
                id=f"tool_{i}",
                name=name,
                input={}
            )
            manager.record_tool_call(tool_call)

        assert [tc.name for tc in manager.tool_calls] == names


@pytest.mark.unit
class TestToolCallUpdates:
    """Tests for tool call result updates"""

    def test_update_tool_call_with_result(self):
        """Test updating tool call with result"""
        manager = AgentStateManager()
        tool_call = ToolCall(
            id="tool_1",
            name="bash",
            input={"command": "pwd"}
        )
        manager.record_tool_call(tool_call)

        manager.update_tool_call_result("tool_1", result="/home/user")

        assert manager.tool_calls[0].result == "/home/user"
        assert manager.tool_calls[0].status == "completed"

    def test_update_tool_call_with_error(self):
        """Test updating tool call with error"""
        manager = AgentStateManager()
        tool_call = ToolCall(
            id="tool_2",
            name="read",
            input={"file_path": "nonexistent.txt"}
        )
        manager.record_tool_call(tool_call)

        manager.update_tool_call_result("tool_2", error="File not found")

        assert manager.tool_calls[0].error == "File not found"
        assert manager.tool_calls[0].status == "failed"

    def test_update_nonexistent_tool_call(self):
        """Test updating tool call that doesn't exist"""
        manager = AgentStateManager()
        # Should not raise error
        manager.update_tool_call_result("nonexistent", result="test")
        assert len(manager.tool_calls) == 0


@pytest.mark.unit
class TestTurnIncrement:
    """Tests for turn incrementing"""

    def test_increment_turn(self):
        """Test incrementing turn"""
        manager = AgentStateManager()
        assert manager.current_turn == 0

        manager.increment_turn()
        assert manager.current_turn == 1

    def test_increment_turn_multiple_times(self):
        """Test incrementing turn multiple times"""
        manager = AgentStateManager()
        for i in range(1, 6):
            manager.increment_turn()
            assert manager.current_turn == i

    def test_increment_turn_returns_false_below_max(self):
        """Test that increment_turn returns False below max"""
        manager = AgentStateManager(max_turns=5)
        for i in range(4):
            result = manager.increment_turn()
            assert result is False

    def test_increment_turn_returns_true_at_max(self):
        """Test that increment_turn returns True at max"""
        manager = AgentStateManager(max_turns=3)
        manager.increment_turn()  # turn = 1
        manager.increment_turn()  # turn = 2
        result = manager.increment_turn()  # turn = 3, should return True
        assert result is True

    def test_increment_turn_respects_max_turns(self):
        """Test that max_turns is compared correctly"""
        manager = AgentStateManager(max_turns=2)
        assert manager.increment_turn() is False  # turn = 1
        assert manager.increment_turn() is True   # turn = 2


@pytest.mark.unit
class TestTokenCounting:
    """Tests for token counting"""

    def test_add_tokens(self):
        """Test adding tokens"""
        manager = AgentStateManager()
        manager.add_tokens(input_tokens=10, output_tokens=5)

        assert manager.total_input_tokens == 10
        assert manager.total_output_tokens == 5

    def test_add_multiple_token_counts(self):
        """Test adding tokens multiple times"""
        manager = AgentStateManager()
        manager.add_tokens(10, 5)
        manager.add_tokens(20, 15)
        manager.add_tokens(5, 3)

        assert manager.total_input_tokens == 35
        assert manager.total_output_tokens == 23

    def test_add_zero_tokens(self):
        """Test adding zero tokens"""
        manager = AgentStateManager()
        manager.add_tokens(0, 0)
        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0


@pytest.mark.unit
class TestStatistics:
    """Tests for statistics generation"""

    def test_get_statistics_initial(self):
        """Test initial statistics"""
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

    def test_get_statistics_with_data(self):
        """Test statistics with data"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.add_tokens(100, 50)

        for i in range(3):
            tool_call = ToolCall(id=f"tool_{i}", name="bash", input={})
            manager.record_tool_call(tool_call)

        manager.tool_calls[0].status = "completed"
        manager.tool_calls[1].status = "completed"
        manager.tool_calls[2].status = "failed"

        manager.increment_turn()
        manager.transition_to(AgentState.COMPLETED)

        stats = manager.get_statistics()
        assert stats["state"] == "completed"
        assert stats["turns"] == 1
        assert stats["tool_calls"] == 3
        assert stats["successful_calls"] == 2
        assert stats["failed_calls"] == 1
        assert stats["input_tokens"] == 100
        assert stats["output_tokens"] == 50
        assert stats["total_tokens"] == 150
        assert stats["duration_seconds"] is not None

    def test_get_statistics_duration(self):
        """Test duration calculation"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.transition_to(AgentState.COMPLETED)

        stats = manager.get_statistics()
        assert stats["duration_seconds"] is not None
        assert stats["duration_seconds"] >= 0


@pytest.mark.unit
class TestReset:
    """Tests for reset functionality"""

    def test_reset_clears_state(self):
        """Test reset clears state"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.add_tokens(100, 50)
        manager.increment_turn()

        manager.reset()

        assert manager.current_state == AgentState.IDLE
        assert manager.current_turn == 0
        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0

    def test_reset_clears_tool_calls(self):
        """Test reset clears tool calls"""
        manager = AgentStateManager()
        tool_call = ToolCall(id="tool_1", name="bash", input={})
        manager.record_tool_call(tool_call)

        manager.reset()
        assert len(manager.tool_calls) == 0

    def test_reset_clears_times(self):
        """Test reset clears times"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.transition_to(AgentState.COMPLETED)

        manager.reset()
        assert manager.start_time is None
        assert manager.end_time is None

    def test_reset_allows_reuse(self):
        """Test that manager can be reused after reset"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        manager.add_tokens(100, 50)

        manager.reset()

        # Should be able to use again
        manager.transition_to(AgentState.THINKING)
        manager.add_tokens(10, 5)

        assert manager.current_state == AgentState.THINKING
        assert manager.total_input_tokens == 10
