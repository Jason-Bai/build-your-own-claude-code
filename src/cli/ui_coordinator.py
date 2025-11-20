"""UI Coordinator - 统一协调 InterfaceManager 和 OutputFormatter

解决问题：
1. InterfaceManager (异步 Live Display) 与同步 input() 冲突
2. OutputFormatter 与 InterfaceManager 双重输出
3. Permission 请求时无法输入

设计思路：
- REACTIVE 模式：InterfaceManager 活跃，OutputFormatter 静默
- INTERACTIVE 模式：InterfaceManager 暂停，OutputFormatter 活跃
- 模式切换通过事件自动触发
"""

from enum import Enum
from typing import Optional
from rich.console import Console
import logging

from src.events import EventBus, Event, EventType
from .ui_manager import InterfaceManager
from src.utils.output import OutputFormatter


logger = logging.getLogger(__name__)


class UIMode(Enum):
    """UI 模式"""
    REACTIVE = "reactive"        # 响应式 UI（Live Display + Spinner）
    INTERACTIVE = "interactive"  # 交互式（同步 input，暂停 Live）
    LEGACY = "legacy"            # 传统模式（仅 print，不使用 Live）


class UICoordinator:
    """
    统一协调 UI 输出，避免冲突

    职责：
    1. 管理 UI 模式切换（REACTIVE ↔ INTERACTIVE）
    2. 在 INTERACTIVE 模式时暂停 InterfaceManager
    3. 在 REACTIVE 模式时禁用 OutputFormatter 状态输出
    4. 保证用户可以正常输入（input）

    使用场景：
    - Permission 请求：REACTIVE → INTERACTIVE → REACTIVE
    - ESC 键暂停：保持当前模式但清理 UI
    - 普通对话：始终 REACTIVE
    """

    def __init__(self, event_bus: EventBus, console: Console,
                 enable_reactive_ui: bool = True):
        """
        Args:
            event_bus: 全局事件总线
            console: Rich Console 实例
            enable_reactive_ui: 是否启用响应式 UI（False 则降级为 LEGACY）
        """
        self.event_bus = event_bus
        self.console = console
        self.enable_reactive = enable_reactive_ui

        # 当前模式
        self.current_mode = UIMode.REACTIVE if enable_reactive_ui else UIMode.LEGACY

        # 组件
        self.interface_manager: Optional[InterfaceManager] = None

        if enable_reactive_ui:
            # 初始化响应式 UI Manager
            self.interface_manager = InterfaceManager(event_bus, console)

            # ✨ 关键修复：设置 OutputFormatter 为 quiet 模式
            # 避免与 InterfaceManager 的 Live Display 产生重复输出
            OutputFormatter.set_quiet_mode(thinking=True, tools=True)

            logger.info("UICoordinator initialized in REACTIVE mode with quiet OutputFormatter")
        else:
            logger.info("UICoordinator initialized in LEGACY mode")

        # 订阅关键事件
        self._subscribe_events()

    def _subscribe_events(self):
        """订阅需要切换模式的事件"""
        self.event_bus.subscribe(EventType.PERMISSION_REQUESTED, self._handle_permission_start)
        self.event_bus.subscribe(EventType.PERMISSION_RESOLVED, self._handle_permission_end)
        self.event_bus.subscribe(EventType.USER_INPUT_PAUSED, self._handle_user_pause)

    async def _handle_permission_start(self, event: Event):
        """
        Permission 请求开始 → 切换到 INTERACTIVE 模式

        流程：
        1. 暂停 InterfaceManager（停止 Live Display）
        2. 切换到 INTERACTIVE 模式
        3. OutputFormatter 可以正常输出
        """
        if not self.enable_reactive:
            return  # LEGACY 模式无需切换

        if self.current_mode == UIMode.INTERACTIVE:
            logger.warning("Already in INTERACTIVE mode")
            return

        logger.debug("Switching to INTERACTIVE mode for permission request")

        # 暂停响应式 UI
        if self.interface_manager:
            await self.interface_manager.pause()

        self.current_mode = UIMode.INTERACTIVE

        # OutputFormatter 会自动输出 permission prompt（因为 Live 已暂停）

    async def _handle_permission_end(self, event: Event):
        """
        Permission 结束 → 切换回 REACTIVE 模式

        流程：
        1. 恢复 InterfaceManager（重启 Live Display）
        2. 切换回 REACTIVE 模式
        3. OutputFormatter 再次静默
        """
        if not self.enable_reactive:
            return

        if self.current_mode != UIMode.INTERACTIVE:
            logger.warning(f"Expected INTERACTIVE mode but in {self.current_mode}")
            return

        logger.debug("Switching back to REACTIVE mode")

        # 恢复响应式 UI
        if self.interface_manager:
            await self.interface_manager.resume()

        self.current_mode = UIMode.REACTIVE

    async def _handle_user_pause(self, event: Event):
        """
        用户按 ESC → 清理 UI（保持当前模式）

        与 permission 不同：
        - Permission: 切换模式（需要恢复）
        - ESC: 清理 UI（不切换模式）
        """
        if self.interface_manager:
            # InterfaceManager 已经订阅了 USER_INPUT_PAUSED
            # 这里只是记录日志
            logger.debug("User paused - UI cleanup triggered")

    def is_reactive_mode(self) -> bool:
        """当前是否处于响应式模式"""
        return self.current_mode == UIMode.REACTIVE

    def is_interactive_mode(self) -> bool:
        """当前是否处于交互式模式"""
        return self.current_mode == UIMode.INTERACTIVE

    def get_current_mode(self) -> UIMode:
        """获取当前模式"""
        return self.current_mode


# ========== 全局单例 ==========

_coordinator: Optional[UICoordinator] = None


def get_coordinator() -> Optional[UICoordinator]:
    """
    获取全局 UI Coordinator 实例

    Returns:
        UICoordinator 实例，如果未初始化则返回 None
    """
    return _coordinator


def init_coordinator(event_bus: EventBus, console: Console,
                    enable_reactive_ui: bool = True) -> UICoordinator:
    """
    初始化全局 UI Coordinator

    Args:
        event_bus: 事件总线
        console: Rich Console
        enable_reactive_ui: 是否启用响应式 UI

    Returns:
        UICoordinator 实例
    """
    global _coordinator

    if _coordinator is not None:
        logger.warning("UICoordinator already initialized, replacing...")

    _coordinator = UICoordinator(event_bus, console, enable_reactive_ui)
    return _coordinator


def reset_coordinator():
    """重置全局 Coordinator（用于测试）"""
    global _coordinator
    _coordinator = None
