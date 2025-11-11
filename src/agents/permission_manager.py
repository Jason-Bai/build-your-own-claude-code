"""Tool execution permission manager"""

import json
import os
from pathlib import Path
from typing import Dict, Set, Tuple
from enum import Enum


class PermissionMode(Enum):
    """权限管理模式"""
    ALWAYS_ASK = "always_ask"              # 所有工具都询问
    AUTO_APPROVE_SAFE = "auto_approve_safe"  # 只自动批准 SAFE（默认）
    AUTO_APPROVE_ALL = "auto_approve_all"    # 批准所有（危险）
    SKIP_ALL = "skip_all"                    # 跳过所有检查（最危险）


class PermissionManager:
    """工具执行权限管理器"""

    def __init__(self, mode: PermissionMode = PermissionMode.AUTO_APPROVE_SAFE, config: dict = None):
        self.mode = mode
        self.config = config or {}

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
        """提示用户确认"""
        print("\n" + "=" * 50)
        print("🔐 Permission Request")
        print("=" * 50)
        print(f"Tool: {tool.name}")
        print(f"Level: {tool.permission_level.value.upper()}")
        print(f"Description: {tool.description}")
        print(f"\nParameters:")
        print(json.dumps(params, indent=2))

        if tool.permission_level.value == "dangerous":
            print("\n⚠️  WARNING: This is a potentially DANGEROUS operation!")
            print("⚠️  Please review the parameters carefully.")

        print("\nOptions:")
        print("  [y] Yes, allow this once")
        print("  [n] No, deny this once")
        print("  [a] Always allow this tool")
        print("  [v] Never allow this tool")
        print("=" * 50)

        while True:
            try:
                choice = input("Your choice: ").lower().strip()

                if choice == 'y':
                    return True, ""
                elif choice == 'n':
                    return False, "Permission denied by user"
                elif choice == 'a':
                    self.approved_tools.add(tool.name)
                    print(f"✓ Will always allow '{tool.name}' in this session")
                    return True, ""
                elif choice == 'v':
                    self.denied_tools.add(tool.name)
                    print(f"✓ Will never allow '{tool.name}' in this session")
                    return False, "Permission denied by user"
                else:
                    print("Invalid choice. Please enter y/n/a/v")
            except (EOFError, KeyboardInterrupt):
                print("\n")
                return False, "Permission request interrupted"

    def save_preferences(self, config_path: str = "config.json"):
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
