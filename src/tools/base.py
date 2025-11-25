"""Base tool interface and result class"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Callable, Awaitable, Optional
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
    async def execute(self, on_chunk: Optional[Callable[[str], Awaitable[None]]] = None, **params) -> ToolResult:
        """执行工具"""
        pass


class SubprocessTool(BaseTool):
    """Base class for tools that run external processes

    This base class provides a standard interface for tools that spawn
    subprocesses, enabling uniform cancellation handling.

    Subclasses must implement:
    - start_async(): Start the process and return a handle
    - is_running(): Check if process is still running
    - kill(): Forcefully terminate the process
    - result(): Get the process result after completion
    """

    @abstractmethod
    async def start_async(self, **params):
        """Start process and return handle

        Returns:
            Process handle that implements is_running(), kill(), and result()
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if process is still running

        Returns:
            True if process is running, False if completed
        """
        pass

    @abstractmethod
    def kill(self):
        """Forcefully terminate process

        This should send SIGKILL or equivalent to ensure immediate termination.
        """
        pass

    @abstractmethod
    def result(self) -> ToolResult:
        """Get process result after completion

        Returns:
            ToolResult containing stdout, stderr, exit code

        Raises:
            RuntimeError: If process is still running
        """
        pass
