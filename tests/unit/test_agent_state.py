"""
Unit tests for Agent State Management

Tests state transitions, tool call recording, and statistics tracking.
"""

import pytest
from datetime import datetime, timedelta
from src.agents.state import AgentState, ToolCall, AgentStateManager


@pytest.mark.unit
class TestAgentState:
    """Tests for AgentState enum"""

    def test_agent_state_values(self):
        """Test all agent state values"""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.THINKING.value == "thinking"
        assert AgentState.USING_TOOL.value == "using_tool"
        assert AgentState.WAITING_FOR_RESULT.value == "waiting_for_result"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.ERROR.value == "error"

    def test_agent_state_enum_members(self):
        """Test that all expected states exist"""
        states = {AgentState.IDLE, AgentState.THINKING, AgentState.USING_TOOL,
                  AgentState.WAITING_FOR_RESULT, AgentState.COMPLETED, AgentState.ERROR}
        assert len(states) == 6


@pytest.mark.unit
class TestToolCall:
    """Tests for ToolCall dataclass"""

    def test_tool_call_creation_minimal(self):
        """Test creating ToolCall with minimal parameters"""
        tool_call = ToolCall(id="tool_1", name="bash", input={"command": "ls"})

        assert tool_call.id == "tool_1"
        assert tool_call.name == "bash"
        assert tool_call.input == {"command": "ls"}
        assert tool_call.status == "pending"
        assert tool_call.result is None
        assert tool_call.error is None

    def test_tool_call_creation_with_timestamp(self):
        """Test that ToolCall has timestamp"""
        tool_call = ToolCall(id="tool_1", name="read", input={"file": "test.txt"})

        assert tool_call.timestamp is not None
        assert isinstance(tool_call.timestamp, datetime)

    def test_tool_call_creation_with_result(self):
        """Test creating ToolCall with result"""
        tool_call = ToolCall(
            id="tool_1",
            name="read",
            input={"file": "test.txt"},
            result="file contents",
            status="completed"
        )

        assert tool_call.result == "file contents"
        assert tool_call.status == "completed"

    def test_tool_call_creation_with_error(self):
        """Test creating ToolCall with error"""
        tool_call = ToolCall(
            id="tool_1",
            name="read",
            input={"file": "nonexistent.txt"},
            error="File not found",
            status="failed"
        )

        assert tool_call.error == "File not found"
        assert tool_call.status == "failed"


@pytest.mark.unit
class TestAgentStateManagerInitialization:
    """Tests for AgentStateManager initialization"""

    def test_state_manager_default_initialization(self):
        """Test default initialization"""
        manager = AgentStateManager()

        assert manager.current_state == AgentState.IDLE
        assert manager.current_turn == 0
        assert manager.max_turns == 20
        assert manager.tool_calls == []
        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0
        assert manager.start_time is None
        assert manager.end_time is None

    def test_state_manager_custom_max_turns(self):
        """Test initialization with custom max_turns"""
        manager = AgentStateManager(max_turns=10)

        assert manager.max_turns == 10

    def test_state_manager_initial_state(self):
        """Test that initial state is IDLE"""
        manager = AgentStateManager()

        assert manager.current_state == AgentState.IDLE


@pytest.mark.unit
class TestAgentStateManagerStateTransition:
    """Tests for state transitions"""

    def test_transition_to_thinking_sets_start_time(self):
        """Test that transitioning to THINKING sets start_time"""
        manager = AgentStateManager()
        assert manager.start_time is None

        manager.transition_to(AgentState.THINKING)

        assert manager.current_state == AgentState.THINKING
        assert manager.start_time is not None

    def test_transition_to_thinking_only_sets_start_time_once(self):
        """Test that start_time is only set on first THINKING transition"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)
        first_start_time = manager.start_time

        manager.transition_to(AgentState.USING_TOOL)
        manager.transition_to(AgentState.THINKING)

        # Start time should not change on second THINKING transition
        assert manager.start_time == first_start_time

    def test_transition_to_completed_sets_end_time(self):
        """Test that transitioning to COMPLETED sets end_time"""
        manager = AgentStateManager()
        manager.transition_to(AgentState.THINKING)

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

    def test_transition_sequence(self):
        """Test typical state transition sequence"""
        manager = AgentStateManager()

        manager.transition_to(AgentState.THINKING)
        assert manager.current_state == AgentState.THINKING

        manager.transition_to(AgentState.USING_TOOL)
        assert manager.current_state == AgentState.USING_TOOL

        manager.transition_to(AgentState.THINKING)
        assert manager.current_state == AgentState.THINKING

        manager.transition_to(AgentState.COMPLETED)
        assert manager.current_state == AgentState.COMPLETED


@pytest.mark.unit
class TestAgentStateManagerToolCalls:
    """Tests for tool call recording and management"""

    def test_record_tool_call(self):
        """Test recording a tool call"""
        manager = AgentStateManager()
        tool_call = ToolCall(id="tool_1", name="bash", input={"command": "ls"})

        manager.record_tool_call(tool_call)

        assert len(manager.tool_calls) == 1
        assert manager.tool_calls[0] == tool_call

    def test_record_multiple_tool_calls(self):
        """Test recording multiple tool calls"""
        manager = AgentStateManager()

        manager.record_tool_call(ToolCall(id="tool_1", name="bash", input={"command": "ls"}))
        manager.record_tool_call(ToolCall(id="tool_2", name="read", input={"file": "test.txt"}))
        manager.record_tool_call(ToolCall(id="tool_3", name="write", input={"file": "out.txt"}))

        assert len(manager.tool_calls) == 3

    def test_update_tool_call_result_success(self):
        """Test updating tool call result on success"""
        manager = AgentStateManager()
        tool_call = ToolCall(id="tool_1", name="bash", input={"command": "ls"})
        manager.record_tool_call(tool_call)

        manager.update_tool_call_result("tool_1", result="output data")

        assert manager.tool_calls[0].result == "output data"
        assert manager.tool_calls[0].error is None
        assert manager.tool_calls[0].status == "completed"

    def test_update_tool_call_result_error(self):
        """Test updating tool call result on error"""
        manager = AgentStateManager()
        tool_call = ToolCall(id="tool_1", name="read", input={"file": "nonexistent.txt"})
        manager.record_tool_call(tool_call)

        manager.update_tool_call_result("tool_1", error="File not found")

        assert manager.tool_calls[0].result is None
        assert manager.tool_calls[0].error == "File not found"
        assert manager.tool_calls[0].status == "failed"

    def test_update_nonexistent_tool_call(self):
        """Test updating nonexistent tool call (should do nothing)"""
        manager = AgentStateManager()

        manager.update_tool_call_result("nonexistent_id", result="data")

        assert len(manager.tool_calls) == 0


@pytest.mark.unit
class TestAgentStateManagerTurns:
    """Tests for turn management"""

    def test_increment_turn_initial(self):
        """Test incrementing turn from initial state"""
        manager = AgentStateManager(max_turns=20)

        result = manager.increment_turn()

        assert manager.current_turn == 1
        assert result is False  # Not exceeded yet

    def test_increment_turn_multiple(self):
        """Test incrementing turn multiple times"""
        manager = AgentStateManager(max_turns=5)

        for i in range(4):
            result = manager.increment_turn()
            assert result is False

        result = manager.increment_turn()
        assert manager.current_turn == 5
        assert result is True  # Exceeded max_turns

    def test_increment_turn_exceeds_limit(self):
        """Test that increment returns True when exceeding limit"""
        manager = AgentStateManager(max_turns=2)

        manager.increment_turn()  # 1
        manager.increment_turn()  # 2
        result = manager.increment_turn()  # 3

        assert result is True


@pytest.mark.unit
class TestAgentStateManagerTokens:
    """Tests for token counting"""

    def test_add_tokens(self):
        """Test adding tokens"""
        manager = AgentStateManager()

        manager.add_tokens(10, 20)

        assert manager.total_input_tokens == 10
        assert manager.total_output_tokens == 20

    def test_add_tokens_multiple(self):
        """Test adding tokens multiple times"""
        manager = AgentStateManager()

        manager.add_tokens(10, 20)
        manager.add_tokens(15, 25)
        manager.add_tokens(5, 10)

        assert manager.total_input_tokens == 30
        assert manager.total_output_tokens == 55

    def test_add_tokens_zero(self):
        """Test adding zero tokens"""
        manager = AgentStateManager()

        manager.add_tokens(0, 0)

        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0


@pytest.mark.unit
class TestAgentStateManagerStatistics:
    """Tests for statistics retrieval"""

    def test_get_statistics_initial(self):
        """Test getting statistics in initial state"""
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

    def test_get_statistics_with_tool_calls(self):
        """Test statistics with tool calls"""
        manager = AgentStateManager()

        manager.record_tool_call(ToolCall(id="tool_1", name="bash", input={}, status="completed"))
        manager.record_tool_call(ToolCall(id="tool_2", name="read", input={}, status="failed"))

        stats = manager.get_statistics()

        assert stats["tool_calls"] == 2
        assert stats["successful_calls"] == 1
        assert stats["failed_calls"] == 1

    def test_get_statistics_with_tokens(self):
        """Test statistics with tokens"""
        manager = AgentStateManager()

        manager.add_tokens(100, 200)

        stats = manager.get_statistics()

        assert stats["input_tokens"] == 100
        assert stats["output_tokens"] == 200
        assert stats["total_tokens"] == 300

    def test_get_statistics_with_duration(self):
        """Test statistics with duration"""
        manager = AgentStateManager()

        manager.transition_to(AgentState.THINKING)
        manager.transition_to(AgentState.COMPLETED)

        stats = manager.get_statistics()

        assert stats["duration_seconds"] is not None
        assert stats["duration_seconds"] >= 0

    def test_get_statistics_complete_workflow(self):
        """Test statistics with complete workflow"""
        manager = AgentStateManager(max_turns=5)

        manager.transition_to(AgentState.THINKING)
        manager.increment_turn()
        manager.record_tool_call(ToolCall(id="tool_1", name="bash", input={}))
        manager.update_tool_call_result("tool_1", result="output")
        manager.add_tokens(50, 100)
        manager.transition_to(AgentState.COMPLETED)

        stats = manager.get_statistics()

        assert stats["state"] == "completed"
        assert stats["turns"] == 1
        assert stats["tool_calls"] == 1
        assert stats["successful_calls"] == 1
        assert stats["failed_calls"] == 0
        assert stats["input_tokens"] == 50
        assert stats["output_tokens"] == 100
        assert stats["total_tokens"] == 150
        assert stats["duration_seconds"] is not None


@pytest.mark.unit
class TestAgentStateManagerReset:
    """Tests for state reset"""

    def test_reset_clears_state(self):
        """Test that reset clears state"""
        manager = AgentStateManager()

        manager.transition_to(AgentState.THINKING)
        manager.current_turn = 5
        manager.record_tool_call(ToolCall(id="tool_1", name="bash", input={}))
        manager.add_tokens(100, 200)

        manager.reset()

        assert manager.current_state == AgentState.IDLE
        assert manager.current_turn == 0
        assert len(manager.tool_calls) == 0
        assert manager.total_input_tokens == 0
        assert manager.total_output_tokens == 0
        assert manager.start_time is None
        assert manager.end_time is None

    def test_reset_preserves_max_turns(self):
        """Test that reset preserves max_turns"""
        manager = AgentStateManager(max_turns=10)

        manager.transition_to(AgentState.THINKING)
        manager.reset()

        assert manager.max_turns == 10

    def test_reset_allows_reuse(self):
        """Test that manager can be reused after reset"""
        manager = AgentStateManager()

        # First workflow
        manager.transition_to(AgentState.THINKING)
        manager.transition_to(AgentState.COMPLETED)

        manager.reset()

        # Second workflow
        manager.transition_to(AgentState.THINKING)
        manager.record_tool_call(ToolCall(id="tool_1", name="bash", input={}))

        assert manager.current_state == AgentState.THINKING
        assert len(manager.tool_calls) == 1


@pytest.mark.unit
class TestAgentStateManagerIntegration:
    """Integration tests for state manager"""

    def test_typical_agent_workflow(self):
        """Test typical agent workflow"""
        manager = AgentStateManager()

        # Initial state
        assert manager.current_state == AgentState.IDLE

        # Start thinking
        manager.transition_to(AgentState.THINKING)
        assert manager.start_time is not None

        # Use tool
        manager.transition_to(AgentState.USING_TOOL)
        manager.record_tool_call(ToolCall(id="tool_1", name="bash", input={"command": "ls"}))

        # Continue thinking
        manager.increment_turn()
        manager.transition_to(AgentState.THINKING)

        # Complete
        manager.transition_to(AgentState.COMPLETED)
        manager.add_tokens(100, 150)

        # Check final stats
        stats = manager.get_statistics()
        assert stats["state"] == "completed"
        assert stats["turns"] == 1
        assert stats["tool_calls"] == 1
        assert stats["total_tokens"] == 250

    def test_error_workflow(self):
        """Test error workflow"""
        manager = AgentStateManager()

        manager.transition_to(AgentState.THINKING)
        manager.record_tool_call(ToolCall(id="tool_1", name="read", input={"file": "nonexistent.txt"}))
        manager.update_tool_call_result("tool_1", error="File not found")
        manager.transition_to(AgentState.ERROR)

        stats = manager.get_statistics()
        assert stats["state"] == "error"
        assert stats["failed_calls"] == 1
        assert manager.end_time is not None

    def test_max_turns_exceeded_workflow(self):
        """Test workflow with max turns exceeded"""
        manager = AgentStateManager(max_turns=3)

        manager.transition_to(AgentState.THINKING)

        for i in range(2):
            result = manager.increment_turn()
            assert result is False

        # Third increment should exceed (3 >= 3)
        result = manager.increment_turn()
        assert result is True
        assert manager.current_turn == 3
