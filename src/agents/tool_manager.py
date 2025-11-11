"""Tool manager for agents"""

from typing import Dict, List, Optional, TYPE_CHECKING
from ..tools import BaseTool, ToolResult, ToolExecutor

if TYPE_CHECKING:
    from ..mcps import MCPClient


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

    async def execute_tool(self, name: str, params: Dict) -> ToolResult:
        """执行工具（带智能重试），支持内置工具和 MCP 工具"""
        # 先检查内置工具
        if name in self.tools:
            tool = self.tools[name]
            result = await self.executor.execute_with_smart_retry(tool, params)
            self.tool_usage_stats[name] = self.tool_usage_stats.get(name, 0) + 1
            return result

        # 检查 MCP 工具
        if self.mcp_client and name in self.mcp_client.tools:
            try:
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
