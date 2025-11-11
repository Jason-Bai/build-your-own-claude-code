"""MCP configuration models"""

from typing import List, Dict
from pydantic import BaseModel


class MCPServerConfig(BaseModel):
    """MCP 服务器配置"""
    name: str
    command: str  # 如 "npx"
    args: List[str]  # 如 ["-y", "@modelcontextprotocol/server-filesystem"]
    env: Dict[str, str] = {}
    transport: str = "stdio"  # "stdio" | "sse"
    enabled: bool = True


class MCPTool(BaseModel):
    """MCP 工具信息"""
    name: str
    description: str
    input_schema: Dict[str, any]
    server: str  # 来自哪个 MCP 服务器
