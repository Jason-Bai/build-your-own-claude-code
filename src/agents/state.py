"""Agent state management"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


class AgentState(Enum):
    """Agent 运行状态"""
    IDLE = "idle"
    THINKING = "thinking"
    USING_TOOL = "using_tool"
    WAITING_FOR_RESULT = "waiting_for_result"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ToolCall:
    """工具调用记录"""
    id: str
    name: str
    input: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    result: Optional[Any] = None
    error: Optional[str] = None
    status: str = "pending"  # pending, completed, failed


@dataclass
class AgentStateManager:
    """Agent 状态管理器"""

    current_state: AgentState = AgentState.IDLE
    current_turn: int = 0
    max_turns: int = 20

    # 工具调用历史
    tool_calls: List[ToolCall] = field(default_factory=list)

    # 统计信息
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def transition_to(self, new_state: AgentState):
        """状态转换"""
        self.current_state = new_state

        if new_state == AgentState.THINKING and self.start_time is None:
            self.start_time = datetime.now()
        elif new_state == AgentState.COMPLETED or new_state == AgentState.ERROR:
            self.end_time = datetime.now()

    def record_tool_call(self, tool_call: ToolCall):
        """记录工具调用"""
        self.tool_calls.append(tool_call)

    def update_tool_call_result(self, tool_id: str, result: Any = None, error: str = None):
        """更新工具调用结果"""
        for call in self.tool_calls:
            if call.id == tool_id:
                call.result = result
                call.error = error
                call.status = "completed" if error is None else "failed"
                break

    def increment_turn(self) -> bool:
        """增加回合数，返回是否超过最大回合数"""
        self.current_turn += 1
        return self.current_turn >= self.max_turns

    def add_tokens(self, input_tokens: int, output_tokens: int):
        """添加 token 使用统计"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            "state": self.current_state.value,
            "turns": self.current_turn,
            "tool_calls": len(self.tool_calls),
            "successful_calls": sum(1 for c in self.tool_calls if c.status == "completed"),
            "failed_calls": sum(1 for c in self.tool_calls if c.status == "failed"),
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "duration_seconds": duration
        }

    def reset(self):
        """重置状态"""
        self.current_state = AgentState.IDLE
        self.current_turn = 0
        self.tool_calls.clear()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.start_time = None
        self.end_time = None
