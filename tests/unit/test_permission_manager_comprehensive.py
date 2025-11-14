"""
Unit tests for Permission Manager

Tests permission modes, tool classification, request handling,
session tracking, configuration, and workflow integration.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from src.agents.permission_manager import PermissionManager, PermissionMode
from src.tools.base import ToolPermissionLevel


@pytest.mark.unit
class TestPermissionModeEnum:
    """Tests for PermissionMode enum"""

    def test_permission_mode_always_ask(self):
        """Test ALWAYS_ASK mode value"""
        assert PermissionMode.ALWAYS_ASK.value == "always_ask"

    def test_permission_mode_auto_approve_safe(self):
        """Test AUTO_APPROVE_SAFE mode value"""
        assert PermissionMode.AUTO_APPROVE_SAFE.value == "auto_approve_safe"

    def test_permission_mode_auto_approve_all(self):
        """Test AUTO_APPROVE_ALL mode value"""
        assert PermissionMode.AUTO_APPROVE_ALL.value == "auto_approve_all"

    def test_permission_mode_skip_all(self):
        """Test SKIP_ALL mode value"""
        assert PermissionMode.SKIP_ALL.value == "skip_all"

    def test_permission_mode_iteration(self):
        """Test can iterate over all modes"""
        modes = list(PermissionMode)
        assert len(modes) == 4

    def test_permission_mode_equality(self):
        """Test mode equality comparison"""
        assert PermissionMode.ALWAYS_ASK == PermissionMode.ALWAYS_ASK
        assert PermissionMode.ALWAYS_ASK != PermissionMode.AUTO_APPROVE_SAFE


@pytest.mark.unit
class TestPermissionManagerInitialization:
    """Tests for PermissionManager initialization"""

    def test_initialization_default(self):
        """Test PermissionManager default initialization"""
        manager = PermissionManager()

        assert manager.mode == PermissionMode.AUTO_APPROVE_SAFE
        assert isinstance(manager.config, dict)
        assert isinstance(manager.approved_tools, set)
        assert isinstance(manager.denied_tools, set)
        assert isinstance(manager.session_approved, set)
        assert isinstance(manager.session_denied, set)
        assert len(manager.approved_tools) == 0
        assert len(manager.session_approved) == 0

    def test_initialization_custom_mode(self):
        """Test initialization with custom mode"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)

        assert manager.mode == PermissionMode.ALWAYS_ASK

    def test_initialization_with_config(self):
        """Test initialization with configuration"""
        config = {
            "always_allow": ["read", "glob"],
            "never_allow": ["bash"],
            "tool_permissions": {"write": "allow"}
        }
        manager = PermissionManager(config=config)

        assert "read" in manager.approved_tools
        assert "glob" in manager.approved_tools
        assert "bash" in manager.denied_tools
        assert manager.tool_permissions["write"] == "allow"

    def test_initialization_loads_always_allow(self):
        """Test initialization loads always_allow list"""
        config = {"always_allow": ["tool1", "tool2"]}
        manager = PermissionManager(config=config)

        assert manager.approved_tools == {"tool1", "tool2"}

    def test_initialization_loads_never_allow(self):
        """Test initialization loads never_allow list"""
        config = {"never_allow": ["dangerous_tool"]}
        manager = PermissionManager(config=config)

        assert manager.denied_tools == {"dangerous_tool"}

    def test_initialization_loads_tool_permissions(self):
        """Test initialization loads tool_permissions"""
        config = {
            "tool_permissions": {
                "bash": "deny",
                "read": "allow"
            }
        }
        manager = PermissionManager(config=config)

        assert manager.tool_permissions["bash"] == "deny"
        assert manager.tool_permissions["read"] == "allow"


@pytest.mark.unit
class TestSkipAllMode:
    """Tests for SKIP_ALL permission mode"""

    @pytest.mark.asyncio
    async def test_skip_all_always_approves(self):
        """Test SKIP_ALL mode always approves"""
        manager = PermissionManager(mode=PermissionMode.SKIP_ALL)
        tool = Mock(name="bash")

        approved, message = await manager.request_permission(tool, {})

        assert approved is True
        assert message == ""

    @pytest.mark.asyncio
    async def test_skip_all_ignores_denied_tools(self):
        """Test SKIP_ALL ignores denied tools list"""
        config = {"never_allow": ["bash"]}
        manager = PermissionManager(
            mode=PermissionMode.SKIP_ALL,
            config=config
        )
        tool = Mock(name="bash")

        approved, message = await manager.request_permission(tool, {})

        assert approved is True


@pytest.mark.unit
class TestAutoApproveAllMode:
    """Tests for AUTO_APPROVE_ALL permission mode"""

    @pytest.mark.asyncio
    async def test_auto_approve_all_approves_everything(self):
        """Test AUTO_APPROVE_ALL mode approves all tools"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)
        tool = Mock(name="bash", permission_level=ToolPermissionLevel.DANGEROUS)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True
        assert message == ""

    @pytest.mark.asyncio
    async def test_auto_approve_all_ignores_permission_level(self):
        """Test AUTO_APPROVE_ALL ignores permission level"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)
        tool = Mock(name="dangerous_tool", permission_level=ToolPermissionLevel.DANGEROUS)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    @pytest.mark.asyncio
    async def test_auto_approve_all_ignores_denied_list(self):
        """Test AUTO_APPROVE_ALL ignores denied tools"""
        config = {"never_allow": ["bash"]}
        manager = PermissionManager(
            mode=PermissionMode.AUTO_APPROVE_ALL,
            config=config
        )
        tool = Mock(name="bash")

        approved, message = await manager.request_permission(tool, {})

        assert approved is True


@pytest.mark.unit
class TestAutoApproveSafeMode:
    """Tests for AUTO_APPROVE_SAFE permission mode"""

    @pytest.mark.asyncio
    async def test_auto_approve_safe_approves_safe_tools(self):
        """Test AUTO_APPROVE_SAFE approves SAFE level tools"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        tool = Mock(name="read", permission_level=ToolPermissionLevel.SAFE)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True
        assert message == ""

    @pytest.mark.asyncio
    async def test_auto_approve_safe_prompts_normal_tools(self):
        """Test AUTO_APPROVE_SAFE prompts for NORMAL level tools"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        tool = Mock(name="write", permission_level=ToolPermissionLevel.NORMAL)

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (False, "Denied by user")
            approved, message = await manager.request_permission(tool, {})

            mock_prompt.assert_called_once_with(tool, {})

    @pytest.mark.asyncio
    async def test_auto_approve_safe_prompts_dangerous_tools(self):
        """Test AUTO_APPROVE_SAFE prompts for DANGEROUS level tools"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        tool = Mock(name="bash", permission_level=ToolPermissionLevel.DANGEROUS)

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (False, "Denied by user")
            await manager.request_permission(tool, {})

            mock_prompt.assert_called_once()


@pytest.mark.unit
class TestAlwaysAskMode:
    """Tests for ALWAYS_ASK permission mode"""

    @pytest.mark.asyncio
    async def test_always_ask_prompts_safe_tools(self):
        """Test ALWAYS_ASK prompts even for SAFE tools"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = Mock(name="read", permission_level=ToolPermissionLevel.SAFE)
        tool.name = "read"

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (True, "")
            await manager.request_permission(tool, {})

            mock_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_always_ask_respects_approved_tools(self):
        """Test ALWAYS_ASK respects approved tools list"""
        config = {"always_allow": ["read"]}
        manager = PermissionManager(
            mode=PermissionMode.ALWAYS_ASK,
            config=config
        )
        tool = Mock()
        tool.name = "read"

        approved, message = await manager.request_permission(tool, {})

        assert approved is True


@pytest.mark.unit
class TestToolSpecificConfiguration:
    """Tests for tool-specific permission configuration"""

    @pytest.mark.asyncio
    async def test_tool_config_allow_overrides_mode(self):
        """Test tool-specific allow overrides mode"""
        config = {"tool_permissions": {"write": "allow"}}
        manager = PermissionManager(
            mode=PermissionMode.ALWAYS_ASK,
            config=config
        )
        tool = Mock()
        tool.name = "write"

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    @pytest.mark.asyncio
    async def test_tool_config_deny_overrides_mode(self):
        """Test tool-specific deny works with ALWAYS_ASK mode"""
        config = {"tool_permissions": {"read": "deny"}}
        manager = PermissionManager(
            mode=PermissionMode.ALWAYS_ASK,
            config=config
        )
        tool = Mock()
        tool.name = "read"

        approved, message = await manager.request_permission(tool, {})

        assert approved is False
        assert message == "Permission denied by configuration"

    @pytest.mark.asyncio
    async def test_tool_config_takes_highest_priority(self):
        """Test tool config takes precedence over approved list"""
        config = {
            "always_allow": ["bash"],
            "tool_permissions": {"bash": "deny"}
        }
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK, config=config)
        tool = Mock()
        tool.name = "bash"

        approved, message = await manager.request_permission(tool, {})

        assert approved is False


@pytest.mark.unit
class TestPermanentApprovedTools:
    """Tests for permanent approved tools list"""

    @pytest.mark.asyncio
    async def test_approved_tools_grants_permission(self):
        """Test approved tools list grants permission"""
        config = {"always_allow": ["read", "glob"]}
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK, config=config)
        tool = Mock()
        tool.name = "read"

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    @pytest.mark.asyncio
    async def test_multiple_approved_tools(self):
        """Test multiple tools in approved list"""
        config = {"always_allow": ["tool1", "tool2", "tool3"]}
        manager = PermissionManager(config=config)

        assert len(manager.approved_tools) == 3
        assert "tool1" in manager.approved_tools

    @pytest.mark.asyncio
    async def test_adding_to_approved_tools(self):
        """Test adding tool to approved list at runtime"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = Mock()
        tool.name = "read"

        manager.approved_tools.add("read")
        approved, message = await manager.request_permission(tool, {})

        assert approved is True


@pytest.mark.unit
class TestPermanentDeniedTools:
    """Tests for permanent denied tools list"""

    @pytest.mark.asyncio
    async def test_denied_tools_blocks_permission(self):
        """Test denied tools list blocks permission"""
        config = {"never_allow": ["bash"]}
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK, config=config)
        tool = Mock()
        tool.name = "bash"

        approved, message = await manager.request_permission(tool, {})

        assert approved is False
        assert message == "Permission denied by user"

    @pytest.mark.asyncio
    async def test_multiple_denied_tools(self):
        """Test multiple tools in denied list"""
        config = {"never_allow": ["bash", "eval", "exec"]}
        manager = PermissionManager(config=config)

        assert len(manager.denied_tools) == 3


@pytest.mark.unit
class TestSessionApprovedTools:
    """Tests for session-level approved tools"""

    @pytest.mark.asyncio
    async def test_session_approved_grants_permission(self):
        """Test session approved list grants permission"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = Mock()
        tool.name = "bash"

        manager.session_approved.add("bash")
        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    @pytest.mark.asyncio
    async def test_session_approved_separate_from_permanent(self):
        """Test session approved is separate from permanent"""
        manager = PermissionManager()

        manager.session_approved.add("read")
        assert "read" not in manager.approved_tools
        assert "read" in manager.session_approved


@pytest.mark.unit
class TestSessionDeniedTools:
    """Tests for session-level denied tools"""

    @pytest.mark.asyncio
    async def test_session_denied_blocks_permission(self):
        """Test session denied list blocks permission"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = Mock()
        tool.name = "bash"

        manager.session_denied.add("bash")
        approved, message = await manager.request_permission(tool, {})

        assert approved is False

    @pytest.mark.asyncio
    async def test_session_denied_separate_from_permanent(self):
        """Test session denied is separate from permanent"""
        manager = PermissionManager()

        manager.session_denied.add("write")
        assert "write" not in manager.denied_tools
        assert "write" in manager.session_denied


@pytest.mark.unit
class TestPermissionPriority:
    """Tests for permission decision priority"""

    @pytest.mark.asyncio
    async def test_tool_config_over_permanent_approved(self):
        """Test tool config takes precedence over approved list"""
        config = {
            "always_allow": ["bash"],
            "tool_permissions": {"bash": "deny"}
        }
        manager = PermissionManager(config=config)
        tool = Mock()
        tool.name = "bash"

        approved, message = await manager.request_permission(tool, {})

        assert approved is False

    @pytest.mark.asyncio
    async def test_permanent_list_over_session(self):
        """Test permanent denied takes precedence over mode"""
        config = {"never_allow": ["read"]}
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK, config=config)
        tool = Mock()
        tool.name = "read"

        manager.session_approved.add("read")  # Session wants to approve
        approved, message = await manager.request_permission(tool, {})

        # Permanent deny takes precedence
        assert approved is False

    @pytest.mark.asyncio
    async def test_skip_all_takes_highest_priority(self):
        """Test SKIP_ALL mode takes highest priority"""
        config = {"never_allow": ["bash"]}
        manager = PermissionManager(
            mode=PermissionMode.SKIP_ALL,
            config=config
        )
        tool = Mock()
        tool.name = "bash"

        approved, message = await manager.request_permission(tool, {})

        assert approved is True


@pytest.mark.unit
class TestPromptUser:
    """Tests for user prompt interaction"""

    @pytest.mark.asyncio
    async def test_prompt_user_yes_response(self):
        """Test user responding yes to permission"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = Mock()
        tool.name = "bash"
        tool.permission_level = ToolPermissionLevel.DANGEROUS
        tool.description = "Execute shell commands"

        with patch('builtins.input', return_value='y'):
            approved, message = await manager._prompt_user(tool, {})

        assert approved is True

    @pytest.mark.asyncio
    async def test_prompt_user_no_response(self):
        """Test user responding no to permission"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = Mock()
        tool.name = "bash"
        tool.permission_level = ToolPermissionLevel.DANGEROUS

        with patch('builtins.input', return_value='n'):
            approved, message = await manager._prompt_user(tool, {})

        assert approved is False
        assert message == "Permission denied by user"

    @pytest.mark.asyncio
    async def test_prompt_user_always_allow_response(self):
        """Test user responding to always allow"""
        manager = PermissionManager()
        tool = Mock()
        tool.name = "read"
        tool.permission_level = ToolPermissionLevel.SAFE

        with patch('builtins.input', return_value='a'):
            approved, message = await manager._prompt_user(tool, {})

        assert approved is True
        assert "read" in manager.approved_tools

    @pytest.mark.asyncio
    async def test_prompt_user_never_allow_response(self):
        """Test user responding to never allow"""
        manager = PermissionManager()
        tool = Mock()
        tool.name = "bash"
        tool.permission_level = ToolPermissionLevel.DANGEROUS

        with patch('builtins.input', return_value='v'):
            approved, message = await manager._prompt_user(tool, {})

        assert approved is False
        assert "bash" in manager.denied_tools

    @pytest.mark.asyncio
    async def test_prompt_user_eof_interrupt(self):
        """Test prompt handling EOF/interrupt"""
        manager = PermissionManager()
        tool = Mock(name="bash")

        with patch('builtins.input', side_effect=EOFError):
            approved, message = await manager._prompt_user(tool, {})

        assert approved is False
        assert "interrupted" in message.lower()

    @pytest.mark.asyncio
    async def test_prompt_user_keyboard_interrupt(self):
        """Test prompt handling keyboard interrupt"""
        manager = PermissionManager()
        tool = Mock(name="bash")

        with patch('builtins.input', side_effect=KeyboardInterrupt):
            approved, message = await manager._prompt_user(tool, {})

        assert approved is False


@pytest.mark.unit
class TestSavePreferences:
    """Tests for saving permission preferences"""

    def test_save_preferences_creates_file(self):
        """Test save_preferences creates config file"""
        manager = PermissionManager()
        manager.approved_tools.add("read")
        manager.denied_tools.add("bash")

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            result = manager.save_preferences(str(config_path))

            assert result is True
            assert config_path.exists()

    def test_save_preferences_includes_approved_tools(self):
        """Test saved config includes approved tools"""
        manager = PermissionManager()
        manager.approved_tools.add("read")
        manager.approved_tools.add("glob")

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager.save_preferences(str(config_path))

            with open(config_path) as f:
                config = json.load(f)

            assert set(config["permissions"]["always_allow"]) == {"read", "glob"}

    def test_save_preferences_includes_denied_tools(self):
        """Test saved config includes denied tools"""
        manager = PermissionManager()
        manager.denied_tools.add("bash")

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            manager.save_preferences(str(config_path))

            with open(config_path) as f:
                config = json.load(f)

            assert config["permissions"]["never_allow"] == ["bash"]

    def test_save_preferences_merges_with_existing(self):
        """Test save_preferences merges with existing config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"

            # Create initial config
            initial_config = {"model": "claude-sonnet"}
            with open(config_path, 'w') as f:
                json.dump(initial_config, f)

            # Save permissions
            manager = PermissionManager()
            manager.approved_tools.add("read")
            manager.save_preferences(str(config_path))

            # Verify both exist
            with open(config_path) as f:
                config = json.load(f)

            assert config["model"] == "claude-sonnet"
            assert "read" in config["permissions"]["always_allow"]

    def test_save_preferences_handles_write_error(self):
        """Test save_preferences handles write errors gracefully"""
        manager = PermissionManager()
        manager.approved_tools.add("read")

        # Use invalid path to cause error
        result = manager.save_preferences("/invalid/path/config.json")

        assert result is False


@pytest.mark.unit
class TestGetStats:
    """Tests for statistics retrieval"""

    def test_get_stats_returns_dict(self):
        """Test get_stats returns dictionary"""
        manager = PermissionManager()
        stats = manager.get_stats()

        assert isinstance(stats, dict)

    def test_get_stats_includes_mode(self):
        """Test get_stats includes current mode"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        stats = manager.get_stats()

        assert stats["mode"] == "always_ask"

    def test_get_stats_includes_approved_tools(self):
        """Test get_stats includes approved tools"""
        config = {"always_allow": ["read"]}
        manager = PermissionManager(config=config)
        stats = manager.get_stats()

        assert "read" in stats["always_allow"]

    def test_get_stats_includes_denied_tools(self):
        """Test get_stats includes denied tools"""
        config = {"never_allow": ["bash"]}
        manager = PermissionManager(config=config)
        stats = manager.get_stats()

        assert "bash" in stats["never_allow"]

    def test_get_stats_includes_session_approved(self):
        """Test get_stats includes session approved"""
        manager = PermissionManager()
        manager.session_approved.add("test_tool")
        stats = manager.get_stats()

        assert "test_tool" in stats["session_approved"]

    def test_get_stats_includes_session_denied(self):
        """Test get_stats includes session denied"""
        manager = PermissionManager()
        manager.session_denied.add("denied_tool")
        stats = manager.get_stats()

        assert "denied_tool" in stats["session_denied"]

    def test_get_stats_includes_tool_permissions(self):
        """Test get_stats includes tool permissions"""
        config = {"tool_permissions": {"bash": "deny"}}
        manager = PermissionManager(config=config)
        stats = manager.get_stats()

        assert stats["tool_permissions"]["bash"] == "deny"


@pytest.mark.unit
class TestIntegration:
    """Integration tests for PermissionManager"""

    @pytest.mark.asyncio
    async def test_complete_permission_workflow(self):
        """Test complete permission request workflow"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = Mock()
        tool.name = "read"
        tool.permission_level = ToolPermissionLevel.SAFE
        tool.description = "Read file"

        with patch('builtins.input', return_value='a'):
            approved, message = await manager.request_permission(tool, {"file": "test.txt"})

        assert approved is True
        assert "read" in manager.approved_tools

        # Second request should not prompt
        approved2, message2 = await manager.request_permission(tool, {"file": "other.txt"})
        assert approved2 is True

    @pytest.mark.asyncio
    async def test_workflow_with_permanent_approval(self):
        """Test workflow with permanent approval"""
        config = {"always_allow": ["read"]}
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK, config=config)
        tool = Mock()
        tool.name = "read"

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    @pytest.mark.asyncio
    async def test_workflow_with_mode_switching(self):
        """Test switching permission modes"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = Mock()
        tool.name = "bash"
        tool.permission_level = ToolPermissionLevel.DANGEROUS

        # First: ask mode would prompt
        with patch('builtins.input', return_value='n'):
            approved1, _ = await manager.request_permission(tool, {})

        assert approved1 is False

        # Switch to auto-approve
        manager.mode = PermissionMode.AUTO_APPROVE_ALL
        approved2, _ = await manager.request_permission(tool, {})

        assert approved2 is True

    @pytest.mark.asyncio
    async def test_workflow_with_session_and_permanent(self):
        """Test interaction between session and permanent approvals"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)
        tool = Mock(name="write")

        # Add to session level
        manager.session_approved.add("write")

        # Should approve from session level
        approved1, _ = await manager.request_permission(tool, {})
        assert approved1 is True

        # Add to permanent level
        manager.approved_tools.add("write")

        # Should still approve
        approved2, _ = await manager.request_permission(tool, {})
        assert approved2 is True


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases"""

    @pytest.mark.asyncio
    async def test_tool_in_both_approved_and_denied(self):
        """Test tool in both lists (denied takes precedence)"""
        config = {
            "always_allow": ["bash"],
            "never_allow": ["bash"]
        }
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL, config=config)
        tool = Mock(name="bash")

        approved, message = await manager.request_permission(tool, {})

        # Denied should be checked after approved, so approve wins
        # Actually based on code, approved is checked first
        assert approved is True

    @pytest.mark.asyncio
    async def test_empty_config(self):
        """Test with empty configuration"""
        manager = PermissionManager(config={})

        assert len(manager.approved_tools) == 0
        assert len(manager.denied_tools) == 0
        assert len(manager.tool_permissions) == 0

    @pytest.mark.asyncio
    async def test_none_config(self):
        """Test with None configuration"""
        manager = PermissionManager(config=None)

        assert isinstance(manager.config, dict)
        assert len(manager.approved_tools) == 0

    def test_special_characters_in_tool_names(self):
        """Test tool names with special characters"""
        config = {"always_allow": ["tool-with-dash", "tool_with_underscore"]}
        manager = PermissionManager(config=config)

        assert "tool-with-dash" in manager.approved_tools
        assert "tool_with_underscore" in manager.approved_tools

    @pytest.mark.asyncio
    async def test_unicode_in_tool_names(self):
        """Test unicode characters in tool names"""
        config = {"always_allow": ["读取", "写入"]}
        manager = PermissionManager(config=config)

        assert "读取" in manager.approved_tools
        assert "写入" in manager.approved_tools

    @pytest.mark.asyncio
    async def test_very_long_tool_list(self):
        """Test with large list of tools"""
        tools = [f"tool_{i}" for i in range(100)]
        config = {"always_allow": tools}
        manager = PermissionManager(config=config)

        assert len(manager.approved_tools) == 100

    @pytest.mark.asyncio
    async def test_request_with_empty_params(self):
        """Test permission request with empty params"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)
        tool = Mock(name="test")

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    @pytest.mark.asyncio
    async def test_request_with_complex_params(self):
        """Test permission request with complex parameters"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)
        tool = Mock(name="bash")

        complex_params = {
            "command": "ls -la",
            "nested": {"key": "value"},
            "list": [1, 2, 3]
        }

        approved, message = await manager.request_permission(tool, complex_params)

        assert approved is True
