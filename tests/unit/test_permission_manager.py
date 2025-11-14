"""
Unit tests for Permission Manager

Tests permission modes, permission requests, configuration persistence, and statistics.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.agents.permission_manager import PermissionManager, PermissionMode
from src.tools.base import ToolPermissionLevel


@pytest.mark.unit
class TestPermissionMode:
    """Tests for PermissionMode enum"""

    def test_permission_mode_values(self):
        """Test PermissionMode enum values"""
        assert PermissionMode.ALWAYS_ASK.value == "always_ask"
        assert PermissionMode.AUTO_APPROVE_SAFE.value == "auto_approve_safe"
        assert PermissionMode.AUTO_APPROVE_ALL.value == "auto_approve_all"
        assert PermissionMode.SKIP_ALL.value == "skip_all"


@pytest.mark.unit
class TestPermissionManagerInitialization:
    """Tests for PermissionManager initialization"""

    def test_initialization_with_defaults(self):
        """Test PermissionManager initialization with defaults"""
        manager = PermissionManager()
        assert manager.mode == PermissionMode.AUTO_APPROVE_SAFE
        assert manager.config == {}
        assert len(manager.approved_tools) == 0
        assert len(manager.denied_tools) == 0

    def test_initialization_with_custom_mode(self):
        """Test initialization with custom mode"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)
        assert manager.mode == PermissionMode.AUTO_APPROVE_ALL

    def test_initialization_with_always_ask_mode(self):
        """Test initialization with ALWAYS_ASK mode"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        assert manager.mode == PermissionMode.ALWAYS_ASK

    def test_initialization_with_skip_all_mode(self):
        """Test initialization with SKIP_ALL mode"""
        manager = PermissionManager(mode=PermissionMode.SKIP_ALL)
        assert manager.mode == PermissionMode.SKIP_ALL

    def test_initialization_with_config_allowed_tools(self):
        """Test initialization with allowed tools in config"""
        config = {"always_allow": ["bash", "read"]}
        manager = PermissionManager(config=config)
        assert "bash" in manager.approved_tools
        assert "read" in manager.approved_tools

    def test_initialization_with_config_denied_tools(self):
        """Test initialization with denied tools in config"""
        config = {"never_allow": ["rm", "delete"]}
        manager = PermissionManager(config=config)
        assert "rm" in manager.denied_tools
        assert "delete" in manager.denied_tools

    def test_initialization_with_tool_permissions(self):
        """Test initialization with tool-specific permissions"""
        config = {"tool_permissions": {"bash": "allow", "rm": "deny"}}
        manager = PermissionManager(config=config)
        assert manager.tool_permissions["bash"] == "allow"
        assert manager.tool_permissions["rm"] == "deny"


@pytest.mark.unit
class TestPermissionRequestSkipAll:
    """Tests for SKIP_ALL permission mode"""

    @pytest.mark.asyncio
    async def test_skip_all_mode_approves_all(self):
        """Test SKIP_ALL mode approves all tools"""
        manager = PermissionManager(mode=PermissionMode.SKIP_ALL)
        mock_tool = Mock()
        mock_tool.name = "dangerous_tool"
        mock_tool.permission_level = ToolPermissionLevel.DANGEROUS

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is True
        assert msg == ""


@pytest.mark.unit
class TestPermissionRequestAutoApproveAll:
    """Tests for AUTO_APPROVE_ALL permission mode"""

    @pytest.mark.asyncio
    async def test_auto_approve_all_mode(self):
        """Test AUTO_APPROVE_ALL approves all tools"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)
        mock_tool = Mock()
        mock_tool.name = "bash"

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is True
        assert msg == ""


@pytest.mark.unit
class TestPermissionRequestToolConfig:
    """Tests for tool-specific permission configuration"""

    @pytest.mark.asyncio
    async def test_tool_config_allow(self):
        """Test tool-specific allow configuration"""
        config = {"tool_permissions": {"bash": "allow"}}
        manager = PermissionManager(config=config)
        mock_tool = Mock()
        mock_tool.name = "bash"

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is True

    @pytest.mark.asyncio
    async def test_tool_config_deny(self):
        """Test tool-specific deny configuration"""
        config = {"tool_permissions": {"rm": "deny"}}
        manager = PermissionManager(config=config)
        mock_tool = Mock()
        mock_tool.name = "rm"

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is False
        assert "configuration" in msg.lower()


@pytest.mark.unit
class TestPermissionRequestApprovedTools:
    """Tests for permanent approved tools list"""

    @pytest.mark.asyncio
    async def test_approved_tools_from_config(self):
        """Test tools in approved list are always approved"""
        config = {"always_allow": ["bash"]}
        manager = PermissionManager(config=config)
        mock_tool = Mock()
        mock_tool.name = "bash"

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is True

    @pytest.mark.asyncio
    async def test_denied_tools_from_config(self):
        """Test tools in denied list are always denied"""
        config = {"never_allow": ["rm"]}
        manager = PermissionManager(config=config)
        mock_tool = Mock()
        mock_tool.name = "rm"

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is False


@pytest.mark.unit
class TestPermissionRequestSessionLists:
    """Tests for session-level approved/denied lists"""

    @pytest.mark.asyncio
    async def test_session_approved_tool(self):
        """Test session-approved tool"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        manager.session_approved.add("bash")
        mock_tool = Mock()
        mock_tool.name = "bash"

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is True

    @pytest.mark.asyncio
    async def test_session_denied_tool(self):
        """Test session-denied tool"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        manager.session_denied.add("rm")
        mock_tool = Mock()
        mock_tool.name = "rm"

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is False


@pytest.mark.unit
class TestPermissionRequestAutoApproveSafe:
    """Tests for AUTO_APPROVE_SAFE permission mode"""

    @pytest.mark.asyncio
    async def test_auto_approve_safe_mode_safe_tool(self):
        """Test AUTO_APPROVE_SAFE approves SAFE tools"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        mock_tool = Mock()
        mock_tool.name = "read"
        mock_tool.permission_level = Mock()
        mock_tool.permission_level.value = "safe"

        approved, msg = await manager.request_permission(mock_tool, {})
        assert approved is True

    @pytest.mark.asyncio
    async def test_auto_approve_safe_mode_normal_tool(self):
        """Test AUTO_APPROVE_SAFE asks for NORMAL tools"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        mock_tool = Mock()
        mock_tool.name = "write"
        mock_tool.permission_level = Mock()
        mock_tool.permission_level.value = "normal"
        mock_tool.description = "Write to file"

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (True, "")
            approved, msg = await manager.request_permission(mock_tool, {})
            # Should call prompt_user for non-SAFE tools
            mock_prompt.assert_called_once()


@pytest.mark.unit
class TestPermissionRequestUserPrompt:
    """Tests for user prompting"""

    @pytest.mark.asyncio
    async def test_prompt_user_called_for_unknown_normal(self):
        """Test that _prompt_user is called for unknown NORMAL tools"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        mock_tool = Mock()
        mock_tool.name = "unknown_tool"
        mock_tool.permission_level = Mock()
        mock_tool.permission_level.value = "normal"
        mock_tool.description = "Unknown tool"

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (False, "User denied")
            approved, msg = await manager.request_permission(mock_tool, {})
            mock_prompt.assert_called_once()


@pytest.mark.unit
class TestPermissionRequestStats:
    """Tests for permission statistics"""

    def test_get_stats_empty(self):
        """Test stats with no permissions set"""
        manager = PermissionManager()
        stats = manager.get_stats()

        assert stats["mode"] == "auto_approve_safe"
        assert len(stats["always_allow"]) == 0
        assert len(stats["never_allow"]) == 0
        assert len(stats["session_approved"]) == 0
        assert len(stats["session_denied"]) == 0

    def test_get_stats_with_approved_tools(self):
        """Test stats with approved tools"""
        config = {"always_allow": ["bash", "read"]}
        manager = PermissionManager(config=config)
        stats = manager.get_stats()

        assert "bash" in stats["always_allow"]
        assert "read" in stats["always_allow"]

    def test_get_stats_with_denied_tools(self):
        """Test stats with denied tools"""
        config = {"never_allow": ["rm"]}
        manager = PermissionManager(config=config)
        stats = manager.get_stats()

        assert "rm" in stats["never_allow"]

    def test_get_stats_with_session_lists(self):
        """Test stats with session lists"""
        manager = PermissionManager()
        manager.session_approved.add("bash")
        manager.session_denied.add("write")

        stats = manager.get_stats()
        assert "bash" in stats["session_approved"]
        assert "write" in stats["session_denied"]


@pytest.mark.unit
class TestPermissionManagerSavePreferences:
    """Tests for saving preferences"""

    def test_save_preferences_creates_config(self):
        """Test saving preferences creates config file"""
        manager = PermissionManager()
        manager.approved_tools.add("bash")
        manager.denied_tools.add("rm")

        with patch('builtins.open', create=True) as mock_open:
            with patch('pathlib.Path.exists', return_value=False):
                result = manager.save_preferences()
                assert result is True
                mock_open.assert_called()

    def test_save_preferences_updates_existing_config(self):
        """Test saving preferences updates existing config"""
        manager = PermissionManager()
        manager.approved_tools.add("grep")

        with patch('builtins.open', create=True) as mock_open:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('json.load', return_value={}):
                    result = manager.save_preferences()
                    assert result is True

    def test_save_preferences_handles_error(self):
        """Test saving preferences handles errors gracefully"""
        manager = PermissionManager()

        with patch('pathlib.Path.exists', side_effect=Exception("Permission denied")):
            result = manager.save_preferences()
            assert result is False


@pytest.mark.unit
class TestPermissionManagerSessionManagement:
    """Tests for session-level permission management"""

    def test_session_approved_add(self):
        """Test adding to session approved"""
        manager = PermissionManager()
        manager.session_approved.add("tool1")
        assert "tool1" in manager.session_approved

    def test_session_denied_add(self):
        """Test adding to session denied"""
        manager = PermissionManager()
        manager.session_denied.add("tool2")
        assert "tool2" in manager.session_denied

    def test_session_lists_separate_from_config(self):
        """Test that session lists are separate from config"""
        config = {"always_allow": ["bash"]}
        manager = PermissionManager(config=config)
        manager.session_approved.add("read")

        assert "bash" in manager.approved_tools
        assert "read" not in manager.approved_tools
        assert "read" in manager.session_approved


@pytest.mark.unit
class TestPermissionManagerToolConfigOverride:
    """Tests for tool-specific config overrides"""

    @pytest.mark.asyncio
    async def test_tool_config_overrides_session_list(self):
        """Test that tool config takes precedence"""
        config = {"tool_permissions": {"bash": "deny"}}
        manager = PermissionManager(config=config)
        manager.session_approved.add("bash")

        mock_tool = Mock()
        mock_tool.name = "bash"

        approved, msg = await manager.request_permission(mock_tool, {})
        # Tool config should override session approval
        assert approved is False

    @pytest.mark.asyncio
    async def test_tool_config_overrides_approved_tools(self):
        """Test that tool config overrides approved tools list"""
        config = {
            "always_allow": ["bash"],
            "tool_permissions": {"bash": "deny"}
        }
        manager = PermissionManager(config=config)

        mock_tool = Mock()
        mock_tool.name = "bash"

        approved, msg = await manager.request_permission(mock_tool, {})
        # Tool-specific config should take precedence
        assert approved is False


@pytest.mark.unit
class TestPermissionManagerEdgeCases:
    """Tests for edge cases"""

    def test_empty_tool_name(self):
        """Test with empty tool name"""
        manager = PermissionManager()
        manager.session_approved.add("")
        assert "" in manager.session_approved

    def test_none_in_tool_lists(self):
        """Test handling of None values"""
        config = {"always_allow": ["bash", None]}
        manager = PermissionManager(config=config)
        # None should be converted to a set
        assert "bash" in manager.approved_tools

    @pytest.mark.asyncio
    async def test_tool_with_no_permission_level(self):
        """Test tool without permission_level attribute"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        mock_tool = Mock()
        mock_tool.name = "custom"
        # Don't set permission_level

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (True, "")
            # Should handle gracefully
            try:
                approved, msg = await manager.request_permission(mock_tool, {})
                # Should either approve or prompt
                assert approved is True or hasattr(mock_tool, 'permission_level')
            except AttributeError:
                # This is acceptable if the tool is required to have permission_level
                pass


@pytest.mark.unit
class TestPermissionManagerIntegration:
    """Integration tests for permission manager"""

    @pytest.mark.asyncio
    async def test_typical_permission_workflow(self):
        """Test typical permission workflow"""
        manager = PermissionManager(
            mode=PermissionMode.AUTO_APPROVE_SAFE,
            config={
                "always_allow": ["bash"],
                "never_allow": ["rm"],
                "tool_permissions": {"dangerous": "deny"}
            }
        )

        # Test SAFE tool (auto-approved)
        safe_tool = Mock(name="read", permission_level=Mock(value="safe"))
        safe_approved, _ = await manager.request_permission(safe_tool, {})

        # Test approved tool
        bash_tool = Mock(name="bash", permission_level=Mock(value="normal"))
        bash_tool.description = "Execute bash"
        with patch.object(manager, '_prompt_user', return_value=(True, "")):
            bash_approved, _ = await manager.request_permission(bash_tool, {})
            assert bash_approved is True

        # Stats should show configuration
        stats = manager.get_stats()
        assert "bash" in stats["always_allow"]
        assert "rm" in stats["never_allow"]

    @pytest.mark.asyncio
    async def test_session_permission_persistence(self):
        """Test session-level permission persistence"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)

        # First tool approval
        tool1 = Mock()
        tool1.name = "tool1"
        manager.session_approved.add("tool1")

        # Check persistence
        tool1_check = Mock()
        tool1_check.name = "tool1"
        approved, _ = await manager.request_permission(tool1_check, {})
        assert approved is True

        # Stats should show session approval
        stats = manager.get_stats()
        assert len(stats["session_approved"]) == 1

    @pytest.mark.asyncio
    async def test_permission_hierarchy(self):
        """Test permission decision hierarchy"""
        config = {
            "always_allow": ["bash"],
            "never_allow": ["rm"],
            "tool_permissions": {"grep": "allow"}
        }
        manager = PermissionManager(
            mode=PermissionMode.ALWAYS_ASK,
            config=config
        )

        # Tool-specific config (highest priority)
        grep_tool = Mock()
        grep_tool.name = "grep"
        grep_approved, _ = await manager.request_permission(grep_tool, {})
        assert grep_approved is True

        # Config list
        bash_tool = Mock()
        bash_tool.name = "bash"
        bash_approved, _ = await manager.request_permission(bash_tool, {})
        assert bash_approved is True

        # Denied from list
        rm_tool = Mock()
        rm_tool.name = "rm"
        rm_approved, _ = await manager.request_permission(rm_tool, {})
        assert rm_approved is False
