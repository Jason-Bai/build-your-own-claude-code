"""Tool manager for agents"""

import asyncio
from typing import Dict, List, Optional, TYPE_CHECKING, Callable, Awaitable
from ..tools import BaseTool, ToolResult, ToolExecutor, SubprocessTool

if TYPE_CHECKING:
    from ..mcps import MCPClient
    from ..utils.cancellation import CancellationToken


class AgentToolManager:
    """Agent 工具管理器（支持 MCP）"""

    def __init__(self, mcp_client: Optional["MCPClient"] = None):
        self.tools: Dict[str, BaseTool] = {}
        self.executor = ToolExecutor()
        self.tool_usage_stats: Dict[str, int] = {}
        self.mcp_client = mcp_client

    def register_tool(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.name] = tool
        self.tool_usage_stats[tool.name] = 0

    def register_tools(self, tools: List[BaseTool]):
        """批量注册工具"""
        for tool in tools:
            self.register_tool(tool)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(name)

    def get_tool_definitions(self) -> List[Dict]:
        """获取所有工具定义（用于 LLM API），包括 MCP 工具"""
        definitions = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]

        # 添加 MCP 工具
        if self.mcp_client and self.mcp_client.is_connected():
            definitions.extend(self.mcp_client.get_tool_definitions())

        return definitions

    async def execute_tool(
        self,
        name: str,
        params: Dict,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        cancellation_token: Optional["CancellationToken"] = None
    ) -> ToolResult:
        """执行工具（带智能重试和取消支持），支持内置工具和 MCP 工具

        Args:
            name: 工具名称
            params: 工具参数
            on_chunk: 流式输出回调
            cancellation_token: 取消令牌，用于中断工具执行

        Returns:
            ToolResult: 工具执行结果
        """
        # Check cancellation before starting
        if cancellation_token:
            cancellation_token.raise_if_cancelled()

        # 先检查内置工具
        if name in self.tools:
            tool = self.tools[name]

            # Case A: Subprocess Tools with cancellation support
            if isinstance(tool, SubprocessTool):
                result = await self._execute_subprocess_tool_with_cancellation(
                    tool, params, cancellation_token
                )
                self.tool_usage_stats[name] = self.tool_usage_stats.get(name, 0) + 1
                return result

            # Case B: Regular async tools
            else:
                result = await self._execute_async_tool_with_cancellation(
                    tool, params, on_chunk, cancellation_token
                )
                self.tool_usage_stats[name] = self.tool_usage_stats.get(name, 0) + 1
                return result

        # 检查 MCP 工具
        if self.mcp_client and name in self.mcp_client.tools:
            try:
                # Use MCP client's cancellation wrapper if available
                if cancellation_token and hasattr(self.mcp_client, 'call_tool_with_cancellation'):
                    mcp_result = await self.mcp_client.call_tool_with_cancellation(
                        name, params, cancellation_token
                    )
                else:
                    mcp_result = await self.mcp_client.call_tool(name, params)

                # 转换 MCP 结果为 ToolResult
                output_parts = []
                if hasattr(mcp_result, 'content'):
                    for content_item in mcp_result.content:
                        if hasattr(content_item, 'type'):
                            if content_item.type == "text":
                                output_parts.append(content_item.text)
                            elif content_item.type == "image":
                                output_parts.append(f"[Image data]")
                            elif content_item.type == "resource":
                                output_parts.append(f"[Resource: {content_item.uri}]")
                else:
                    output_parts.append(str(mcp_result))

                self.tool_usage_stats[name] = self.tool_usage_stats.get(name, 0) + 1

                return ToolResult(
                    success=True,
                    output="\n".join(output_parts) if output_parts else "Success",
                    metadata={"source": "mcp"}
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"MCP tool execution failed: {str(e)}"
                )

        # 工具不存在
        return ToolResult(
            success=False,
            output="",
            error=f"Tool {name} not found"
        )

    async def _execute_subprocess_tool_with_cancellation(
        self,
        tool: SubprocessTool,
        params: Dict,
        cancellation_token: Optional["CancellationToken"]
    ) -> ToolResult:
        """Execute subprocess tool with cancellation support

        Uses asyncio.wait() with FIRST_COMPLETED for immediate response.
        When cancelled, kills the subprocess immediately.

        Args:
            tool: SubprocessTool instance
            params: Tool parameters
            cancellation_token: Cancellation token

        Returns:
            ToolResult from the process
        """
        # Start the process
        process = await tool.start_async(**params)

        if not cancellation_token:
            # No cancellation support, just wait for completion
            while process.is_running():
                await asyncio.sleep(0.1)
            return process.result()

        # Create task for process completion
        async def wait_for_process():
            while process.is_running():
                await asyncio.sleep(0.1)
            return process.result()

        process_task = asyncio.create_task(wait_for_process())

        # Create cancellation monitoring task
        cancel_task = asyncio.create_task(
            cancellation_token.wait()
        )

        try:
            # Wait for whichever completes first
            done, pending = await asyncio.wait(
                [process_task, cancel_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Check if cancellation happened
            if cancel_task in done:
                # Kill the process immediately
                process.kill()

                # Cancel the waiting task
                process_task.cancel()

                # Raise cancellation
                raise asyncio.CancelledError("Tool execution cancelled")

            # Process completed normally
            cancel_task.cancel()
            return await process_task

        finally:
            # Cleanup
            for task in [process_task, cancel_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    async def _execute_async_tool_with_cancellation(
        self,
        tool: BaseTool,
        params: Dict,
        on_chunk: Optional[Callable[[str], Awaitable[None]]],
        cancellation_token: Optional["CancellationToken"]
    ) -> ToolResult:
        """Execute async tool with cancellation support

        Uses asyncio.wait() with FIRST_COMPLETED to immediately respond to
        cancellation requests without polling delays.

        Args:
            tool: BaseTool instance
            params: Tool parameters
            on_chunk: Streaming callback
            cancellation_token: Cancellation token

        Returns:
            ToolResult from the tool
        """
        # Use executor with smart retry for non-subprocess tools
        if not cancellation_token:
            # No cancellation support, execute directly
            return await self.executor.execute_with_smart_retry(
                tool, params, on_chunk=on_chunk
            )

        # Create task for tool execution
        tool_task = asyncio.create_task(
            self.executor.execute_with_smart_retry(tool, params, on_chunk=on_chunk)
        )

        # Create cancellation monitoring task
        cancel_task = asyncio.create_task(
            cancellation_token.wait()
        )

        try:
            # Wait for whichever completes first
            done, pending = await asyncio.wait(
                [tool_task, cancel_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Check if cancellation happened
            if cancel_task in done:
                # Cancel the tool task
                tool_task.cancel()

                # Wait for it to actually cancel (with timeout)
                try:
                    await asyncio.wait_for(tool_task, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

                # Raise cancellation
                raise asyncio.CancelledError("Tool execution cancelled")

            # Tool task completed normally
            cancel_task.cancel()
            return await tool_task

        finally:
            # Cleanup: ensure all tasks are cancelled
            for task in [tool_task, cancel_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    def get_usage_statistics(self) -> Dict[str, int]:
        """获取工具使用统计"""
        return self.tool_usage_stats.copy()

    def reset_statistics(self):
        """重置统计"""
        for tool_name in self.tool_usage_stats:
            self.tool_usage_stats[tool_name] = 0

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self.tools.keys())

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self.tools
