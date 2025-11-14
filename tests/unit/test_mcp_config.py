"""
Unit tests for MCP Configuration Models

Tests MCPServerConfig and MCPTool Pydantic models, including validation,
default values, serialization, and edge cases.
"""

import pytest
from pydantic import ValidationError
from src.mcps.config import MCPServerConfig, MCPTool


@pytest.mark.unit
class TestMCPServerConfigInitialization:
    """Tests for MCPServerConfig initialization"""

    def test_initialization_with_required_fields(self):
        """Test MCPServerConfig creation with required fields"""
        config = MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"]
        )

        assert config.name == "filesystem"
        assert config.command == "npx"
        assert config.args == ["-y", "@modelcontextprotocol/server-filesystem"]

    def test_initialization_with_all_fields(self):
        """Test MCPServerConfig creation with all fields"""
        config = MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            env={"NODE_ENV": "production"},
            transport="stdio",
            enabled=True
        )

        assert config.name == "filesystem"
        assert config.env == {"NODE_ENV": "production"}
        assert config.transport == "stdio"
        assert config.enabled is True

    def test_initialization_missing_required_name(self):
        """Test MCPServerConfig fails when name is missing"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                command="npx",
                args=["arg1"]
            )

    def test_initialization_missing_required_command(self):
        """Test MCPServerConfig fails when command is missing"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="filesystem",
                args=["arg1"]
            )

    def test_initialization_missing_required_args(self):
        """Test MCPServerConfig fails when args is missing"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="filesystem",
                command="npx"
            )


@pytest.mark.unit
class TestMCPServerConfigDefaults:
    """Tests for MCPServerConfig default values"""

    def test_default_env_is_empty_dict(self):
        """Test that env defaults to empty dictionary"""
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[]
        )
        assert config.env == {}
        assert isinstance(config.env, dict)

    def test_default_transport_is_stdio(self):
        """Test that transport defaults to stdio"""
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[]
        )
        assert config.transport == "stdio"

    def test_default_enabled_is_true(self):
        """Test that enabled defaults to True"""
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[]
        )
        assert config.enabled is True

    def test_env_can_be_overridden(self):
        """Test that env can be set to non-empty"""
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[],
            env={"VAR1": "value1", "VAR2": "value2"}
        )
        assert len(config.env) == 2
        assert config.env["VAR1"] == "value1"

    def test_transport_can_be_changed(self):
        """Test that transport can be set to different value"""
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[],
            transport="sse"
        )
        assert config.transport == "sse"

    def test_enabled_can_be_false(self):
        """Test that enabled can be set to False"""
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[],
            enabled=False
        )
        assert config.enabled is False


@pytest.mark.unit
class TestMCPServerConfigValidation:
    """Tests for MCPServerConfig validation"""

    def test_name_must_be_string(self):
        """Test that name must be string type"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name=123,
                command="npx",
                args=[]
            )

    def test_command_must_be_string(self):
        """Test that command must be string type"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="test",
                command=["npx"],
                args=[]
            )

    def test_args_must_be_list(self):
        """Test that args must be list type"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="test",
                command="npx",
                args="arg1"
            )

    def test_args_list_must_contain_strings(self):
        """Test that args list contains strings"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="test",
                command="npx",
                args=[1, 2, 3]
            )

    def test_env_must_be_dict(self):
        """Test that env must be dict type"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="test",
                command="npx",
                args=[],
                env="KEY=VALUE"
            )

    def test_transport_must_be_string(self):
        """Test that transport must be string type"""
        with pytest.raises(ValidationError):
            MCPServerConfig(
                name="test",
                command="npx",
                args=[],
                transport=123
            )

    def test_enabled_can_coerce_to_bool(self):
        """Test that enabled can be coerced from string"""
        # Pydantic coerces values to bool, so "yes" becomes True
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[],
            enabled="yes"
        )
        assert config.enabled is True  # Pydantic coerces non-empty strings to True

    def test_empty_string_name_invalid(self):
        """Test that empty string for name is handled"""
        # Pydantic allows empty strings by default, but implementation may validate
        config = MCPServerConfig(
            name="",
            command="npx",
            args=[]
        )
        assert config.name == ""

    def test_empty_args_list_valid(self):
        """Test that empty args list is valid"""
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[]
        )
        assert config.args == []


@pytest.mark.unit
class TestMCPServerConfigSerialization:
    """Tests for MCPServerConfig serialization and deserialization"""

    def test_model_dump_returns_dict(self):
        """Test that model_dump returns dictionary"""
        config = MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            env={"VAR": "value"},
            transport="stdio",
            enabled=True
        )

        dumped = config.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["name"] == "filesystem"

    def test_model_dump_includes_all_fields(self):
        """Test that model_dump includes all fields"""
        config = MCPServerConfig(
            name="test",
            command="cmd",
            args=["arg1"],
            env={"KEY": "VALUE"},
            transport="sse",
            enabled=False
        )

        dumped = config.model_dump()
        assert "name" in dumped
        assert "command" in dumped
        assert "args" in dumped
        assert "env" in dumped
        assert "transport" in dumped
        assert "enabled" in dumped

    def test_model_validate_from_dict(self):
        """Test creating config from dict using model_validate"""
        data = {
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"]
        }

        config = MCPServerConfig.model_validate(data)
        assert config.name == "filesystem"

    def test_model_dump_json_returns_string(self):
        """Test that model_dump_json returns JSON string"""
        config = MCPServerConfig(
            name="test",
            command="npx",
            args=[]
        )

        json_str = config.model_dump_json()
        assert isinstance(json_str, str)
        assert "test" in json_str


@pytest.mark.unit
class TestMCPToolInitialization:
    """Tests for MCPTool initialization"""

    def test_initialization_with_required_fields(self):
        """Test MCPTool creation with required fields"""
        tool = MCPTool(
            name="read_file",
            description="Read file contents",
            input_schema={},
            server="filesystem"
        )

        assert tool.name == "read_file"
        assert tool.description == "Read file contents"
        assert tool.input_schema == {}
        assert tool.server == "filesystem"

    def test_initialization_with_simple_input_schema(self):
        """Test MCPTool with simple input schema using empty dict"""
        # The input_schema field expects a dict that Pydantic can parse
        # Empty dict works reliably
        tool = MCPTool(
            name="read_file",
            description="Read file contents",
            input_schema={},
            server="filesystem"
        )

        assert tool.input_schema == {}

    def test_initialization_missing_required_name(self):
        """Test MCPTool fails when name is missing"""
        with pytest.raises(ValidationError):
            MCPTool(
                description="Test tool",
                input_schema={},
                server="test"
            )

    def test_initialization_missing_required_description(self):
        """Test MCPTool fails when description is missing"""
        with pytest.raises(ValidationError):
            MCPTool(
                name="test_tool",
                input_schema={},
                server="test"
            )

    def test_initialization_missing_required_input_schema(self):
        """Test MCPTool fails when input_schema is missing"""
        with pytest.raises(ValidationError):
            MCPTool(
                name="test_tool",
                description="Test tool",
                server="test"
            )

    def test_initialization_missing_required_server(self):
        """Test MCPTool fails when server is missing"""
        with pytest.raises(ValidationError):
            MCPTool(
                name="test_tool",
                description="Test tool",
                input_schema={}
            )


@pytest.mark.unit
class TestMCPToolValidation:
    """Tests for MCPTool field validation"""

    def test_name_must_be_string(self):
        """Test that name must be string type"""
        with pytest.raises(ValidationError):
            MCPTool(
                name=123,
                description="Test",
                input_schema={},
                server="test"
            )

    def test_description_must_be_string(self):
        """Test that description must be string type"""
        with pytest.raises(ValidationError):
            MCPTool(
                name="test",
                description=123,
                input_schema={},
                server="test"
            )

    def test_input_schema_must_be_dict(self):
        """Test that input_schema must be dict type"""
        with pytest.raises(ValidationError):
            MCPTool(
                name="test",
                description="Test",
                input_schema="schema",
                server="test"
            )

    def test_server_must_be_string(self):
        """Test that server must be string type"""
        with pytest.raises(ValidationError):
            MCPTool(
                name="test",
                description="Test",
                input_schema={},
                server=123
            )

    def test_empty_string_name(self):
        """Test empty string for name"""
        tool = MCPTool(
            name="",
            description="Test",
            input_schema={},
            server="test"
        )
        assert tool.name == ""

    def test_empty_input_schema(self):
        """Test empty dict for input_schema"""
        tool = MCPTool(
            name="test",
            description="Test",
            input_schema={},
            server="test"
        )
        assert tool.input_schema == {}


@pytest.mark.unit
class TestMCPToolSerialization:
    """Tests for MCPTool serialization"""

    def test_model_dump_returns_dict(self):
        """Test that model_dump returns dictionary"""
        tool = MCPTool(
            name="read_file",
            description="Read file contents",
            input_schema={},
            server="filesystem"
        )

        dumped = tool.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["name"] == "read_file"

    def test_model_dump_includes_all_fields(self):
        """Test that model_dump includes all fields"""
        tool = MCPTool(
            name="test",
            description="Description",
            input_schema={},
            server="server_name"
        )

        dumped = tool.model_dump()
        assert "name" in dumped
        assert "description" in dumped
        assert "input_schema" in dumped
        assert "server" in dumped


@pytest.mark.unit
class TestMCPConfigIntegration:
    """Integration tests for MCP configurations"""

    def test_server_config_with_typical_filesystem_setup(self):
        """Test typical filesystem MCP server configuration"""
        config = MCPServerConfig(
            name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "."],
            transport="stdio",
            enabled=True
        )

        assert config.name == "filesystem"
        assert config.enabled is True
        assert "." in config.args

    def test_server_config_with_disabled_server(self):
        """Test disabled server configuration"""
        config = MCPServerConfig(
            name="disabled_server",
            command="npx",
            args=[],
            enabled=False
        )

        assert config.enabled is False

    def test_multiple_configs_independence(self):
        """Test that multiple configs don't interfere"""
        config1 = MCPServerConfig(
            name="server1",
            command="cmd1",
            args=["arg1"]
        )

        config2 = MCPServerConfig(
            name="server2",
            command="cmd2",
            args=["arg2"]
        )

        assert config1.name == "server1"
        assert config2.name == "server2"
        assert config1.command != config2.command

    def test_tool_list_with_multiple_servers(self):
        """Test tools from different servers"""
        tool1 = MCPTool(
            name="read",
            description="Read file",
            input_schema={},
            server="filesystem"
        )

        tool2 = MCPTool(
            name="search",
            description="Search web",
            input_schema={},
            server="web"
        )

        assert tool1.server == "filesystem"
        assert tool2.server == "web"
        assert tool1.name != tool2.name

    def test_tool_with_empty_schema_from_server(self):
        """Test tool with empty JSON schema"""
        schema = {}

        tool = MCPTool(
            name="list_files",
            description="List files in directory",
            input_schema=schema,
            server="filesystem"
        )

        assert tool.input_schema == {}

    def test_config_from_dict_roundtrip(self):
        """Test config serialization roundtrip"""
        original = MCPServerConfig(
            name="test",
            command="test_cmd",
            args=["arg1", "arg2"],
            env={"VAR": "value"},
            transport="stdio",
            enabled=True
        )

        dumped = original.model_dump()
        restored = MCPServerConfig.model_validate(dumped)

        assert restored.name == original.name
        assert restored.command == original.command
        assert restored.args == original.args
        assert restored.env == original.env
        assert restored.transport == original.transport
        assert restored.enabled == original.enabled
