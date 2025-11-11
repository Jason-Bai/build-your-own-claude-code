"""Tool executor with smart retry logic"""

import asyncio
from typing import Dict
from .base import BaseTool, ToolResult


class ToolExecutor:
    """工具执行器，带智能重试逻辑"""

    async def execute_with_smart_retry(
        self,
        tool: BaseTool,
        params: Dict,
        max_retries: int = 2
    ) -> ToolResult:
        """
        先尝试最多2次自动重试
        如果都失败，返回错误让 Claude 决定
        """
        last_result = None

        for attempt in range(max_retries):
            result = await tool.execute(**params)

            if result.success:
                return result

            last_result = result

            # 某些错误不值得重试
            if self._is_non_retryable_error(result):
                break

            # 短暂延迟后重试
            await asyncio.sleep(0.5 * (attempt + 1))

        # 所有重试都失败，返回错误信息
        return ToolResult(
            success=False,
            output="",
            error=f"Tool execution failed after {max_retries} attempts: {last_result.error}",
            metadata={"attempts": max_retries, "last_error": last_result.error}
        )

    def _is_non_retryable_error(self, result: ToolResult) -> bool:
        """判断是否不应该重试的错误"""
        # 文件不存在、权限错误等不应该重试
        non_retryable_keywords = [
            "not found",
            "permission denied",
            "invalid syntax",
            "does not exist"
        ]

        error_msg = (result.error or "").lower()
        return any(kw in error_msg for kw in non_retryable_keywords)
