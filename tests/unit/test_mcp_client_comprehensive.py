"""
Unit tests for MCP Client

Tests MCPClient initialization, server connections, tool management,
tool execution, and availability checking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.mcps.client import MCPClient
from src.mcps.config import MCPServerConfig, MCPTool


@pytest.mark.unit
class TestMCPClientInitialization:
    """Tests for MCPClient initialization"""

    def test_initialization_creates_empty_servers(self):
        """Test that MCPClient initializes with empty servers"""
        client = MCPClient()

        assert client.servers == {}
        assert isinstance(client.servers, dict)

    def test_initialization_creates_empty_tools(self):
        """Test that MCPClient initializes with empty tools"""
        client = MCPClient()

        assert client.tools == {}
        assert isinstance(client.tools, dict)

    def test_initialization_checks_mcp_availability(self):
        """Test that MCPClient checks MCP availability on init"""
        client = MCPClient()

        assert hasattr(client, '_mcp_available')
        assert isinstance(client._mcp_available, bool)

    def test_mcp_availability_returns_boolean(self):
        """Test that _mcp_available is a boolean"""
        client = MCPClient()

        is_available = client._mcp_available
        assert isinstance(is_available, bool)


@pytest.mark.unit
class TestMCPClientAvailabilityCheck:
    """Tests for MCP availability checking"""

    def test_is_available_returns_boolean(self):
        """Test that is_available returns boolean"""
        client = MCPClient()
        result = client.is_available()

        assert isinstance(result, bool)

    def test_is_available_reflects_mcp_installation(self):
        """Test that is_available reflects MCP installation status"""
        client = MCPClient()

        # Should return True if mcp is installed, False otherwise
        # We can't guarantee either, so just verify it's boolean
        assert isinstance(client.is_available(), bool)

    @patch.object(MCPClient, '_check_mcp_availability', return_value=True)
    def test_is_available_true_when_mcp_installed(self, mock_check):
        """Test is_available returns True when MCP is installed"""
        client = MCPClient()

        assert client.is_available() is True

    @patch.object(MCPClient, '_check_mcp_availability', return_value=False)
    def test_is_available_false_when_mcp_not_installed(self, mock_check):
        """Test is_available returns False when MCP is not installed"""
        client = MCPClient()

        assert client.is_available() is False


@pytest.mark.unit
class TestMCPClientConnectionStatus:
    """Tests for MCP client connection status checking"""

    def test_is_connected_returns_boolean(self):
        """Test that is_connected returns boolean"""
        client = MCPClient()
        result = client.is_connected()

        assert isinstance(result, bool)

    def test_is_connected_false_when_no_servers(self):
        """Test that is_connected returns False with no servers"""
        client = MCPClient()

        assert client.is_connected() is False

    def test_is_connected_true_when_servers_present(self):
        """Test that is_connected returns True when servers are present"""
        client = MCPClient()
        # Simulate a connected server
        client.servers["test_server"] = Mock()

        assert client.is_connected() is True

    def test_is_connected_reflects_server_count(self):
        """Test that is_connected reflects server count"""
        client = MCPClient()

        # Initially False
        assert client.is_connected() is False

        # Add server
        client.servers["server1"] = Mock()
        assert client.is_connected() is True

        # Add another
        client.servers["server2"] = Mock()
        assert client.is_connected() is True

        # Remove servers
        client.servers.clear()
        assert client.is_connected() is False


@pytest.mark.unit
class TestMCPClientToolManagement:
    """Tests for tool management in MCPClient"""

    def test_get_tool_definitions_empty(self):
        """Test getting tool definitions when no tools registered"""
        client = MCPClient()
        definitions = client.get_tool_definitions()

        assert definitions == []
        assert isinstance(definitions, list)

    def test_get_tool_definitions_single_tool(self):
        """Test getting tool definitions with single tool"""
        client = MCPClient()
        tool = MCPTool(
            name="read_file",
            description="Read file contents",
            input_schema={},
            server="filesystem"
        )
        client.tools["mcp_filesystem_read_file"] = tool

        definitions = client.get_tool_definitions()

        assert len(definitions) == 1
        assert definitions[0]["name"] == "mcp_filesystem_read_file"
        assert definitions[0]["description"] == "Read file contents"

    def test_get_tool_definitions_multiple_tools(self):
        """Test getting tool definitions with multiple tools"""
        client = MCPClient()

        for i in range(3):
            tool = MCPTool(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={},
                server="server"
            )
            client.tools[f"mcp_server_tool_{i}"] = tool

        definitions = client.get_tool_definitions()

        assert len(definitions) == 3
        assert all("name" in d for d in definitions)
        assert all("description" in d for d in definitions)
        assert all("input_schema" in d for d in definitions)

    def test_get_tool_definitions_includes_input_schema(self):
        """Test that tool definitions include input schema"""
        client = MCPClient()
        schema = {}

        tool = MCPTool(
            name="read",
            description="Read file",
            input_schema=schema,
            server="filesystem"
        )
        client.tools["mcp_fs_read"] = tool

        definitions = client.get_tool_definitions()

        assert definitions[0]["input_schema"] == schema


@pytest.mark.unit
class TestMCPClientToolExecutionErrors:
    """Tests for error handling in tool execution"""

    @pytest.mark.asyncio
    async def test_call_tool_nonexistent_tool(self):
        """Test calling nonexistent tool raises error"""
        client = MCPClient()

        with pytest.raises(ValueError, match="not found"):
            await client.call_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_call_tool_disconnected_server(self):
        """Test calling tool when server not connected"""
        client = MCPClient()
        tool = MCPTool(
            name="read",
            description="Read",
            input_schema={},
            server="filesystem"
        )
        client.tools["mcp_filesystem_read"] = tool
        # Server not added, so it's not connected

        with pytest.raises(ValueError, match="not connected"):
            await client.call_tool("mcp_filesystem_read", {})


@pytest.mark.unit
class TestMCPClientDisconnection:
    """Tests for server disconnection"""

    @pytest.mark.asyncio
    async def test_disconnect_all_empty_servers(self):
        """Test disconnect_all with no servers"""
        client = MCPClient()

        # Should complete without error
        await client.disconnect_all()

        assert client.servers == {}
        assert client.tools == {}

    @pytest.mark.asyncio
    async def test_disconnect_all_clears_servers(self):
        """Test that disconnect_all clears servers"""
        client = MCPClient()
        mock_session = AsyncMock()
        client.servers["test"] = mock_session

        await client.disconnect_all()

        assert client.servers == {}
        assert mock_session.close.called

    @pytest.mark.asyncio
    async def test_disconnect_all_clears_tools(self):
        """Test that disconnect_all clears tools"""
        client = MCPClient()
        tool = MCPTool(
            name="test",
            description="Test",
            input_schema={},
            server="test"
        )
        client.tools["mcp_test_tool"] = tool
        mock_session = AsyncMock()
        client.servers["test"] = mock_session

        await client.disconnect_all()

        assert client.tools == {}

    @pytest.mark.asyncio
    async def test_disconnect_all_handles_session_close_error(self):
        """Test that disconnect_all handles session close errors"""
        client = MCPClient()
        mock_session = AsyncMock()
        mock_session.close.side_effect = Exception("Close failed")
        client.servers["test"] = mock_session

        # Should not raise error
        await client.disconnect_all()

        assert client.servers == {}


@pytest.mark.unit
class TestMCPClientConnectionFlow:
    """Tests for server connection flow"""

    @pytest.mark.asyncio
    async def test_connect_server_disabled(self):
        """Test that disabled servers are not connected"""
        client = MCPClient()
        config = MCPServerConfig(
            name="disabled",
            command="npx",
            args=[],
            enabled=False
        )

        await client.connect_server(config)

        assert "disabled" not in client.servers

    @pytest.mark.asyncio
    async def test_connect_server_mcp_not_available(self):
        """Test connect_server when MCP is not available"""
        with patch.object(MCPClient, '_check_mcp_availability', return_value=False):
            client = MCPClient()
            config = MCPServerConfig(
                name="test",
                command="npx",
                args=[],
                enabled=True
            )

            await client.connect_server(config)

            # Server should not be connected
            assert "test" not in client.servers


@pytest.mark.unit
class TestMCPClientIntegration:
    """Integration tests for MCPClient"""

    @pytest.mark.asyncio
    async def test_complete_workflow_with_tools(self):
        """Test complete workflow: init, add tools, get definitions"""
        client = MCPClient()

        # Add tools
        for i in range(2):
            tool = MCPTool(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema={},
                server="test"
            )
            client.tools[f"mcp_test_tool_{i}"] = tool

        # Get definitions
        definitions = client.get_tool_definitions()

        assert len(definitions) == 2
        assert all(d["description"] for d in definitions)

    def test_server_dict_operations(self):
        """Test server dictionary operations"""
        client = MCPClient()

        # Add server
        mock_session = Mock()
        client.servers["server1"] = mock_session

        assert "server1" in client.servers
        assert client.servers["server1"] == mock_session
        assert client.is_connected() is True

    def test_tool_dict_operations(self):
        """Test tool dictionary operations"""
        client = MCPClient()

        tool = MCPTool(
            name="test",
            description="Test tool",
            input_schema={},
            server="test"
        )
        client.tools["mcp_test_tool"] = tool

        assert "mcp_test_tool" in client.tools
        assert client.tools["mcp_test_tool"].name == "test"

    @pytest.mark.asyncio
    async def test_multiple_server_management(self):
        """Test managing multiple servers"""
        client = MCPClient()

        # Add multiple server mocks
        for i in range(3):
            mock_session = AsyncMock()
            client.servers[f"server_{i}"] = mock_session

        assert len(client.servers) == 3
        assert client.is_connected() is True

        # Disconnect all
        await client.disconnect_all()

        assert len(client.servers) == 0


@pytest.mark.unit
class TestMCPClientEdgeCases:
    """Tests for edge cases in MCPClient"""

    def test_empty_tool_definitions_list(self):
        """Test tool definitions returns empty list when no tools"""
        client = MCPClient()

        definitions = client.get_tool_definitions()

        assert isinstance(definitions, list)
        assert len(definitions) == 0

    def test_tool_name_with_prefix(self):
        """Test that tool names are properly prefixed in definitions"""
        client = MCPClient()

        tool = MCPTool(
            name="original_name",
            description="Test",
            input_schema={},
            server="server_name"
        )
        client.tools["mcp_server_name_original_name"] = tool

        definitions = client.get_tool_definitions()

        assert definitions[0]["name"] == "mcp_server_name_original_name"

    @pytest.mark.asyncio
    async def test_disconnect_all_idempotent(self):
        """Test that disconnect_all can be called multiple times"""
        client = MCPClient()

        # Should succeed multiple times
        await client.disconnect_all()
        await client.disconnect_all()
        await client.disconnect_all()

        assert client.servers == {}
        assert client.tools == {}

    def test_client_state_isolation(self):
        """Test that multiple client instances don't share state"""
        client1 = MCPClient()
        client2 = MCPClient()

        tool = MCPTool(
            name="test",
            description="Test",
            input_schema={},
            server="test"
        )
        client1.tools["tool1"] = tool

        assert "tool1" in client1.tools
        assert "tool1" not in client2.tools


@pytest.mark.unit
class TestMCPClientMockIntegration:
    """Tests using mocks for realistic scenarios"""

    @pytest.mark.asyncio
    async def test_call_tool_with_mock_session(self):
        """Test calling tool with mocked session"""
        client = MCPClient()

        # Setup tool and session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_session.call_tool = AsyncMock(return_value=mock_result)

        tool = MCPTool(
            name="read",
            description="Read file",
            input_schema={},
            server="filesystem"
        )
        client.tools["mcp_filesystem_read"] = tool
        client.servers["filesystem"] = mock_session

        # Call tool
        result = await client.call_tool("mcp_filesystem_read", {"path": "/test"})

        assert result == mock_result
        mock_session.call_tool.assert_called_once_with("read", {"path": "/test"})

    def test_get_definitions_preserves_schema(self):
        """Test that definitions preserve input schema"""
        client = MCPClient()

        schema = {}

        tool = MCPTool(
            name="read",
            description="Read file",
            input_schema=schema,
            server="fs"
        )
        client.tools["mcp_fs_read"] = tool

        definitions = client.get_tool_definitions()

        assert definitions[0]["input_schema"] == schema
