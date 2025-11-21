"""Tool execution permission manager"""

import json
import os
from pathlib import Path
from typing import Dict, Set, Tuple, Optional
from enum import Enum

from ..events import EventBus, Event, EventType, get_event_bus
from ..logging import get_action_logger
from ..logging.types import ActionType


class PermissionMode(Enum):
    """权限管理模式"""
    ALWAYS_ASK = "always_ask"              # 所有工具都询问
    AUTO_APPROVE_SAFE = "auto_approve_safe"  # 只自动批准 SAFE（默认）
    AUTO_APPROVE_ALL = "auto_approve_all"    # 批准所有（危险）
    SKIP_ALL = "skip_all"                    # 跳过所有检查（最危险）


class PermissionManager:
    """工具执行权限管理器"""

    def __init__(self, mode: PermissionMode = PermissionMode.AUTO_APPROVE_SAFE,
                 config: dict = None,
                 event_bus: Optional[EventBus] = None):
        self.mode = mode
        self.config = config or {}
        self.event_bus = event_bus or get_event_bus()
        self.action_logger = get_action_logger()

        # 从配置加载预设权限
        self.approved_tools: Set[str] = set(
            self.config.get("always_allow", [])
        )
        self.denied_tools: Set[str] = set(
            self.config.get("never_allow", [])
        )

        # 工具特定权限配置
        self.tool_permissions: Dict[str, str] = self.config.get("tool_permissions", {})

        # 运行时用户选择的历史（会话级别）
        self.session_approved: Set[str] = set()
        self.session_denied: Set[str] = set()

    async def request_permission(
        self,
        tool,  # BaseTool type
        params: Dict
    ) -> Tuple[bool, str]:
        """
        请求工具执行权限

        Args:
            tool: 工具实例
            params: 工具参数

        Returns:
            (is_approved, message)
        """

        # 模式1: 跳过所有检查
        if self.mode == PermissionMode.SKIP_ALL:
            return True, ""

        # 模式2: 批准所有
        if self.mode == PermissionMode.AUTO_APPROVE_ALL:
            return True, ""

        # 检查工具特定配置
        tool_config = self.tool_permissions.get(tool.name)
        if tool_config == "allow":
            return True, ""
        elif tool_config == "deny":
            return False, "Permission denied by configuration"

        # 检查永久批准/拒绝列表
        if tool.name in self.approved_tools:
            return True, ""
        if tool.name in self.denied_tools:
            return False, "Permission denied by user"

        # 检查会话级别批准/拒绝
        if tool.name in self.session_approved:
            return True, ""
        if tool.name in self.session_denied:
            return False, "Permission denied by user"

        # 模式3: 自动批准 SAFE 级别
        if self.mode == PermissionMode.AUTO_APPROVE_SAFE:
            if tool.permission_level.value == "safe":
                return True, ""

        # 显示权限请求
        return await self._prompt_user(tool, params)

    async def _prompt_user(self, tool, params: Dict) -> Tuple[bool, str]:
        """提示用户确认 - 紧凑格式"""

        # 🔔 通知 UICoordinator: 需要同步输入（暂停 Live Display）
        await self.event_bus.emit(Event(
            EventType.PERMISSION_REQUESTED,
            tool_name=tool.name,
            level=tool.permission_level.value
        ))

        try:
            # 简化参数显示（只显示关键参数，限制长度）
            simplified_params = {}
            for key, value in params.items():
                if isinstance(value, str) and len(value) > 50:
                    simplified_params[key] = value[:50] + "..."
                else:
                    simplified_params[key] = value

            # 使用紧凑的表格式显示
            print("\n" + "━" * 60)
            level_symbol = "⚠️" if tool.permission_level.value == "dangerous" else "🔐"
            print(f"{level_symbol}  Permission Required: {tool.name} ({tool.permission_level.value.upper()})")
            print("━" * 60)
            print(f"Parameters: {json.dumps(simplified_params, ensure_ascii=False)}")

            if tool.permission_level.value == "dangerous":
                print("⚠️  WARNING: Potentially DANGEROUS operation!")

            print("\n[y]es  [n]o  [a]lways  ne[v]er")

            # 同步等待用户输入（Live Display 已停止，不会冲突）
            while True:
                try:
                    choice = input("Your choice: ").lower().strip()

                    if choice == 'y':
                        # Log permission granted
                        self.action_logger.log(
                            action_type=ActionType.TOOL_PERMISSION,
                            tool_name=tool.name,
                            permission_level=tool.permission_level.value,
                            user_decision="approved",
                            decision_type="once"
                        )
                        return True, ""
                    elif choice == 'n':
                        # Log permission denied
                        self.action_logger.log(
                            action_type=ActionType.TOOL_PERMISSION,
                            tool_name=tool.name,
                            permission_level=tool.permission_level.value,
                            user_decision="denied",
                            decision_type="once"
                        )
                        return False, "Permission denied by user"
                    elif choice == 'a':
                        self.approved_tools.add(tool.name)
                        print(f"✓ Will always allow '{tool.name}' in this session")
                        # Log permission always approved
                        self.action_logger.log(
                            action_type=ActionType.TOOL_PERMISSION,
                            tool_name=tool.name,
                            permission_level=tool.permission_level.value,
                            user_decision="approved",
                            decision_type="always"
                        )
                        return True, ""
                    elif choice == 'v':
                        self.denied_tools.add(tool.name)
                        print(f"✓ Will never allow '{tool.name}' in this session")
                        # Log permission never allowed
                        self.action_logger.log(
                            action_type=ActionType.TOOL_PERMISSION,
                            tool_name=tool.name,
                            permission_level=tool.permission_level.value,
                            user_decision="denied",
                            decision_type="never"
                        )
                        return False, "Permission denied by user"
                    else:
                        print("Invalid choice. Please enter y/n/a/v")
                except (EOFError, KeyboardInterrupt):
                    print("\n")
                    # Log permission interrupted
                    self.action_logger.log(
                        action_type=ActionType.TOOL_PERMISSION,
                        tool_name=tool.name,
                        permission_level=tool.permission_level.value,
                        user_decision="interrupted",
                        decision_type="interrupted"
                    )
                    return False, "Permission request interrupted"

        finally:
            # 🔔 通知 UICoordinator: 同步输入完成（恢复 Live Display）
            await self.event_bus.emit(Event(
                EventType.PERMISSION_RESOLVED,
                tool_name=tool.name
            ))

    def save_preferences(self, config_path: str = "~/.tiny-claude-code/settings.json"):
        """保存用户权限偏好到配置文件"""
        try:
            config_path = Path(config_path)
            config = {}

            # 如果配置文件存在，读取现有配置
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # 更新权限配置
            if "permissions" not in config:
                config["permissions"] = {}

            config["permissions"]["always_allow"] = list(self.approved_tools)
            config["permissions"]["never_allow"] = list(self.denied_tools)

            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"⚠️  Failed to save permission preferences: {e}")
            return False

    def get_stats(self) -> Dict:
        """获取权限统计信息"""
        return {
            "mode": self.mode.value,
            "always_allow": list(self.approved_tools),
            "never_allow": list(self.denied_tools),
            "session_approved": list(self.session_approved),
            "session_denied": list(self.session_denied),
            "tool_permissions": self.tool_permissions
        }
