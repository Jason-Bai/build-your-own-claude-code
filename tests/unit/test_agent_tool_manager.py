"""
Unit tests for Agent Tool Manager

Tests tool registration, execution, and statistics.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.agents.tool_manager import AgentToolManager
from src.tools import BaseTool, ToolResult


@pytest.mark.unit
class TestAgentToolManagerInitialization:
    """Tests for tool manager initialization"""

    def test_tool_manager_initialization(self):
        """Test tool manager initialization"""
        manager = AgentToolManager()

        assert manager.tools == {}
        assert manager.tool_usage_stats == {}
        assert manager.executor is not None
        assert manager.mcp_client is None

    def test_tool_manager_with_mcp_client(self):
        """Test tool manager initialization with MCP client"""
        mcp_client = Mock()
        manager = AgentToolManager(mcp_client=mcp_client)

        assert manager.mcp_client == mcp_client


@pytest.mark.unit
class TestAgentToolManagerRegistration:
    """Tests for tool registration"""

    def test_register_single_tool(self):
        """Test registering a single tool"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "test_tool"

        manager.register_tool(tool)

        assert "test_tool" in manager.tools
        assert manager.tools["test_tool"] == tool
        assert manager.tool_usage_stats["test_tool"] == 0

    def test_register_multiple_tools(self):
        """Test registering multiple tools"""
        manager = AgentToolManager()

        tools = []
        for i in range(3):
            tool = Mock(spec=BaseTool)
            tool.name = f"tool_{i}"
            tools.append(tool)

        manager.register_tools(tools)

        assert len(manager.tools) == 3
        for i in range(3):
            assert f"tool_{i}" in manager.tools

    def test_register_tool_overwrites_existing(self):
        """Test that registering tool with same name overwrites"""
        manager = AgentToolManager()

        tool1 = Mock(spec=BaseTool)
        tool1.name = "tool"
        tool2 = Mock(spec=BaseTool)
        tool2.name = "tool"

        manager.register_tool(tool1)
        manager.register_tool(tool2)

        assert manager.tools["tool"] == tool2


@pytest.mark.unit
class TestAgentToolManagerRetrieval:
    """Tests for tool retrieval"""

    def test_get_tool(self):
        """Test getting a tool"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"

        manager.register_tool(tool)
        retrieved = manager.get_tool("bash")

        assert retrieved == tool

    def test_get_nonexistent_tool(self):
        """Test getting nonexistent tool"""
        manager = AgentToolManager()

        result = manager.get_tool("nonexistent")

        assert result is None

    def test_list_tools(self):
        """Test listing all tool names"""
        manager = AgentToolManager()

        for i in range(3):
            tool = Mock(spec=BaseTool)
            tool.name = f"tool_{i}"
            manager.register_tool(tool)

        tools = manager.list_tools()

        assert len(tools) == 3
        assert "tool_0" in tools
        assert "tool_1" in tools
        assert "tool_2" in tools

    def test_has_tool(self):
        """Test checking tool existence"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"

        manager.register_tool(tool)

        assert manager.has_tool("bash") is True
        assert manager.has_tool("nonexistent") is False


@pytest.mark.unit
class TestAgentToolManagerDefinitions:
    """Tests for tool definitions"""

    def test_get_tool_definitions_basic(self):
        """Test getting tool definitions"""
        manager = AgentToolManager()

        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        tool.description = "Execute bash commands"
        tool.input_schema = {"type": "object", "properties": {}}

        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()

        assert len(definitions) == 1
        assert definitions[0]["name"] == "bash"
        assert definitions[0]["description"] == "Execute bash commands"
        assert definitions[0]["input_schema"] == {"type": "object", "properties": {}}

    def test_get_tool_definitions_multiple(self):
        """Test getting definitions for multiple tools"""
        manager = AgentToolManager()

        for i in range(3):
            tool = Mock(spec=BaseTool)
            tool.name = f"tool_{i}"
            tool.description = f"Tool {i}"
            tool.input_schema = {}
            manager.register_tool(tool)

        definitions = manager.get_tool_definitions()

        assert len(definitions) == 3

    def test_get_tool_definitions_with_mcp_disconnected(self):
        """Test that disconnected MCP client is ignored"""
        mcp_client = Mock()
        mcp_client.is_connected.return_value = False

        manager = AgentToolManager(mcp_client=mcp_client)

        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        tool.description = "Execute bash"
        tool.input_schema = {}

        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()

        # Should only include the registered tool
        assert len(definitions) == 1


@pytest.mark.unit
class TestAgentToolManagerStatistics:
    """Tests for statistics tracking"""

    def test_get_usage_statistics_empty(self):
        """Test getting statistics when no usage"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"

        manager.register_tool(tool)

        stats = manager.get_usage_statistics()

        assert stats["bash"] == 0

    def test_reset_statistics(self):
        """Test resetting statistics"""
        manager = AgentToolManager()

        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        manager.register_tool(tool)

        # Simulate some usage
        manager.tool_usage_stats["bash"] = 5

        manager.reset_statistics()

        assert manager.tool_usage_stats["bash"] == 0

    def test_get_usage_statistics_returns_copy(self):
        """Test that get_usage_statistics returns a copy"""
        manager = AgentToolManager()
        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        manager.register_tool(tool)

        stats1 = manager.get_usage_statistics()
        stats1["bash"] = 999

        stats2 = manager.get_usage_statistics()

        assert stats2["bash"] == 0


@pytest.mark.unit
class TestAgentToolManagerExecution:
    """Tests for tool execution"""

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test executing nonexistent tool"""
        manager = AgentToolManager()

        result = await manager.execute_tool("nonexistent", {})

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_with_mock_executor(self):
        """Test executing tool with mocked executor"""
        manager = AgentToolManager()

        # Mock executor
        manager.executor.execute_with_smart_retry = AsyncMock(
            return_value=ToolResult(success=True, output="test output")
        )

        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        manager.register_tool(tool)

        result = await manager.execute_tool("bash", {"command": "ls"})

        assert result.success is True
        assert result.output == "test output"
        assert manager.tool_usage_stats["bash"] == 1


@pytest.mark.unit
class TestAgentToolManagerIntegration:
    """Integration tests for tool manager"""

    def test_workflow_register_and_retrieve(self):
        """Test typical workflow of registering and retrieving tools"""
        manager = AgentToolManager()

        # Register tools
        for i in range(5):
            tool = Mock(spec=BaseTool)
            tool.name = f"tool_{i}"
            tool.description = f"Tool {i}"
            tool.input_schema = {}
            manager.register_tool(tool)

        # Retrieve and verify
        assert len(manager.list_tools()) == 5
        assert manager.has_tool("tool_0") is True
        assert manager.has_tool("tool_4") is True
        assert manager.has_tool("tool_5") is False

        # Get definitions
        definitions = manager.get_tool_definitions()
        assert len(definitions) == 5

    def test_workflow_with_statistics(self):
        """Test workflow with statistics tracking"""
        manager = AgentToolManager()

        tool = Mock(spec=BaseTool)
        tool.name = "bash"
        manager.register_tool(tool)

        # Mock executor for execution
        manager.executor.execute_with_smart_retry = AsyncMock(
            return_value=ToolResult(success=True, output="")
        )

        # Simulate async execution tracking
        async def simulate_execution():
            for i in range(3):
                manager.tool_usage_stats["bash"] += 1

        import asyncio
        asyncio.run(simulate_execution())

        stats = manager.get_usage_statistics()
        assert stats["bash"] == 3

        manager.reset_statistics()
        stats = manager.get_usage_statistics()
        assert stats["bash"] == 0
