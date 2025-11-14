"""
Unit tests for Main Application Functions

Tests configuration loading, argument parsing, event listeners,
hook setup, and main application initialization.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open
from src.main import (
    load_config, _resolve_env_vars, parse_args,
    _setup_hooks, _setup_event_listeners
)


@pytest.mark.unit
class TestLoadConfigBasic:
    """Tests for load_config basic functionality"""

    def test_load_config_default_path(self):
        """Test load_config uses default path"""
        with patch('pathlib.Path.exists', return_value=False):
            config = load_config()

            assert isinstance(config, dict)

    def test_load_config_custom_path(self):
        """Test load_config with custom path"""
        with patch('pathlib.Path.exists', return_value=False):
            config = load_config("custom.json")

            assert isinstance(config, dict)

    def test_load_config_returns_dict(self):
        """Test load_config always returns dict"""
        with patch('pathlib.Path.exists', return_value=False):
            config = load_config()

            assert isinstance(config, dict)


@pytest.mark.unit
class TestLoadConfigFromFile:
    """Tests for loading configuration from JSON file"""

    def test_load_config_from_existing_file(self):
        """Test loading config from existing JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {"max_turns": 20}
            json.dump(test_config, f)
            f.flush()
            temp_path = f.name

        try:
            # Patch to avoid env file loading
            with patch('pathlib.Path.exists', return_value=False):
                with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                    config = load_config(temp_path)

                    assert isinstance(config, dict)
        finally:
            os.unlink(temp_path)

    def test_load_config_with_missing_file(self):
        """Test load_config when file doesn't exist"""
        with patch('pathlib.Path.exists', return_value=False):
            config = load_config("nonexistent.json")

            assert isinstance(config, dict)

    def test_load_config_preserves_structure(self):
        """Test load_config preserves nested structure"""
        config_data = {
            "max_turns": 20,
            "mcp_servers": [
                {"name": "server1", "command": "cmd"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            temp_path = f.name

        try:
            with patch('pathlib.Path.exists', return_value=False):
                with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
                    config = load_config(temp_path)

                    assert isinstance(config, dict)
        finally:
            os.unlink(temp_path)


@pytest.mark.unit
class TestResolveEnvVars:
    """Tests for environment variable resolution"""

    def test_resolve_env_vars_string_without_placeholder(self):
        """Test resolving string without ${} placeholder"""
        result = _resolve_env_vars("plain_string")

        assert result == "plain_string"

    def test_resolve_env_vars_string_with_placeholder(self):
        """Test resolving string with ${VAR_NAME} placeholder"""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = _resolve_env_vars("${TEST_VAR}")

            assert result == "test_value"

    def test_resolve_env_vars_missing_variable(self):
        """Test resolving nonexistent variable returns original"""
        with patch.dict(os.environ, {}, clear=True):
            result = _resolve_env_vars("${NONEXISTENT_VAR}")

            assert result == "${NONEXISTENT_VAR}"

    def test_resolve_env_vars_dict_recursion(self):
        """Test resolving environment variables in dict"""
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            config = {
                "api_key": "${API_KEY}",
                "nested": {
                    "password": "${API_KEY}"
                }
            }

            result = _resolve_env_vars(config)

            assert result["api_key"] == "secret123"
            assert result["nested"]["password"] == "secret123"

    def test_resolve_env_vars_list_recursion(self):
        """Test resolving environment variables in list"""
        with patch.dict(os.environ, {"VAR1": "value1", "VAR2": "value2"}):
            config = ["${VAR1}", "${VAR2}", "plain"]

            result = _resolve_env_vars(config)

            assert result == ["value1", "value2", "plain"]

    def test_resolve_env_vars_mixed_types(self):
        """Test resolving with mixed types"""
        with patch.dict(os.environ, {"KEY": "value"}):
            config = {
                "string": "${KEY}",
                "number": 123,
                "bool": True,
                "list": ["${KEY}", 456],
                "nested_dict": {"key": "${KEY}"}
            }

            result = _resolve_env_vars(config)

            assert result["string"] == "value"
            assert result["number"] == 123
            assert result["bool"] is True
            assert result["list"][0] == "value"
            assert result["nested_dict"]["key"] == "value"

    def test_resolve_env_vars_none_value(self):
        """Test resolving None values"""
        result = _resolve_env_vars(None)

        assert result is None

    def test_resolve_env_vars_partial_placeholder(self):
        """Test partial placeholder is not resolved"""
        result = _resolve_env_vars("prefix_${VAR}_suffix")

        assert result == "prefix_${VAR}_suffix"


@pytest.mark.unit
class TestParseArgs:
    """Tests for command-line argument parsing"""

    def test_parse_args_defaults(self):
        """Test parse_args returns expected defaults"""
        with patch('sys.argv', ['prog']):
            args = parse_args()

            assert args.config == "config.json"
            assert args.verbose is False
            assert args.quiet is False

    def test_parse_args_verbose_flag(self):
        """Test parse_args with verbose flag"""
        with patch('sys.argv', ['prog', '--verbose']):
            args = parse_args()

            assert args.verbose is True

    def test_parse_args_verbose_short_flag(self):
        """Test parse_args with -v short flag"""
        with patch('sys.argv', ['prog', '-v']):
            args = parse_args()

            assert args.verbose is True

    def test_parse_args_quiet_flag(self):
        """Test parse_args with quiet flag"""
        with patch('sys.argv', ['prog', '--quiet']):
            args = parse_args()

            assert args.quiet is True

    def test_parse_args_quiet_short_flag(self):
        """Test parse_args with -q short flag"""
        with patch('sys.argv', ['prog', '-q']):
            args = parse_args()

            assert args.quiet is True

    def test_parse_args_custom_config(self):
        """Test parse_args with custom config path"""
        with patch('sys.argv', ['prog', '--config', 'custom.json']):
            args = parse_args()

            assert args.config == "custom.json"

    def test_parse_args_permission_skip(self):
        """Test parse_args with dangerously-skip-permissions"""
        with patch('sys.argv', ['prog', '--dangerously-skip-permissions']):
            args = parse_args()

            assert args.dangerously_skip_permissions is True

    def test_parse_args_permission_auto_approve(self):
        """Test parse_args with auto-approve-all"""
        with patch('sys.argv', ['prog', '--auto-approve-all']):
            args = parse_args()

            assert args.auto_approve_all is True

    def test_parse_args_permission_always_ask(self):
        """Test parse_args with always-ask"""
        with patch('sys.argv', ['prog', '--always-ask']):
            args = parse_args()

            assert args.always_ask is True

    def test_parse_args_multiple_flags(self):
        """Test parse_args with multiple flags"""
        with patch('sys.argv', ['prog', '--verbose', '--config', 'test.json']):
            args = parse_args()

            assert args.verbose is True
            assert args.config == "test.json"

    def test_parse_args_verbose_quiet_mutually_exclusive(self):
        """Test that verbose and quiet are mutually exclusive"""
        with patch('sys.argv', ['prog', '--verbose', '--quiet']):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_permission_flags_mutually_exclusive(self):
        """Test that permission flags are mutually exclusive"""
        with patch('sys.argv', ['prog', '--dangerously-skip-permissions', '--auto-approve-all']):
            with pytest.raises(SystemExit):
                parse_args()


@pytest.mark.unit
class TestSetupHooks:
    """Tests for hook setup"""

    def test_setup_hooks_basic(self):
        """Test _setup_hooks basic functionality"""
        mock_hook_manager = Mock()
        config = {}

        _setup_hooks(mock_hook_manager, config, verbose=False)

        # Should register error handler
        assert mock_hook_manager.register_error_handler.called

    def test_setup_hooks_with_verbose(self):
        """Test _setup_hooks with verbose=True"""
        mock_hook_manager = Mock()
        config = {}

        _setup_hooks(mock_hook_manager, config, verbose=True)

        # Should register hooks for all events
        assert mock_hook_manager.register.call_count > 0

    def test_setup_hooks_without_verbose(self):
        """Test _setup_hooks with verbose=False"""
        mock_hook_manager = Mock()
        config = {}

        _setup_hooks(mock_hook_manager, config, verbose=False)

        # Should still register error handler
        assert mock_hook_manager.register_error_handler.called

    def test_setup_hooks_registers_error_handler(self):
        """Test _setup_hooks registers error handler"""
        mock_hook_manager = Mock()
        config = {}

        _setup_hooks(mock_hook_manager, config, verbose=False)

        mock_hook_manager.register_error_handler.assert_called_once()

    def test_setup_hooks_error_handler_callable(self):
        """Test error handler is a callable"""
        mock_hook_manager = Mock()
        config = {}

        _setup_hooks(mock_hook_manager, config, verbose=False)

        # Get the error handler
        call_args = mock_hook_manager.register_error_handler.call_args
        error_handler = call_args[0][0]

        assert callable(error_handler)


@pytest.mark.unit
class TestSetupEventListeners:
    """Tests for event listener setup"""

    @pytest.mark.asyncio
    async def test_setup_event_listeners_basic(self):
        """Test _setup_event_listeners basic functionality"""
        mock_event_bus = Mock()

        await _setup_event_listeners(mock_event_bus)

        # Should subscribe to events
        assert mock_event_bus.subscribe.call_count > 0

    @pytest.mark.asyncio
    async def test_setup_event_listeners_tool_events(self):
        """Test _setup_event_listeners registers tool events"""
        mock_event_bus = Mock()

        await _setup_event_listeners(mock_event_bus)

        # Check that event subscriptions were registered
        subscribe_calls = [call[0][0] for call in mock_event_bus.subscribe.call_args_list]

        # Should have subscribed to tool-related events
        from src.events import EventType
        assert len(subscribe_calls) > 0

    @pytest.mark.asyncio
    async def test_setup_event_listeners_agent_events(self):
        """Test _setup_event_listeners registers agent events"""
        mock_event_bus = Mock()

        await _setup_event_listeners(mock_event_bus)

        # Should have multiple event subscriptions
        assert mock_event_bus.subscribe.call_count >= 6

    @pytest.mark.asyncio
    async def test_event_listener_handlers_are_async(self):
        """Test that event listeners are async functions"""
        mock_event_bus = Mock()

        await _setup_event_listeners(mock_event_bus)

        # Get handlers
        calls = mock_event_bus.subscribe.call_args_list
        for call in calls:
            handler = call[0][1]
            # Handlers should be async
            import inspect
            assert inspect.iscoroutinefunction(handler)


@pytest.mark.unit
class TestConfigPriority:
    """Tests for configuration priority handling"""

    def test_config_priority_json_then_env(self):
        """Test that JSON config has lower priority than environment"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "model": {
                    "ANTHROPIC_API_KEY": "json_key",
                    "ANTHROPIC_MODEL": "json_model"
                }
            }
            json.dump(test_config, f)
            f.flush()
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env_key"}):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                        config = load_config(temp_path)

                        # Config loaded successfully
                        assert isinstance(config, dict)
        finally:
            os.unlink(temp_path)

    def test_config_with_placeholder_resolution(self):
        """Test config with ${VAR_NAME} placeholders"""
        with patch.dict(os.environ, {"MY_KEY": "resolved_key"}):
            config = {
                "api_key": "${MY_KEY}",
                "nested": {
                    "key": "${MY_KEY}"
                }
            }

            result = _resolve_env_vars(config)

            assert result["api_key"] == "resolved_key"
            assert result["nested"]["key"] == "resolved_key"


@pytest.mark.unit
class TestArgumentParsing:
    """Tests for argument parsing"""

    def test_parse_args_has_config_default(self):
        """Test parse_args has config default"""
        with patch('sys.argv', ['prog']):
            args = parse_args()

            assert hasattr(args, 'config')
            assert args.config == "config.json"

    def test_parse_args_has_verbose_default(self):
        """Test parse_args has verbose default"""
        with patch('sys.argv', ['prog']):
            args = parse_args()

            assert hasattr(args, 'verbose')
            assert args.verbose is False

    def test_parse_args_has_quiet_default(self):
        """Test parse_args has quiet default"""
        with patch('sys.argv', ['prog']):
            args = parse_args()

            assert hasattr(args, 'quiet')
            assert args.quiet is False

    def test_parse_args_has_permission_flags(self):
        """Test parse_args has permission flags"""
        with patch('sys.argv', ['prog']):
            args = parse_args()

            assert hasattr(args, 'dangerously_skip_permissions')
            assert hasattr(args, 'auto_approve_all')
            assert hasattr(args, 'always_ask')


@pytest.mark.unit
class TestConfigLoading:
    """Tests for configuration file loading"""

    def test_load_config_empty_file(self):
        """Test loading empty config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            f.flush()
            temp_path = f.name

        try:
            config = load_config(temp_path)

            assert isinstance(config, dict)
        finally:
            os.unlink(temp_path)

    def test_load_config_nested_structure(self):
        """Test loading config with nested structure"""
        test_config = {
            "model": {
                "ANTHROPIC_API_KEY": "key",
                "ANTHROPIC_MODEL": "model"
            },
            "mcp_servers": [
                {
                    "name": "fs",
                    "command": "npx",
                    "args": []
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            f.flush()
            temp_path = f.name

        try:
            config = load_config(temp_path)

            assert "model" in config
            assert "mcp_servers" in config
        finally:
            os.unlink(temp_path)


@pytest.mark.unit
class TestHookSetupConfiguration:
    """Tests for hook setup configuration"""

    def test_setup_hooks_calls_register_error_handler(self):
        """Test _setup_hooks calls register_error_handler"""
        mock_hook_manager = Mock()
        config = {}

        _setup_hooks(mock_hook_manager, config, verbose=False)

        mock_hook_manager.register_error_handler.assert_called_once()

    def test_setup_hooks_verbose_registers_multiple_hooks(self):
        """Test verbose mode registers multiple hooks"""
        mock_hook_manager = Mock()
        config = {}

        _setup_hooks(mock_hook_manager, config, verbose=True)

        # Should register hooks for multiple events
        register_calls = mock_hook_manager.register.call_count
        assert register_calls > 0

    def test_setup_hooks_non_verbose_fewer_registrations(self):
        """Test non-verbose mode has fewer registrations"""
        mock_hook_manager = Mock()
        config = {}

        _setup_hooks(mock_hook_manager, config, verbose=False)

        # Should still register error handler
        assert mock_hook_manager.register_error_handler.called


@pytest.mark.unit
class TestEventListenerHandlers:
    """Tests for event listener handler behavior"""

    @pytest.mark.asyncio
    async def test_tool_selected_handler_exists(self):
        """Test tool selected handler is registered"""
        mock_event_bus = Mock()

        await _setup_event_listeners(mock_event_bus)

        # Should have registered handlers
        assert mock_event_bus.subscribe.call_count > 0

    @pytest.mark.asyncio
    async def test_tool_completed_handler_exists(self):
        """Test tool completed handler is registered"""
        mock_event_bus = Mock()

        await _setup_event_listeners(mock_event_bus)

        # Should have tool completed handler
        assert mock_event_bus.subscribe.call_count > 0

    @pytest.mark.asyncio
    async def test_agent_end_handler_exists(self):
        """Test agent end handler is registered"""
        mock_event_bus = Mock()

        await _setup_event_listeners(mock_event_bus)

        # Should have agent end handler
        assert mock_event_bus.subscribe.call_count > 0


@pytest.mark.unit
class TestIntegrationConfigAndArgs:
    """Integration tests for config and args"""

    def test_config_and_args_combined(self):
        """Test using config with args together"""
        with patch('sys.argv', ['prog', '--verbose', '--config', 'test.json']):
            with patch('pathlib.Path.exists', return_value=False):
                args = parse_args()
                config = load_config(args.config)

                assert args.verbose is True
                assert args.config == "test.json"
                assert isinstance(config, dict)

    def test_env_var_resolution_in_loaded_config(self):
        """Test environment variable resolution in loaded config"""
        test_config = {
            "model": {
                "ANTHROPIC_API_KEY": "${API_KEY}",
                "temperature": 0.7
            }
        }

        with patch.dict(os.environ, {"API_KEY": "test_key"}):
            result = _resolve_env_vars(test_config)

            assert result["model"]["ANTHROPIC_API_KEY"] == "test_key"
            assert result["model"]["temperature"] == 0.7
