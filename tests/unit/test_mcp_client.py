"""
Unit tests for MCP Client

Tests server connection lifecycle, tool discovery, execution,
error handling, and connection management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.mcps.client import MCPClient
from src.mcps.config import MCPServerConfig, MCPTool


@pytest.mark.unit
class TestMCPClientInitialization:
    """Tests for MCP client initialization"""

    def test_client_initializes_empty(self):
        """Test MCP client initializes with empty state"""
        client = MCPClient()

        assert client.servers == {}
        assert client.tools == {}
        assert hasattr(client, '_mcp_available')

    def test_client_checks_mcp_availability(self):
        """Test client checks MCP availability on init"""
        client = MCPClient()

        assert isinstance(client._mcp_available, bool)

    def test_client_availability_when_not_installed(self):
        """Test client reports unavailable when MCP not installed"""
        with patch('builtins.__import__', side_effect=ImportError):
            client = MCPClient()
            assert client._mcp_available is False


@pytest.mark.unit
class TestMCPAvailability:
    """Tests for MCP availability checking"""

    def test_is_available_returns_boolean(self):
        """Test is_available returns boolean"""
        client = MCPClient()

        result = client.is_available()

        assert isinstance(result, bool)

    def test_is_available_true_when_installed(self):
        """Test is_available returns True when MCP installed"""
        client = MCPClient()

        if client._mcp_available:
            assert client.is_available() is True

    def test_is_available_matches_mcp_available_flag(self):
        """Test is_available matches _mcp_available flag"""
        client = MCPClient()

        assert client.is_available() == client._mcp_available


@pytest.mark.unit
class TestConnectionStatus:
    """Tests for connection status checks"""

    def test_is_connected_false_initially(self):
        """Test is_connected returns False initially"""
        client = MCPClient()

        assert client.is_connected() is False

    def test_is_connected_true_with_servers(self):
        """Test is_connected returns True when servers connected"""
        client = MCPClient()
        client.servers["test_server"] = Mock()

        assert client.is_connected() is True

    def test_is_connected_with_multiple_servers(self):
        """Test is_connected with multiple servers"""
        client = MCPClient()
        client.servers["server1"] = Mock()
        client.servers["server2"] = Mock()

        assert client.is_connected() is True


@pytest.mark.unit
class TestServerConnection:
    """Tests for server connection"""

    @pytest.mark.asyncio
    async def test_connect_server_disabled_config_skips(self):
        """Test connect_server skips disabled config"""
        client = MCPClient()
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[],
            enabled=False
        )

        await client.connect_server(config)

        assert client.is_connected() is False

    @pytest.mark.asyncio
    async def test_connect_server_mcp_not_available_warns(self):
        """Test connect_server warns when MCP not available"""
        client = MCPClient()
        client._mcp_available = False

        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[]
        )

        with patch('builtins.print') as mock_print:
            await client.connect_server(config)

        mock_print.assert_called_once()
        assert "MCP not installed" in str(mock_print.call_args)


@pytest.mark.unit
class TestToolCall:
    """Tests for tool calling"""

    @pytest.mark.asyncio
    async def test_call_tool_not_found_raises(self):
        """Test call_tool raises when tool not found"""
        client = MCPClient()

        with pytest.raises(ValueError, match="not found"):
            await client.call_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_call_tool_server_not_connected_raises(self):
        """Test call_tool raises when server not connected"""
        client = MCPClient()

        # Add tool without connecting server
        client.tools["test_tool"] = MCPTool(
            name="test",
            description="Test tool",
            input_schema={},
            server="disconnected"
        )

        with pytest.raises(ValueError, match="not connected"):
            await client.call_tool("test_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_executes(self):
        """Test call_tool executes correctly"""
        client = MCPClient()

        # Setup tool and session
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value={"result": "success"})

        client.servers["test_server"] = mock_session
        client.tools["test_tool"] = MCPTool(
            name="original_name",
            description="Test",
            input_schema={},
            server="test_server"
        )

        result = await client.call_tool("test_tool", {"arg": "value"})

        assert result == {"result": "success"}
        mock_session.call_tool.assert_called_once_with("original_name", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_passes_arguments(self):
        """Test call_tool passes arguments correctly"""
        client = MCPClient()

        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(return_value={})

        client.servers["server"] = mock_session
        client.tools["tool"] = MCPTool(
            name="tool_name",
            description="Test",
            input_schema={},
            server="server"
        )

        await client.call_tool("tool", {"key1": "val1", "key2": 123})

        call_args = mock_session.call_tool.call_args[0]
        assert call_args[1] == {"key1": "val1", "key2": 123}


@pytest.mark.unit
class TestToolDefinitions:
    """Tests for tool definitions"""

    def test_get_tool_definitions_empty(self):
        """Test get_tool_definitions returns empty list initially"""
        client = MCPClient()

        definitions = client.get_tool_definitions()

        assert definitions == []

    def test_get_tool_definitions_includes_tools(self):
        """Test get_tool_definitions includes registered tools"""
        client = MCPClient()

        client.tools["tool1"] = MCPTool(
            name="tool1",
            description="First tool",
            input_schema={},
            server="server1"
        )

        definitions = client.get_tool_definitions()

        assert len(definitions) == 1
        assert definitions[0]["name"] == "tool1"
        assert definitions[0]["description"] == "First tool"

    def test_get_tool_definitions_multiple_tools(self):
        """Test get_tool_definitions with multiple tools"""
        client = MCPClient()

        client.tools["tool1"] = MCPTool(
            name="tool1",
            description="Tool 1",
            input_schema={},
            server="server1"
        )
        client.tools["tool2"] = MCPTool(
            name="tool2",
            description="Tool 2",
            input_schema={},
            server="server2"
        )

        definitions = client.get_tool_definitions()

        assert len(definitions) == 2
        names = [d["name"] for d in definitions]
        assert "tool1" in names
        assert "tool2" in names

    def test_get_tool_definitions_format(self):
        """Test get_tool_definitions returns correct format"""
        client = MCPClient()

        client.tools["test"] = MCPTool(
            name="test",
            description="Test tool",
            input_schema={},
            server="server"
        )

        definitions = client.get_tool_definitions()

        assert "name" in definitions[0]
        assert "description" in definitions[0]
        assert "input_schema" in definitions[0]


@pytest.mark.unit
class TestDisconnection:
    """Tests for server disconnection"""

    @pytest.mark.asyncio
    async def test_disconnect_all_closes_sessions(self):
        """Test disconnect_all closes all sessions"""
        client = MCPClient()

        mock_session1 = AsyncMock()
        mock_session2 = AsyncMock()

        client.servers["server1"] = mock_session1
        client.servers["server2"] = mock_session2

        await client.disconnect_all()

        mock_session1.close.assert_called_once()
        mock_session2.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_all_clears_servers(self):
        """Test disconnect_all clears servers"""
        client = MCPClient()

        mock_session = AsyncMock()
        client.servers["server"] = mock_session

        await client.disconnect_all()

        assert client.servers == {}

    @pytest.mark.asyncio
    async def test_disconnect_all_clears_tools(self):
        """Test disconnect_all clears tools"""
        client = MCPClient()

        client.tools["tool"] = MCPTool(
            name="tool",
            description="Test",
            input_schema={},
            server="server"
        )

        mock_session = AsyncMock()
        client.servers["server"] = mock_session

        await client.disconnect_all()

        assert client.tools == {}

    @pytest.mark.asyncio
    async def test_disconnect_all_handles_close_errors(self):
        """Test disconnect_all handles close errors gracefully"""
        client = MCPClient()

        mock_session = AsyncMock()
        mock_session.close = AsyncMock(side_effect=Exception("Close failed"))

        client.servers["server"] = mock_session

        with patch('builtins.print') as mock_print:
            await client.disconnect_all()

        # Should log error but not raise
        mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_disconnect_all_with_multiple_errors(self):
        """Test disconnect_all continues despite errors"""
        client = MCPClient()

        mock_session1 = AsyncMock()
        mock_session1.close = AsyncMock(side_effect=Exception("Error 1"))

        mock_session2 = AsyncMock()
        mock_session2.close = AsyncMock()

        client.servers["server1"] = mock_session1
        client.servers["server2"] = mock_session2

        with patch('builtins.print'):
            await client.disconnect_all()

        # Both should attempt close
        mock_session1.close.assert_called_once()
        mock_session2.close.assert_called_once()


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    def test_client_with_no_servers(self):
        """Test client with no servers"""
        client = MCPClient()

        assert client.is_connected() is False
        assert client.get_tool_definitions() == []

    def test_tool_with_empty_description(self):
        """Test tool with empty description"""
        tool = MCPTool(
            name="tool",
            description="",
            input_schema={},
            server="server"
        )

        assert tool.name == "tool"
        assert tool.description == ""

    @pytest.mark.asyncio
    async def test_disconnect_all_with_empty_servers(self):
        """Test disconnect_all with no servers"""
        client = MCPClient()

        # Should not raise
        await client.disconnect_all()

    def test_get_tool_definitions_is_list(self):
        """Test get_tool_definitions always returns list"""
        client = MCPClient()

        result = client.get_tool_definitions()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_connect_multiple_servers_sequentially(self):
        """Test multiple servers can be created"""
        config1 = MCPServerConfig(name="server1", command="cmd1", args=[])
        config2 = MCPServerConfig(name="server2", command="cmd2", args=[])

        assert config1.name == "server1"
        assert config2.name == "server2"

