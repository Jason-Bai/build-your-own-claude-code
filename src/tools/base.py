"""Base tool interface and result class"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel
from enum import Enum


class ToolPermissionLevel(Enum):
    """工具权限级别"""
    SAFE = "safe"          # 只读操作：Read, Glob, Grep, TodoWrite
    NORMAL = "normal"      # 写入操作：Write, Edit
    DANGEROUS = "dangerous"  # 执行操作：Bash


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    output: str
    error: str | None = None
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """工具基类"""

    # 默认权限级别（子类应该覆盖）
    permission_level: ToolPermissionLevel = ToolPermissionLevel.NORMAL

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict:
        """JSON Schema 格式的参数定义"""
        pass

    @abstractmethod
    async def execute(self, **params) -> ToolResult:
        """执行工具"""
        pass
