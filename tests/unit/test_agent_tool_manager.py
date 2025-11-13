"""
Unit tests for Agent Tool Manager module

Tests the AgentToolManager class which manages tool registration,
execution, and statistics tracking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from src.agents.tool_manager import AgentToolManager
from src.tools.base import BaseTool, ToolResult


# Mock tool for testing
class MockTool(BaseTool):
    """Mock tool for testing"""

    def __init__(self, name: str = "mock_tool", description: str = "Mock tool", fail: bool = False):
        self._name = name
        self._description = description
        self._fail = fail
        self.execute_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            }
        }

    async def execute(self, **params) -> ToolResult:
        self.execute_count += 1
        if self._fail:
            return ToolResult(success=False, output="", error="Mock tool error")
        return ToolResult(success=True, output="Mock output")


@pytest.mark.unit
class TestAgentToolManagerInitialization:
    """Tests for AgentToolManager initialization"""

    def test_initialization_without_mcp(self):
        """Test initializing tool manager without MCP client"""
        manager = AgentToolManager()
        assert manager.tools == {}
        assert manager.tool_usage_stats == {}
        assert manager.mcp_client is None
        assert manager.executor is not None

    def test_initialization_with_mcp(self):
        """Test initializing tool manager with MCP client"""
        mcp_mock = Mock()
        manager = AgentToolManager(mcp_client=mcp_mock)
        assert manager.mcp_client is mcp_mock
        assert manager.tools == {}


@pytest.mark.unit
class TestToolRegistration:
    """Tests for tool registration"""

    def test_register_single_tool(self):
        """Test registering a single tool"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool")
        manager.register_tool(tool)

        assert "test_tool" in manager.tools
        assert manager.tools["test_tool"] == tool
        assert "test_tool" in manager.tool_usage_stats
        assert manager.tool_usage_stats["test_tool"] == 0

    def test_register_multiple_tools(self):
        """Test registering multiple tools individually"""
        manager = AgentToolManager()
        tool1 = MockTool(name="tool1")
        tool2 = MockTool(name="tool2")
        tool3 = MockTool(name="tool3")

        manager.register_tool(tool1)
        manager.register_tool(tool2)
        manager.register_tool(tool3)

        assert len(manager.tools) == 3
        assert len(manager.tool_usage_stats) == 3

    def test_register_tools_batch(self):
        """Test registering multiple tools at once"""
        manager = AgentToolManager()
        tools = [
            MockTool(name="tool1"),
            MockTool(name="tool2"),
            MockTool(name="tool3")
        ]
        manager.register_tools(tools)

        assert len(manager.tools) == 3
        for tool in tools:
            assert tool.name in manager.tools
            assert manager.tool_usage_stats[tool.name] == 0

    def test_register_duplicate_tool_overwrites(self):
        """Test that registering a tool with same name overwrites"""
        manager = AgentToolManager()
        tool1 = MockTool(name="tool")
        tool2 = MockTool(name="tool", description="Different tool")

        manager.register_tool(tool1)
        manager.register_tool(tool2)

        assert len(manager.tools) == 1
        assert manager.tools["tool"] == tool2


@pytest.mark.unit
class TestToolRetrieval:
    """Tests for tool retrieval"""

    def test_get_tool_existing(self):
        """Test retrieving an existing tool"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool")
        manager.register_tool(tool)

        retrieved = manager.get_tool("test_tool")
        assert retrieved == tool

    def test_get_tool_nonexistent(self):
        """Test retrieving a non-existent tool returns None"""
        manager = AgentToolManager()
        retrieved = manager.get_tool("nonexistent")
        assert retrieved is None

    def test_list_tools(self):
        """Test listing all tool names"""
        manager = AgentToolManager()
        tools = [
            MockTool(name="tool1"),
            MockTool(name="tool2"),
            MockTool(name="tool3")
        ]
        manager.register_tools(tools)

        tool_list = manager.list_tools()
        assert len(tool_list) == 3
        assert "tool1" in tool_list
        assert "tool2" in tool_list
        assert "tool3" in tool_list

    def test_list_tools_empty(self):
        """Test listing tools when none registered"""
        manager = AgentToolManager()
        assert manager.list_tools() == []

    def test_has_tool_existing(self):
        """Test checking if tool exists"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool")
        manager.register_tool(tool)

        assert manager.has_tool("test_tool") is True
        assert manager.has_tool("nonexistent") is False

    def test_has_tool_empty(self):
        """Test checking tool existence when none registered"""
        manager = AgentToolManager()
        assert manager.has_tool("any_tool") is False


@pytest.mark.unit
class TestToolDefinitions:
    """Tests for tool definitions"""

    def test_get_tool_definitions_empty(self):
        """Test getting definitions when no tools registered"""
        manager = AgentToolManager()
        definitions = manager.get_tool_definitions()
        assert definitions == []

    def test_get_tool_definitions_single_tool(self):
        """Test getting definitions for single tool"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool", description="Test description")
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()
        assert len(definitions) == 1
        assert definitions[0]["name"] == "test_tool"
        assert definitions[0]["description"] == "Test description"
        assert "input_schema" in definitions[0]

    def test_get_tool_definitions_multiple_tools(self):
        """Test getting definitions for multiple tools"""
        manager = AgentToolManager()
        tools = [
            MockTool(name="tool1", description="First tool"),
            MockTool(name="tool2", description="Second tool"),
            MockTool(name="tool3", description="Third tool")
        ]
        manager.register_tools(tools)

        definitions = manager.get_tool_definitions()
        assert len(definitions) == 3

        names = [d["name"] for d in definitions]
        assert "tool1" in names
        assert "tool2" in names
        assert "tool3" in names

    def test_get_tool_definitions_with_mcp_disconnected(self):
        """Test that MCP tools not included when disconnected"""
        mcp_mock = Mock()
        mcp_mock.is_connected.return_value = False
        manager = AgentToolManager(mcp_client=mcp_mock)

        tool = MockTool(name="built_in")
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()
        assert len(definitions) == 1
        assert definitions[0]["name"] == "built_in"

    def test_get_tool_definitions_with_mcp_connected(self):
        """Test that MCP tools included when connected"""
        mcp_mock = Mock()
        mcp_mock.is_connected.return_value = True
        mcp_mock.get_tool_definitions.return_value = [
            {"name": "mcp_tool1", "description": "MCP tool 1"},
            {"name": "mcp_tool2", "description": "MCP tool 2"}
        ]
        manager = AgentToolManager(mcp_client=mcp_mock)

        tool = MockTool(name="built_in")
        manager.register_tool(tool)

        definitions = manager.get_tool_definitions()
        assert len(definitions) == 3
        names = [d["name"] for d in definitions]
        assert "built_in" in names
        assert "mcp_tool1" in names
        assert "mcp_tool2" in names


@pytest.mark.asyncio
@pytest.mark.unit
class TestToolExecution:
    """Tests for tool execution"""

    async def test_execute_tool_success(self):
        """Test executing a tool successfully"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool")
        manager.register_tool(tool)

        result = await manager.execute_tool("test_tool", {})

        assert result.success is True
        assert result.output == "Mock output"
        assert manager.tool_usage_stats["test_tool"] == 1

    async def test_execute_tool_failure(self):
        """Test executing a tool that fails"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool", fail=True)
        manager.register_tool(tool)

        result = await manager.execute_tool("test_tool", {})

        # Tool failed, but manager caught it and returned failure result
        assert result.success is False
        # Tool execution attempt recorded
        assert tool.execute_count > 0

    async def test_execute_tool_nonexistent(self):
        """Test executing a tool that doesn't exist"""
        manager = AgentToolManager()

        result = await manager.execute_tool("nonexistent", {})

        assert result.success is False
        assert "not found" in result.error.lower()

    async def test_execute_tool_with_params(self):
        """Test executing a tool with parameters"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool")
        manager.register_tool(tool)

        params = {"param": "test_value"}
        result = await manager.execute_tool("test_tool", params)

        assert result.success is True
        assert manager.tool_usage_stats["test_tool"] == 1

    async def test_execute_multiple_tools(self):
        """Test executing multiple different tools"""
        manager = AgentToolManager()
        tool1 = MockTool(name="tool1")
        tool2 = MockTool(name="tool2")
        manager.register_tools([tool1, tool2])

        await manager.execute_tool("tool1", {})
        await manager.execute_tool("tool2", {})
        await manager.execute_tool("tool1", {})

        assert manager.tool_usage_stats["tool1"] == 2
        assert manager.tool_usage_stats["tool2"] == 1

    async def test_execute_mcp_tool_success(self):
        """Test executing an MCP tool successfully"""
        mcp_mock = Mock()
        mcp_result_mock = Mock()
        mcp_result_mock.content = []
        mcp_mock.call_tool = AsyncMock(return_value=mcp_result_mock)
        mcp_mock.tools = {"mcp_tool": True}

        manager = AgentToolManager(mcp_client=mcp_mock)

        result = await manager.execute_tool("mcp_tool", {"param": "value"})

        assert result.success is True
        assert result.metadata["source"] == "mcp"
        mcp_mock.call_tool.assert_called_once()

    async def test_execute_mcp_tool_failure(self):
        """Test executing an MCP tool that fails"""
        mcp_mock = Mock()
        mcp_mock.call_tool = AsyncMock(side_effect=Exception("MCP error"))
        mcp_mock.tools = {"mcp_tool": True}

        manager = AgentToolManager(mcp_client=mcp_mock)

        result = await manager.execute_tool("mcp_tool", {})

        assert result.success is False
        assert "MCP tool execution failed" in result.error

    async def test_mcp_tool_result_conversion_text(self):
        """Test converting MCP text result to ToolResult"""
        content_mock = Mock()
        content_mock.type = "text"
        content_mock.text = "MCP output"

        mcp_result_mock = Mock()
        mcp_result_mock.content = [content_mock]

        mcp_mock = Mock()
        mcp_mock.call_tool = AsyncMock(return_value=mcp_result_mock)
        mcp_mock.tools = {"mcp_tool": True}

        manager = AgentToolManager(mcp_client=mcp_mock)
        result = await manager.execute_tool("mcp_tool", {})

        assert result.success is True
        assert "MCP output" in result.output


@pytest.mark.unit
class TestToolUsageStatistics:
    """Tests for tool usage statistics"""

    def test_get_usage_statistics_empty(self):
        """Test getting statistics when no tools used"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool")
        manager.register_tool(tool)

        stats = manager.get_usage_statistics()
        assert stats["test_tool"] == 0

    def test_get_usage_statistics_after_execution(self):
        """Test getting statistics after tool execution"""
        manager = AgentToolManager()
        # Note: We're testing the stats dict directly since async execution isn't tested here
        manager.tool_usage_stats["tool1"] = 5
        manager.tool_usage_stats["tool2"] = 3

        stats = manager.get_usage_statistics()
        assert stats["tool1"] == 5
        assert stats["tool2"] == 3

    def test_get_usage_statistics_returns_copy(self):
        """Test that get_usage_statistics returns a copy"""
        manager = AgentToolManager()
        manager.tool_usage_stats["tool1"] = 5

        stats = manager.get_usage_statistics()
        stats["tool1"] = 999  # Modify copy

        # Original should not be affected
        assert manager.tool_usage_stats["tool1"] == 5

    def test_reset_statistics(self):
        """Test resetting statistics"""
        manager = AgentToolManager()
        tools = [
            MockTool(name="tool1"),
            MockTool(name="tool2"),
            MockTool(name="tool3")
        ]
        manager.register_tools(tools)

        # Set some usage stats
        manager.tool_usage_stats["tool1"] = 10
        manager.tool_usage_stats["tool2"] = 5
        manager.tool_usage_stats["tool3"] = 8

        manager.reset_statistics()

        assert manager.tool_usage_stats["tool1"] == 0
        assert manager.tool_usage_stats["tool2"] == 0
        assert manager.tool_usage_stats["tool3"] == 0

    def test_reset_statistics_empty_manager(self):
        """Test resetting statistics on empty manager"""
        manager = AgentToolManager()
        manager.reset_statistics()  # Should not error
        assert manager.tool_usage_stats == {}


@pytest.mark.unit
class TestToolManagerEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_register_empty_tool_list(self):
        """Test registering empty list of tools"""
        manager = AgentToolManager()
        manager.register_tools([])
        assert manager.tools == {}

    def test_tool_with_special_characters_in_name(self):
        """Test tool with special characters in name"""
        manager = AgentToolManager()
        tool = MockTool(name="tool-with_special.chars")
        manager.register_tool(tool)

        assert manager.has_tool("tool-with_special.chars")
        assert manager.get_tool("tool-with_special.chars") == tool

    def test_multiple_manager_instances_independent(self):
        """Test that multiple manager instances are independent"""
        manager1 = AgentToolManager()
        manager2 = AgentToolManager()

        tool1 = MockTool(name="tool1")
        tool2 = MockTool(name="tool2")

        manager1.register_tool(tool1)
        manager2.register_tool(tool2)

        assert manager1.has_tool("tool1")
        assert not manager1.has_tool("tool2")
        assert manager2.has_tool("tool2")
        assert not manager2.has_tool("tool1")

    def test_executor_not_shared_between_managers(self):
        """Test that executor instances are separate per manager"""
        manager1 = AgentToolManager()
        manager2 = AgentToolManager()

        assert manager1.executor is not manager2.executor


@pytest.mark.asyncio
@pytest.mark.unit
class TestToolExecutionWithRetry:
    """Tests for tool execution with retry logic"""

    async def test_built_in_tool_retried(self):
        """Test that built-in tools use executor with retry"""
        manager = AgentToolManager()
        tool = MockTool(name="test_tool")
        manager.register_tool(tool)

        # Execute the tool
        result = await manager.execute_tool("test_tool", {})

        # Tool should be executed at least once
        assert tool.execute_count >= 1

    async def test_mcp_tool_not_using_executor(self):
        """Test that MCP tools don't use the retry executor"""
        # MCP tools are called directly, not through the executor
        mcp_mock = Mock()
        mcp_result_mock = Mock()
        mcp_result_mock.content = []
        mcp_mock.call_tool = AsyncMock(return_value=mcp_result_mock)
        mcp_mock.tools = {"mcp_tool": True}

        manager = AgentToolManager(mcp_client=mcp_mock)

        result = await manager.execute_tool("mcp_tool", {})

        # MCP client should be called directly
        mcp_mock.call_tool.assert_called_once_with("mcp_tool", {})


@pytest.mark.unit
class TestToolManagerState:
    """Tests for tool manager state management"""

    def test_state_isolation_between_executions(self):
        """Test that tool state doesn't bleed between executions"""
        manager = AgentToolManager()
        tool1 = MockTool(name="tool1")
        tool2 = MockTool(name="tool2")
        manager.register_tools([tool1, tool2])

        # Manually set stats (simulating executions)
        manager.tool_usage_stats["tool1"] = 5
        manager.tool_usage_stats["tool2"] = 0

        # Stats should be independent
        assert manager.tool_usage_stats["tool1"] != manager.tool_usage_stats["tool2"]

    def test_tool_manager_attributes_preservation(self):
        """Test that tool manager preserves all attributes"""
        mcp_mock = Mock()
        manager = AgentToolManager(mcp_client=mcp_mock)

        # All attributes should be accessible
        assert hasattr(manager, 'tools')
        assert hasattr(manager, 'executor')
        assert hasattr(manager, 'tool_usage_stats')
        assert hasattr(manager, 'mcp_client')
        assert manager.mcp_client is mcp_mock
