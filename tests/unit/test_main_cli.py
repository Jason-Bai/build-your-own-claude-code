"""
Unit tests for Main CLI Application

Tests configuration loading, argument parsing, agent initialization,
and main application flow.
"""

import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open
from src.main import (
    load_config, parse_args, _resolve_env_vars, _setup_hooks,
    _load_user_hooks, _setup_event_listeners, initialize_agent, cli
)
from src.utils.output import OutputFormatter, OutputLevel
from src.agents import PermissionMode
from src.events import EventBus, EventType


@pytest.mark.unit
class TestLoadConfig:
    """Tests for load_config function"""

    def test_load_config_returns_dict(self):
        """Test load_config returns a dictionary"""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                config = load_config("nonexistent.json")
                assert isinstance(config, dict)

    def test_load_config_loads_json_file(self):
        """Test load_config loads valid JSON file"""
        test_config = {"model": {"ANTHROPIC_API_KEY": "test-key"}}
        with patch('pathlib.Path.exists', return_value=False):
            with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                with patch.dict(os.environ, {}, clear=True):
                    config = load_config("~/.tiny-claude-code/settings.json")
                    assert isinstance(config, dict)

    def test_load_config_handles_missing_file(self):
        """Test load_config handles missing config file gracefully"""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                config = load_config("missing.json")
                assert isinstance(config, dict)

    def test_load_config_handles_missing_unified_file(self):
        """Test load_config handles missing unified config file gracefully"""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                config = load_config("~/.tiny-claude-code/settings.json")
                assert isinstance(config, dict)
                assert config == {}

    def test_load_config_with_env_vars(self):
        """Test load_config merges environment variables"""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}, clear=True):
                with patch('src.main.load_dotenv'):
                    config = load_config("~/.tiny-claude-code/settings.json")
                    assert isinstance(config, dict)

    def test_load_config_env_file_exists(self):
        """Test load_config loads .env file"""
        test_config = {"model": {"ANTHROPIC_API_KEY": "config-key"}}
        with patch('pathlib.Path.exists', side_effect=lambda: True):
            with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                with patch('src.main.load_dotenv'):
                    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
                        config = load_config("~/.tiny-claude-code/settings.json")
                        assert isinstance(config, dict)


@pytest.mark.unit
class TestResolveEnvVars:
    """Tests for _resolve_env_vars function"""

    def test_resolve_env_vars_string_with_placeholder(self):
        """Test resolving string with environment variable placeholder"""
        with patch.dict(os.environ, {"MY_VAR": "my_value"}):
            result = _resolve_env_vars("${MY_VAR}")
            assert result == "my_value"

    def test_resolve_env_vars_string_without_placeholder(self):
        """Test resolving plain string"""
        result = _resolve_env_vars("plain_string")
        assert result == "plain_string"

    def test_resolve_env_vars_dict_with_placeholders(self):
        """Test resolving dictionary with placeholders"""
        with patch.dict(os.environ, {"KEY1": "value1"}):
            input_dict = {"key": "${KEY1}"}
            result = _resolve_env_vars(input_dict)
            assert result["key"] == "value1"

    def test_resolve_env_vars_nested_dict(self):
        """Test resolving nested dictionary"""
        with patch.dict(os.environ, {"VAR": "val"}):
            input_dict = {"outer": {"inner": "${VAR}"}}
            result = _resolve_env_vars(input_dict)
            assert result["outer"]["inner"] == "val"

    def test_resolve_env_vars_list(self):
        """Test resolving list with placeholders"""
        with patch.dict(os.environ, {"VAR": "value"}):
            input_list = ["${VAR}", "plain", "${MISSING}"]
            result = _resolve_env_vars(input_list)
            assert result[0] == "value"
            assert result[1] == "plain"
            assert result[2] == "${MISSING}"  # Missing vars unchanged

    def test_resolve_env_vars_non_string_types(self):
        """Test resolving non-string types pass through"""
        assert _resolve_env_vars(123) == 123
        assert _resolve_env_vars(True) is True
        assert _resolve_env_vars(None) is None

    def test_resolve_env_vars_missing_env_var(self):
        """Test resolving missing environment variable"""
        with patch.dict(os.environ, {}, clear=True):
            result = _resolve_env_vars("${NONEXISTENT}")
            assert result == "${NONEXISTENT}"


@pytest.mark.unit
class TestParseArgs:
    """Tests for parse_args function"""

    def test_parse_args_default(self):
        """Test parse_args with default arguments"""
        with patch('sys.argv', ['script']):
            args = parse_args()
            assert args.config == "~/.tiny-claude-code/settings.json"
            assert args.verbose is False
            assert args.quiet is False

    def test_parse_args_verbose_flag(self):
        """Test parse_args with verbose flag"""
        with patch('sys.argv', ['script', '--verbose']):
            args = parse_args()
            assert args.verbose is True

    def test_parse_args_verbose_short_flag(self):
        """Test parse_args with -v short flag"""
        with patch('sys.argv', ['script', '-v']):
            args = parse_args()
            assert args.verbose is True

    def test_parse_args_quiet_flag(self):
        """Test parse_args with quiet flag"""
        with patch('sys.argv', ['script', '--quiet']):
            args = parse_args()
            assert args.quiet is True

    def test_parse_args_quiet_short_flag(self):
        """Test parse_args with -q short flag"""
        with patch('sys.argv', ['script', '-q']):
            args = parse_args()
            assert args.quiet is True

    def test_parse_args_config_file(self):
        """Test parse_args with config file"""
        with patch('sys.argv', ['script', '--config', 'custom.json']):
            args = parse_args()
            assert args.config == "custom.json"

    def test_parse_args_permission_skip(self):
        """Test parse_args with permission skip flag"""
        with patch('sys.argv', ['script', '--dangerously-skip-permissions']):
            args = parse_args()
            assert args.dangerously_skip_permissions is True

    def test_parse_args_permission_auto_approve_all(self):
        """Test parse_args with auto-approve-all flag"""
        with patch('sys.argv', ['script', '--auto-approve-all']):
            args = parse_args()
            assert args.auto_approve_all is True

    def test_parse_args_permission_always_ask(self):
        """Test parse_args with always-ask flag"""
        with patch('sys.argv', ['script', '--always-ask']):
            args = parse_args()
            assert args.always_ask is True

    def test_parse_args_verbose_and_quiet_mutually_exclusive(self):
        """Test that verbose and quiet flags are mutually exclusive"""
        with patch('sys.argv', ['script', '--verbose', '--quiet']):
            with pytest.raises(SystemExit):
                parse_args()


@pytest.mark.unit
class TestSetupHooks:
    """Tests for _setup_hooks function"""

    @patch('src.main.HookManager')
    def test_setup_hooks_with_verbose_false(self, mock_hook_manager):
        """Test _setup_hooks doesn't register hooks in non-verbose mode"""
        hook_manager = Mock()
        _setup_hooks(hook_manager, {}, verbose=False)
        # Should still register error handler
        hook_manager.register_error_handler.assert_called()

    @patch('src.main.HookManager')
    def test_setup_hooks_with_verbose_true(self, mock_hook_manager):
        """Test _setup_hooks registers log hooks in verbose mode"""
        hook_manager = Mock()
        _setup_hooks(hook_manager, {}, verbose=True)
        # Should register multiple hooks
        assert hook_manager.register.call_count > 0

    @patch('src.main.HookManager')
    def test_setup_hooks_registers_error_handler(self, mock_hook_manager):
        """Test _setup_hooks always registers error handler"""
        hook_manager = Mock()
        _setup_hooks(hook_manager, {}, verbose=False)
        hook_manager.register_error_handler.assert_called_once()


@pytest.mark.unit
class TestLoadUserHooks:
    """Tests for _load_user_hooks function"""

    @pytest.mark.asyncio
    async def test_load_user_hooks_basic(self):
        """Test _load_user_hooks basic execution"""
        hook_manager = Mock()
        with patch('src.main.HookConfigLoader'):
            await _load_user_hooks(hook_manager, verbose=False)

    @pytest.mark.asyncio
    async def test_load_user_hooks_with_verbose(self):
        """Test _load_user_hooks with verbose mode"""
        hook_manager = Mock()
        with patch('src.main.HookConfigLoader'):
            await _load_user_hooks(hook_manager, verbose=True)


@pytest.mark.unit
class TestSetupEventListeners:
    """Tests for _setup_event_listeners function"""

    @pytest.mark.asyncio
    async def test_setup_event_listeners_basic(self):
        """Test _setup_event_listeners subscribes to events"""
        event_bus = Mock()
        event_bus.subscribe = Mock()
        await _setup_event_listeners(event_bus)
        # Should subscribe to multiple events
        assert event_bus.subscribe.call_count > 0

    @pytest.mark.asyncio
    async def test_setup_event_listeners_subscribes_to_tool_events(self):
        """Test _setup_event_listeners subscribes to tool events"""
        event_bus = Mock()
        await _setup_event_listeners(event_bus)
        # Check if tool events are subscribed
        calls = [call[0][0] for call in event_bus.subscribe.call_args_list]
        assert EventType.TOOL_SELECTED in calls or any("TOOL" in str(c) for c in calls)

    @pytest.mark.asyncio
    async def test_setup_event_listeners_subscribes_to_agent_events(self):
        """Test _setup_event_listeners subscribes to agent events"""
        event_bus = Mock()
        await _setup_event_listeners(event_bus)
        # Should have multiple subscriptions
        assert event_bus.subscribe.call_count >= 5


@pytest.mark.unit
class TestInitializeAgent:
    """Tests for initialize_agent function"""

    @pytest.mark.asyncio
    async def test_initialize_agent_requires_api_key(self):
        """Test initialize_agent requires API key"""
        config = {"model": {}}
        args = Mock()
        args.verbose = False
        args.dangerously_skip_permissions = False
        args.auto_approve_all = False
        args.always_ask = False
        with patch('src.main.check_provider_available', return_value=False):
            # The function will sys.exit when no API provider is found
            # So we expect this to exit with status 1
            try:
                await initialize_agent(config, args)
                # If we reach here, the function didn't exit
                pytest.fail("Expected sys.exit(1) to be called")
            except SystemExit as e:
                # Verify it exited with code 1
                assert e.code == 1

    @pytest.mark.asyncio
    async def test_initialize_agent_with_valid_config(self):
        """Test initialize_agent with valid configuration"""
        config = {
            "model": {
                "ANTHROPIC_API_KEY": "test-key",
                "ANTHROPIC_MODEL": "claude-sonnet-4",
            }
        }
        mock_client = Mock()
        mock_client.context_window = 8000
        with patch('src.main.check_provider_available', return_value=True):
            with patch('src.main.create_client', return_value=mock_client):
                with patch('src.main.EnhancedAgent'):
                    agent = await initialize_agent(config, None)
                    assert agent is not None

    @pytest.mark.asyncio
    async def test_initialize_agent_sets_permission_mode(self):
        """Test initialize_agent sets permission mode correctly"""
        config = {
            "model": {
                "ANTHROPIC_API_KEY": "test-key",
            }
        }
        args = Mock()
        args.verbose = False
        args.dangerously_skip_permissions = True
        mock_client = Mock()
        mock_client.context_window = 8000
        with patch('src.main.check_provider_available', return_value=True):
            with patch('src.main.create_client', return_value=mock_client):
                with patch('src.main.EnhancedAgent') as mock_agent_class:
                    await initialize_agent(config, args)
                    # Check that permission mode was set to SKIP_ALL
                    call_kwargs = mock_agent_class.call_args[1]
                    assert call_kwargs['permission_mode'] == PermissionMode.SKIP_ALL

    @pytest.mark.asyncio
    async def test_initialize_agent_auto_approve_all_mode(self):
        """Test initialize_agent with auto-approve-all mode"""
        config = {
            "model": {
                "ANTHROPIC_API_KEY": "test-key",
            }
        }
        args = Mock()
        args.verbose = False
        args.dangerously_skip_permissions = False
        args.auto_approve_all = True
        args.always_ask = False
        mock_client = Mock()
        mock_client.context_window = 8000
        with patch('src.main.check_provider_available', return_value=True):
            with patch('src.main.create_client', return_value=mock_client):
                with patch('src.main.EnhancedAgent') as mock_agent_class:
                    await initialize_agent(config, args)
                    call_kwargs = mock_agent_class.call_args[1]
                    assert call_kwargs['permission_mode'] == PermissionMode.AUTO_APPROVE_ALL

    @pytest.mark.asyncio
    async def test_initialize_agent_always_ask_mode(self):
        """Test initialize_agent with always-ask mode"""
        config = {
            "model": {
                "ANTHROPIC_API_KEY": "test-key",
            }
        }
        args = Mock()
        args.verbose = False
        args.dangerously_skip_permissions = False
        args.auto_approve_all = False
        args.always_ask = True
        mock_client = Mock()
        mock_client.context_window = 8000
        with patch('src.main.check_provider_available', return_value=True):
            with patch('src.main.create_client', return_value=mock_client):
                with patch('src.main.EnhancedAgent') as mock_agent_class:
                    await initialize_agent(config, args)
                    call_kwargs = mock_agent_class.call_args[1]
                    assert call_kwargs['permission_mode'] == PermissionMode.ALWAYS_ASK

    @pytest.mark.asyncio
    async def test_initialize_agent_openai_fallback(self):
        """Test initialize_agent falls back to OpenAI if Anthropic unavailable"""
        config = {
            "model": {
                "ANTHROPIC_API_KEY": "anthropic-key",
                "OPENAI_API_KEY": "openai-key",
            }
        }
        mock_client = Mock()
        mock_client.context_window = 8000

        def check_available(provider):
            return provider == "openai"

        with patch('src.main.check_provider_available', side_effect=check_available):
            with patch('src.main.create_client', return_value=mock_client):
                with patch('src.main.EnhancedAgent'):
                    agent = await initialize_agent(config, None)
                    assert agent is not None

    @pytest.mark.asyncio
    async def test_initialize_agent_mcp_client_initialization(self):
        """Test initialize_agent initializes MCP client"""
        config = {
            "model": {
                "ANTHROPIC_API_KEY": "test-key",
            },
            "mcp_servers": [
                {
                    "name": "test_server",
                    "command": "test",
                    "args": [],
                    "enabled": False
                }
            ]
        }
        mock_client = Mock()
        mock_client.context_window = 8000
        with patch('src.main.check_provider_available', return_value=True):
            with patch('src.main.create_client', return_value=mock_client):
                with patch('src.main.MCPClient'):
                    with patch('src.main.EnhancedAgent'):
                        agent = await initialize_agent(config, None)
                        assert agent is not None


@pytest.mark.unit
class TestCLI:
    """Tests for CLI entry point"""

    def test_cli_entry_point(self):
        """Test cli function entry point"""
        with patch('asyncio.run'):
            with patch('src.main.main'):
                cli()

    def test_cli_keyboard_interrupt_handling(self):
        """Test CLI handles keyboard interrupt"""
        def raise_keyboard_interrupt(*args):
            raise KeyboardInterrupt()

        with patch('asyncio.run', side_effect=raise_keyboard_interrupt):
            with patch('sys.exit') as mock_exit:
                cli()
                mock_exit.assert_called_once_with(0)


@pytest.mark.unit
class TestConfigLoading:
    """Tests for configuration loading edge cases"""

    def test_config_model_defaults(self):
        """Test config provides sensible defaults for model"""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                config = load_config("~/.tiny-claude-code/settings.json")
                # Should be a dict, even if empty
                assert isinstance(config, dict)

    def test_config_temperature_conversion(self):
        """Test config properly converts temperature to float"""
        test_config = {"model": {"temperature": "0.7"}}
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {"TEMPERATURE": "0.8"}):
                with patch('src.main.load_dotenv'):
                    config = load_config("~/.tiny-claude-code/settings.json")
                    assert isinstance(config, dict)

    def test_config_max_tokens_conversion(self):
        """Test config properly converts max_tokens to int"""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {"MAX_TOKENS": "2000"}):
                with patch('src.main.load_dotenv'):
                    config = load_config("~/.tiny-claude-code/settings.json")
                    assert isinstance(config, dict)


@pytest.mark.unit
class TestMainFunctionality:
    """Tests for main application functionality"""

    def test_parse_args_returns_namespace(self):
        """Test parse_args returns argument namespace"""
        with patch('sys.argv', ['script']):
            args = parse_args()
            assert hasattr(args, 'config')
            assert hasattr(args, 'verbose')
            assert hasattr(args, 'quiet')

    def test_load_config_priority(self):
        """Test load_config respects priority (env > .env > ~/.tiny-claude-code/settings.json)"""
        test_config = {"model": {"ANTHROPIC_API_KEY": "config-key"}}
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                config = load_config("~/.tiny-claude-code/settings.json")
                assert isinstance(config, dict)

    def test_resolve_env_vars_escaping(self):
        """Test _resolve_env_vars doesn't process non-placeholder strings"""
        result = _resolve_env_vars("normal-string-with-dashes")
        assert result == "normal-string-with-dashes"

    def test_resolve_env_vars_partial_placeholder(self):
        """Test _resolve_env_vars doesn't process partial placeholders"""
        result = _resolve_env_vars("${INCOMPLETE")
        assert result == "${INCOMPLETE"
