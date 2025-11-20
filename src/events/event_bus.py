"""EventBus implementation for real-time feedback"""

from enum import Enum
from typing import Callable, List, Dict, Any
from dataclasses import dataclass, field
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for Agent execution pipeline"""

    # Agent lifecycle
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"

    # Agent State Changes
    AGENT_STATE_CHANGED = "agent_state_changed"

    # Thinking phase
    AGENT_THINKING = "agent_thinking"
    AGENT_THINKING_END = "agent_thinking_end"

    # Tool selection phase
    TOOL_SELECTED = "tool_selected"

    # Tool execution phase
    TOOL_STARTED = "tool_started"  # Tool begins execution (replaces TOOL_EXECUTING)
    TOOL_EXECUTING = "tool_executing"  # Kept for backward compatibility
    TOOL_OUTPUT_CHUNK = "tool_output_chunk"
    TOOL_COMPLETED = "tool_completed"
    TOOL_ERROR = "tool_error"

    # LLM communication
    LLM_CALLING = "llm_calling"
    LLM_RESPONSE = "llm_response"

    # User interaction
    USER_INPUT_PAUSED = "user_input_paused"  # ESC key pressed
    USER_INPUT_RESUMED = "user_input_resumed"  # Input resumed after pause

    # Permission requests (for UI coordination)
    PERMISSION_REQUESTED = "permission_requested"  # Permission dialog shown
    PERMISSION_RESOLVED = "permission_resolved"    # Permission dialog closed

    # Status updates
    STATUS_UPDATE = "status_update"


@dataclass
class Event:
    """Event data structure"""
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time() if asyncio.get_event_loop() else 0)

    def __init__(self, event_type: EventType, **data):
        self.event_type = event_type
        self.data = data
        try:
            self.timestamp = asyncio.get_event_loop().time()
        except RuntimeError:
            self.timestamp = 0


class EventBus:
    """Pub/Sub event bus for real-time feedback"""

    def __init__(self):
        # 存储监听器: {event_type: [callback1, callback2, ...]}
        self._listeners: Dict[EventType, List[Callable]] = {}
        # 全局监听器（监听所有事件）
        self._global_listeners: List[Callable] = []
        # 事件队列（用于异步处理）
        self._event_queue: asyncio.Queue = None
        self._lock = asyncio.Lock() if asyncio.get_event_loop() else None

    async def _ensure_queue(self):
        """确保事件队列已初始化"""
        if self._event_queue is None:
            self._event_queue = asyncio.Queue()

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        订阅特定事件类型

        Args:
            event_type: 事件类型
            callback: 回调函数 (async def callback(event: Event) -> None)
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type.value}")

    def subscribe_all(self, callback: Callable) -> None:
        """
        订阅所有事件

        Args:
            callback: 回调函数 (async def callback(event: Event) -> None)
        """
        self._global_listeners.append(callback)
        logger.debug("Subscribed to all events")

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """取消订阅特定事件"""
        if event_type in self._listeners and callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)

    def unsubscribe_all(self, callback: Callable) -> None:
        """从全局监听器中移除"""
        if callback in self._global_listeners:
            self._global_listeners.remove(callback)

    async def emit(self, event: Event) -> None:
        """
        发送事件（异步，不阻塞）

        Args:
            event: 事件对象
        """
        await self._ensure_queue()

        # 立即调用同步监听器
        # 1. 调用特定事件的监听器
        if event.event_type in self._listeners:
            for callback in self._listeners[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {event.event_type.value}: {e}")

        # 2. 调用全局监听器
        for callback in self._global_listeners:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in global event callback: {e}")

    def emit_sync(self, event: Event) -> None:
        """
        同步发送事件（非异步版本）
        用于在没有 async context 的地方发送事件

        Args:
            event: 事件对象
        """
        # 1. 调用特定事件的监听器
        if event.event_type in self._listeners:
            for callback in self._listeners[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        # 无法在同步上下文中调用异步函数
                        logger.warning(f"Cannot call async callback in sync context for {event.event_type.value}")
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {event.event_type.value}: {e}")

        # 2. 调用全局监听器
        for callback in self._global_listeners:
            try:
                if asyncio.iscoroutinefunction(callback):
                    logger.warning(f"Cannot call async callback in sync context")
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in global event callback: {e}")

    def clear(self) -> None:
        """清空所有监听器"""
        self._listeners.clear()
        self._global_listeners.clear()


# 全局事件总线实例
_global_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def reset_event_bus() -> None:
    """重置全局事件总线（用于测试）"""
    global _global_event_bus
    _global_event_bus = None
