"""
Unit tests for Agent Tool Manager

Tests tool registration, execution, statistics, and MCP integration.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.agents.tool_manager import AgentToolManager
from src.tools.base import BaseTool, ToolResult


@pytest.mark.unit
class TestAgentToolManagerInitialization:
    """Tests for AgentToolManager initialization"""

    def test_initialization_without_mcp(self):
        """Test initialization without MCP client"""
        manager = AgentToolManager()
        assert manager.mcp_client is None
        assert len(manager.tools) == 0
        assert len(manager.tool_usage_stats) == 0
        assert manager.executor is not None

    def test_initialization_with_mcp(self):
        """Test initialization with MCP client"""
        mock_mcp = Mock()
        manager = AgentToolManager(mcp_client=mock_mcp)
        assert manager.mcp_client == mock_mcp


@pytest.mark.unit
class TestToolRegistration:
    """Tests for tool registration"""

    def test_register_single_tool(self):
        """Test registering a single tool"""
        manager = AgentToolManager()
        mock_tool = Mock(spec=BaseTool)
        mock_tool.name = "bash"

        manager.register_tool(mock_tool)

        assert "bash" in manager.tools
        assert manager.tools["bash"] == mock_tool
        assert manager.tool_usage_stats["bash"] == 0

    def test_register_multiple_tools(self):
        """Test registering multiple tools"""
        manager = AgentToolManager()
        tools = []
        for i, name in enumerate(["bash", "read", "write"]):
            tool = Mock(spec=BaseTool)
            tool.name = name
            tools.append(tool)

        for tool in tools:
            manager.register_tool(tool)

        assert len(manager.tools) == 3
        assert all(name in manager.tools for name in ["bash", "read", "write"])

    def test_register_tools_batch(self):
        """Test batch registering tools"""
        manager = AgentToolManager()
        tools = []
        for name in ["bash", "read", "write", "edit"]:
            tool = Mock(spec=BaseTool)
            tool.name = name
            tools.append(tool)

        manager.register_tools(tools)

        assert len(manager.tools) == 4
        for tool in tools:
            assert tool.name in manager.tools

    def test_register_tool_overwrites_existing(self):
        """Test registering tool with same name overwrites"""
        manager = AgentToolManager()
        tool1 = Mock(spec=BaseTool)
        tool1.name = "bash"
        tool2 = Mock(spec=BaseTool)
        tool2.name = "bash"

        manager.register_tool(tool1)
        manager.register_tool(tool2)

        assert manager.tools["bash"] == tool2
        assert len(manager.tools) == 1


@pytest.mark.unit
class TestToolRetrieval:
    """Tests for tool retrieval"""

    def test_get_existing_tool(self):
        """Test getting existing tool"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        manager.register_tool(tool)

        retrieved = manager.get_tool("bash")
        assert retrieved == tool

    def test_get_nonexistent_tool(self):
        """Test getting nonexistent tool returns None"""
        manager = AgentToolManager()
        result = manager.get_tool("nonexistent")
        assert result is None

    def test_has_tool_existing(self):
        """Test has_tool for existing tool"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "read"
        manager.register_tool(tool)

        assert manager.has_tool("read") is True

    def test_has_tool_nonexistent(self):
        """Test has_tool for nonexistent tool"""
        manager = AgentToolManager()
        assert manager.has_tool("write") is False


@pytest.mark.unit
class TestToolDefinitions:
    """Tests for tool definitions"""

    def test_get_tool_definitions_empty(self):
        """Test getting tool definitions when no tools registered"""
        manager = AgentToolManager()
        definitions = manager.get_tool_definitions()
        assert definitions == []

    def test_get_tool_definitions_single_tool(self):
        """Test getting tool definitions with single tool"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        tool.description = "Execute shell commands"
        tool.input_schema = {"type": "object"}
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()
        assert len(definitions) == 1
        assert definitions[0]["name"] == "bash"
        assert definitions[0]["description"] == "Execute shell commands"

    def test_get_tool_definitions_multiple_tools(self):
        """Test getting tool definitions with multiple tools"""
        manager = AgentToolManager()
        for name in ["bash", "read", "write"]:
            tool = Mock(spec=BaseTool)
            tool.name = name
            tool.description = f"Tool: {name}"
            tool.input_schema = {}
            manager.register_tool(tool)

        definitions = manager.get_tool_definitions()
        assert len(definitions) == 3
        assert all(def_["name"] in ["bash", "read", "write"] for def_ in definitions)

    def test_get_tool_definitions_includes_mcp_tools(self):
        """Test that tool definitions include MCP tools"""
        mock_mcp = Mock()
        mock_mcp.is_connected.return_value = True
        mock_mcp.get_tool_definitions.return_value = [
            {"name": "mcp_tool_1", "description": "MCP Tool 1"}
        ]

        manager = AgentToolManager(mcp_client=mock_mcp)
        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        tool.description = "Bash tool"
        tool.input_schema = {}
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()
        assert len(definitions) == 2
        assert any(d["name"] == "bash" for d in definitions)
        assert any(d["name"] == "mcp_tool_1" for d in definitions)


@pytest.mark.unit
class TestToolExecution:
    """Tests for tool execution"""

    @pytest.mark.asyncio
    async def test_execute_builtin_tool_success(self):
        """Test executing builtin tool successfully"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        manager.register_tool(tool)

        # Mock executor
        with patch.object(manager.executor, 'execute_with_smart_retry') as mock_exec:
            expected_result = ToolResult(success=True, output="success")
            mock_exec.return_value = expected_result

            result = await manager.execute_tool("bash", {"command": "ls"})

            assert result.success is True
            assert result.output == "success"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing nonexistent tool"""
        manager = AgentToolManager()
        result = await manager.execute_tool("nonexistent", {})

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_increments_stats(self):
        """Test that execution increments usage stats"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "read"
        manager.register_tool(tool)

        with patch.object(manager.executor, 'execute_with_smart_retry') as mock_exec:
            mock_exec.return_value = ToolResult(success=True, output="")

            # Execute multiple times
            await manager.execute_tool("read", {})
            await manager.execute_tool("read", {})

            assert manager.tool_usage_stats["read"] == 2


@pytest.mark.unit
class TestMCPToolExecution:
    """Tests for MCP tool execution"""

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_success(self):
        """Test executing MCP tool successfully"""
        mock_mcp = Mock()
        mock_mcp.tools = {"mcp_tool": True}
        mock_mcp.call_tool = AsyncMock()

        # Mock MCP result with content
        mock_result = Mock()
        mock_content = Mock()
        mock_content.type = "text"
        mock_content.text = "MCP response"
        mock_result.content = [mock_content]
        mock_mcp.call_tool.return_value = mock_result

        manager = AgentToolManager(mcp_client=mock_mcp)
        result = await manager.execute_tool("mcp_tool", {})

        assert result.success is True
        assert "MCP response" in result.output
        assert result.metadata["source"] == "mcp"

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_not_connected(self):
        """Test executing MCP tool when not connected"""
        manager = AgentToolManager()
        result = await manager.execute_tool("mcp_tool", {})

        assert result.success is False
        assert "not found" in result.error.lower()


@pytest.mark.unit
class TestUsageStatistics:
    """Tests for usage statistics"""

    def test_get_usage_statistics_empty(self):
        """Test getting stats when no tools registered"""
        manager = AgentToolManager()
        stats = manager.get_usage_statistics()
        assert stats == {}

    def test_get_usage_statistics_after_registration(self):
        """Test getting stats after tool registration"""
        manager = AgentToolManager()
        for name in ["bash", "read", "write"]:
            tool = Mock(spec=BaseTool)
            tool.name = name
            manager.register_tool(tool)

        stats = manager.get_usage_statistics()
        assert all(name in stats for name in ["bash", "read", "write"])
        assert all(count == 0 for count in stats.values())

    def test_reset_statistics(self):
        """Test resetting statistics"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        manager.register_tool(tool)

        # Manually increment stat
        manager.tool_usage_stats["bash"] = 5

        manager.reset_statistics()
        assert manager.tool_usage_stats["bash"] == 0

    def test_get_usage_statistics_returns_copy(self):
        """Test that get_usage_statistics returns a copy"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        manager.register_tool(tool)

        stats = manager.get_usage_statistics()
        stats["bash"] = 999

        # Original should be unchanged
        assert manager.tool_usage_stats["bash"] == 0


@pytest.mark.unit
class TestListTools:
    """Tests for listing tools"""

    def test_list_tools_empty(self):
        """Test listing tools when none registered"""
        manager = AgentToolManager()
        result = manager.list_tools()
        assert result == []

    def test_list_tools_multiple(self):
        """Test listing multiple tools"""
        manager = AgentToolManager()
        names = ["bash", "read", "write", "grep"]
        for name in names:
            tool = Mock(spec=BaseTool)
            tool.name = name
            manager.register_tool(tool)

        result = manager.list_tools()
        assert set(result) == set(names)
        assert len(result) == 4


@pytest.mark.unit
class TestToolManagerIntegration:
    """Integration tests for AgentToolManager"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete workflow: register, execute, check stats"""
        manager = AgentToolManager()

        # Register tools
        tools = []
        for name in ["bash", "read", "write"]:
            tool = Mock(spec=BaseTool)
            tool.name = name
            tool.description = f"Tool: {name}"
            tool.input_schema = {}
            tools.append(tool)

        manager.register_tools(tools)

        # Check definitions
        definitions = manager.get_tool_definitions()
        assert len(definitions) == 3

        # Mock execution
        with patch.object(manager.executor, 'execute_with_smart_retry') as mock_exec:
            mock_exec.return_value = ToolResult(success=True, output="result")

            # Execute bash twice
            await manager.execute_tool("bash", {"command": "ls"})
            await manager.execute_tool("bash", {"command": "pwd"})

        # Check stats
        stats = manager.get_usage_statistics()
        assert stats["bash"] == 2
        assert stats["read"] == 0
        assert stats["write"] == 0

    @pytest.mark.asyncio
    async def test_mixed_builtin_and_mcp_tools(self):
        """Test workflow with both builtin and MCP tools"""
        mock_mcp = Mock()
        mock_mcp.is_connected.return_value = True
        mock_mcp.tools = {"mcp_search": True}
        mock_mcp.get_tool_definitions.return_value = [
            {"name": "mcp_search", "description": "MCP Search"}
        ]

        manager = AgentToolManager(mcp_client=mock_mcp)

        # Register builtin tool
        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        tool.description = "Bash"
        tool.input_schema = {}
        manager.register_tool(tool)

        # Get all definitions
        definitions = manager.get_tool_definitions()
        names = [d["name"] for d in definitions]
        assert "bash" in names
        assert "mcp_search" in names
