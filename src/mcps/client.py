"""MCP (Model Context Protocol) client implementation"""

from typing import List, Dict, Any
from .config import MCPServerConfig, MCPTool


class MCPClient:
    """MCP 客户端（简化版，可选安装）"""

    def __init__(self):
        self.servers: Dict[str, Any] = {}
        self.tools: Dict[str, MCPTool] = {}
        self._mcp_available = self._check_mcp_availability()

    def _check_mcp_availability(self) -> bool:
        """检查 MCP 是否可用"""
        try:
            import mcp  # type: ignore
            return True
        except ImportError:
            return False

    async def connect_server(self, config: MCPServerConfig):
        """连接到 MCP 服务器"""
        if not self._mcp_available:
            print(f"⚠️  MCP not installed. Install with: pip install mcp")
            return

        if not config.enabled:
            return

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            if config.transport == "stdio":
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=config.env
                )

                stdio_transport = await stdio_client(server_params)
                session = ClientSession(
                    stdio_transport.read,
                    stdio_transport.write
                )

                await session.initialize()

                # 保存会话
                self.servers[config.name] = session

                # 获取工具列表
                tools_result = await session.list_tools()

                for tool in tools_result.tools:
                    # 添加前缀避免冲突
                    tool_name = f"mcp_{config.name}_{tool.name}"
                    self.tools[tool_name] = MCPTool(
                        name=tool.name,
                        description=tool.description or "",
                        input_schema=tool.inputSchema,
                        server=config.name
                    )

                print(f"✓ Connected to MCP server: {config.name} ({len(tools_result.tools)} tools)")

            else:
                raise NotImplementedError(f"Transport {config.transport} not supported")

        except Exception as e:
            print(f"✗ Failed to connect to MCP server {config.name}: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用 MCP 工具"""
        if tool_name not in self.tools:
            raise ValueError(f"MCP tool {tool_name} not found")

        tool_info = self.tools[tool_name]
        server_name = tool_info.server
        original_name = tool_info.name

        if server_name not in self.servers:
            raise ValueError(f"MCP server {server_name} not connected")

        session = self.servers[server_name]
        result = await session.call_tool(original_name, arguments)

        return result

    def get_tool_definitions(self) -> List[Dict]:
        """获取所有 MCP 工具定义"""
        return [
            {
                "name": tool_name,
                "description": tool_info.description,
                "input_schema": tool_info.input_schema
            }
            for tool_name, tool_info in self.tools.items()
        ]

    async def disconnect_all(self):
        """断开所有 MCP 服务器"""
        for name, session in self.servers.items():
            try:
                await session.close()
                print(f"✓ Disconnected from MCP server: {name}")
            except Exception as e:
                print(f"✗ Error disconnecting from {name}: {e}")

        self.servers.clear()
        self.tools.clear()

    def is_available(self) -> bool:
        """MCP 是否可用"""
        return self._mcp_available

    def is_connected(self) -> bool:
        """是否有已连接的服务器"""
        return len(self.servers) > 0
