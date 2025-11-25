"""
日志系统数据类型定义
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """行动类型枚举"""
    # 用户交互
    USER_INPUT = "user_input"
    USER_COMMAND = "user_command"

    # Agent状态
    AGENT_STATE_CHANGE = "agent_state_change"
    AGENT_THINKING = "agent_thinking"        # Agent思考过程

    # LLM交互
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    LLM_ERROR = "llm_error"  # 新增：LLM调用失败

    # 工具执行
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"
    TOOL_PERMISSION = "tool_permission"      # 工具权限请求

    # 会话生命周期
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_PAUSE = "session_pause"      # 会话暂停
    SESSION_RESUME = "session_resume"    # 会话恢复
    EXECUTION_CANCELLED = "execution_cancelled"  # 执行被取消（用户按ESC）

    # 系统级别
    SYSTEM_ERROR = "system_error"  # 新增：系统错误
    SYSTEM_WARNING = "system_warning"  # 新增：系统警告


class ActionStatus(str, Enum):
    """行动状态"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"


@dataclass
class ActionData:
    """
    行动日志数据结构

    通用字段（所有日志共享）：
    - timestamp: 时间戳（ISO 8601格式）
    - action_number: 行动序号（全局递增）
    - action_type: 行动类型
    - session_id: 会话ID
    - execution_id: 执行ID（可选，仅长流程任务）
    - status: 状态
    - data: 具体数据（根据action_type不同而不同）
    """
    timestamp: str
    action_number: int
    action_type: str
    session_id: str
    status: str
    data: Dict[str, Any] = field(default_factory=dict)
    execution_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于JSON序列化）"""
        result = {
            "timestamp": self.timestamp,
            "action_number": self.action_number,
            "action_type": self.action_type,
            "session_id": self.session_id,
            "status": self.status,
        }

        # 可选字段
        if self.execution_id:
            result["execution_id"] = self.execution_id

        # 合并具体数据
        result.update(self.data)

        return result

    @classmethod
    def create(
        cls,
        action_type: str,
        session_id: str,
        status: str = ActionStatus.SUCCESS,
        execution_id: Optional[str] = None,
        **data
    ) -> "ActionData":
        """
        创建行动数据（工厂方法）

        Args:
            action_type: 行动类型
            session_id: 会话ID
            status: 状态（默认success）
            execution_id: 执行ID（可选）
            **data: 具体数据字段

        Returns:
            ActionData实例
        """
        return cls(
            timestamp=datetime.now().isoformat(),
            action_number=0,  # 将在logger中分配
            action_type=action_type,
            session_id=session_id,
            status=status,
            execution_id=execution_id,
            data=data
        )
