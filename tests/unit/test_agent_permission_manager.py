"""
Unit tests for Permission Manager module

Tests the PermissionManager class which manages tool execution permissions
with multiple modes (always_ask, auto_approve_safe, auto_approve_all, skip_all).
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from src.agents.permission_manager import PermissionManager, PermissionMode
from src.tools.base import ToolPermissionLevel


# Mock tool for testing
class MockTool:
    """Mock tool for testing permissions"""

    def __init__(self, name: str = "mock_tool", permission_level: ToolPermissionLevel = ToolPermissionLevel.NORMAL):
        self.name = name
        self.description = f"Mock {name} tool"
        self.permission_level = permission_level


@pytest.mark.unit
class TestPermissionManagerInitialization:
    """Tests for PermissionManager initialization"""

    def test_initialization_default(self):
        """Test initializing with default settings"""
        manager = PermissionManager()
        assert manager.mode == PermissionMode.AUTO_APPROVE_SAFE
        assert manager.config == {}
        assert manager.approved_tools == set()
        assert manager.denied_tools == set()
        assert manager.session_approved == set()
        assert manager.session_denied == set()

    def test_initialization_with_mode(self):
        """Test initializing with custom mode"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        assert manager.mode == PermissionMode.ALWAYS_ASK

    def test_initialization_with_config_always_allow(self):
        """Test initializing with pre-approved tools"""
        config = {"always_allow": ["tool1", "tool2"]}
        manager = PermissionManager(config=config)
        assert "tool1" in manager.approved_tools
        assert "tool2" in manager.approved_tools

    def test_initialization_with_config_never_allow(self):
        """Test initializing with denied tools"""
        config = {"never_allow": ["tool1", "tool2"]}
        manager = PermissionManager(config=config)
        assert "tool1" in manager.denied_tools
        assert "tool2" in manager.denied_tools

    def test_initialization_with_tool_permissions(self):
        """Test initializing with tool-specific permissions"""
        config = {
            "tool_permissions": {
                "tool1": "allow",
                "tool2": "deny"
            }
        }
        manager = PermissionManager(config=config)
        assert manager.tool_permissions["tool1"] == "allow"
        assert manager.tool_permissions["tool2"] == "deny"

    def test_initialization_with_complete_config(self):
        """Test initializing with complete config"""
        config = {
            "always_allow": ["tool1"],
            "never_allow": ["tool2"],
            "tool_permissions": {"tool3": "allow"}
        }
        manager = PermissionManager(config=config)
        assert "tool1" in manager.approved_tools
        assert "tool2" in manager.denied_tools
        assert manager.tool_permissions["tool3"] == "allow"


@pytest.mark.asyncio
@pytest.mark.unit
class TestPermissionRequestSkipAllMode:
    """Tests for SKIP_ALL permission mode"""

    async def test_skip_all_approves_all(self):
        """Test that SKIP_ALL mode approves everything"""
        manager = PermissionManager(mode=PermissionMode.SKIP_ALL)
        tool = MockTool(name="test_tool", permission_level=ToolPermissionLevel.DANGEROUS)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True
        assert message == ""

    async def test_skip_all_with_dangerous_tool(self):
        """Test that SKIP_ALL approves dangerous operations"""
        manager = PermissionManager(mode=PermissionMode.SKIP_ALL)
        tool = MockTool(name="bash", permission_level=ToolPermissionLevel.DANGEROUS)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    async def test_skip_all_with_safe_tool(self):
        """Test that SKIP_ALL approves safe operations"""
        manager = PermissionManager(mode=PermissionMode.SKIP_ALL)
        tool = MockTool(name="read", permission_level=ToolPermissionLevel.SAFE)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True


@pytest.mark.asyncio
@pytest.mark.unit
class TestPermissionRequestAutoApproveAllMode:
    """Tests for AUTO_APPROVE_ALL permission mode"""

    async def test_auto_approve_all_approves_all(self):
        """Test that AUTO_APPROVE_ALL mode approves everything"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)
        tool = MockTool(name="test_tool", permission_level=ToolPermissionLevel.DANGEROUS)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    async def test_auto_approve_all_with_multiple_tools(self):
        """Test AUTO_APPROVE_ALL with different tool levels"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_ALL)

        for level in [ToolPermissionLevel.SAFE, ToolPermissionLevel.NORMAL, ToolPermissionLevel.DANGEROUS]:
            tool = MockTool(name=f"tool_{level.value}", permission_level=level)
            approved, message = await manager.request_permission(tool, {})
            assert approved is True


@pytest.mark.asyncio
@pytest.mark.unit
class TestPermissionRequestAutoApproveSafeMode:
    """Tests for AUTO_APPROVE_SAFE permission mode (default)"""

    async def test_auto_approve_safe_allows_safe_tools(self):
        """Test that safe tools are auto-approved"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        tool = MockTool(name="read", permission_level=ToolPermissionLevel.SAFE)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    async def test_auto_approve_safe_requires_approval_for_normal(self):
        """Test that normal tools require user approval"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        tool = MockTool(name="write", permission_level=ToolPermissionLevel.NORMAL)

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (False, "Permission denied")
            approved, message = await manager.request_permission(tool, {})

            # Should call prompt for NORMAL tools
            mock_prompt.assert_called_once()

    async def test_auto_approve_safe_requires_approval_for_dangerous(self):
        """Test that dangerous tools require user approval"""
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE)
        tool = MockTool(name="bash", permission_level=ToolPermissionLevel.DANGEROUS)

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (False, "Permission denied")
            approved, message = await manager.request_permission(tool, {})

            # Should call prompt for DANGEROUS tools
            mock_prompt.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
class TestPermissionPreApproval:
    """Tests for pre-approved tools"""

    async def test_pre_approved_tool_bypasses_prompt(self):
        """Test that pre-approved tools don't prompt"""
        config = {"always_allow": ["read"]}
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK, config=config)
        tool = MockTool(name="read", permission_level=ToolPermissionLevel.NORMAL)

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            approved, message = await manager.request_permission(tool, {})

            assert approved is True
            mock_prompt.assert_not_called()

    async def test_denied_tool_bypasses_prompt(self):
        """Test that denied tools reject without prompting"""
        config = {"never_allow": ["bash"]}
        manager = PermissionManager(config=config)
        tool = MockTool(name="bash", permission_level=ToolPermissionLevel.DANGEROUS)

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            approved, message = await manager.request_permission(tool, {})

            assert approved is False
            assert "Permission denied" in message
            mock_prompt.assert_not_called()

    async def test_tool_permission_config_allow(self):
        """Test tool-specific config with allow"""
        config = {"tool_permissions": {"mytool": "allow"}}
        manager = PermissionManager(config=config)
        tool = MockTool(name="mytool", permission_level=ToolPermissionLevel.DANGEROUS)

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    async def test_tool_permission_config_deny(self):
        """Test tool-specific config with deny"""
        config = {"tool_permissions": {"mytool": "deny"}}
        manager = PermissionManager(config=config)
        tool = MockTool(name="mytool", permission_level=ToolPermissionLevel.NORMAL)

        approved, message = await manager.request_permission(tool, {})

        assert approved is False
        assert "Permission denied" in message


@pytest.mark.asyncio
@pytest.mark.unit
class TestSessionLevelPermissions:
    """Tests for session-level permission tracking"""

    async def test_session_approved_tools(self):
        """Test that session-approved tools are remembered"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = MockTool(name="tool1", permission_level=ToolPermissionLevel.NORMAL)

        # Manually add to session approved (simulating user choice)
        manager.session_approved.add("tool1")

        approved, message = await manager.request_permission(tool, {})

        assert approved is True

    async def test_session_denied_tools(self):
        """Test that session-denied tools remain denied"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = MockTool(name="tool1", permission_level=ToolPermissionLevel.NORMAL)

        # Manually add to session denied
        manager.session_denied.add("tool1")

        approved, message = await manager.request_permission(tool, {})

        assert approved is False
        assert "Permission denied" in message

    async def test_session_vs_permanent_permissions(self):
        """Test priority: permanent denied overrides session approved"""
        config = {"never_allow": ["tool1"]}
        manager = PermissionManager(config=config)
        tool = MockTool(name="tool1")

        # Try to approve in session (should be overridden)
        manager.session_approved.add("tool1")

        approved, message = await manager.request_permission(tool, {})

        # Should still be denied (permanent takes precedence)
        assert approved is False


@pytest.mark.unit
class TestPermissionStatistics:
    """Tests for permission statistics"""

    def test_get_stats_default(self):
        """Test getting stats with default configuration"""
        manager = PermissionManager()
        stats = manager.get_stats()

        assert stats["mode"] == "auto_approve_safe"
        assert stats["always_allow"] == []
        assert stats["never_allow"] == []
        assert stats["session_approved"] == []
        assert stats["session_denied"] == []

    def test_get_stats_with_approvals(self):
        """Test stats include approved tools"""
        config = {"always_allow": ["tool1", "tool2"]}
        manager = PermissionManager(config=config)
        stats = manager.get_stats()

        assert "tool1" in stats["always_allow"]
        assert "tool2" in stats["always_allow"]

    def test_get_stats_with_denials(self):
        """Test stats include denied tools"""
        config = {"never_allow": ["tool1", "tool2"]}
        manager = PermissionManager(config=config)
        stats = manager.get_stats()

        assert "tool1" in stats["never_allow"]
        assert "tool2" in stats["never_allow"]

    def test_get_stats_with_session_changes(self):
        """Test stats reflect session changes"""
        manager = PermissionManager()
        manager.session_approved.add("tool1")
        manager.session_denied.add("tool2")
        stats = manager.get_stats()

        assert "tool1" in stats["session_approved"]
        assert "tool2" in stats["session_denied"]

    def test_get_stats_includes_tool_permissions(self):
        """Test stats include tool-specific permissions"""
        config = {"tool_permissions": {"tool1": "allow"}}
        manager = PermissionManager(config=config)
        stats = manager.get_stats()

        assert stats["tool_permissions"]["tool1"] == "allow"


@pytest.mark.unit
class TestPermissionSavePreferences:
    """Tests for saving permissions to config file"""

    def test_save_preferences_new_file(self):
        """Test saving preferences to new config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            manager = PermissionManager()
            manager.approved_tools.add("tool1")
            manager.denied_tools.add("tool2")

            result = manager.save_preferences(str(config_path))

            assert result is True
            assert config_path.exists()

            # Verify saved content
            with open(config_path) as f:
                saved_config = json.load(f)
            assert "tool1" in saved_config["permissions"]["always_allow"]
            assert "tool2" in saved_config["permissions"]["never_allow"]

    def test_save_preferences_existing_file(self):
        """Test saving preferences to existing config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"

            # Create existing config
            existing_config = {"other_setting": "value"}
            with open(config_path, 'w') as f:
                json.dump(existing_config, f)

            # Save preferences
            manager = PermissionManager()
            manager.approved_tools.add("tool1")
            result = manager.save_preferences(str(config_path))

            assert result is True

            # Verify existing settings are preserved
            with open(config_path) as f:
                saved_config = json.load(f)
            assert saved_config["other_setting"] == "value"
            assert "tool1" in saved_config["permissions"]["always_allow"]

    def test_save_preferences_empty_permissions(self):
        """Test saving empty permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            manager = PermissionManager()

            result = manager.save_preferences(str(config_path))

            assert result is True
            with open(config_path) as f:
                saved_config = json.load(f)
            assert saved_config["permissions"]["always_allow"] == []
            assert saved_config["permissions"]["never_allow"] == []

    def test_save_preferences_unicode(self):
        """Test saving preferences with unicode tool names"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            manager = PermissionManager()
            manager.approved_tools.add("工具1")
            manager.approved_tools.add("tool_中文")

            result = manager.save_preferences(str(config_path))

            assert result is True
            with open(config_path, encoding='utf-8') as f:
                saved_config = json.load(f)
            assert "工具1" in saved_config["permissions"]["always_allow"]


@pytest.mark.unit
class TestPermissionModes:
    """Tests for all permission modes"""

    def test_all_modes_exist(self):
        """Test all permission modes are defined"""
        modes = [
            PermissionMode.ALWAYS_ASK,
            PermissionMode.AUTO_APPROVE_SAFE,
            PermissionMode.AUTO_APPROVE_ALL,
            PermissionMode.SKIP_ALL
        ]
        assert len(modes) == 4

    def test_mode_values(self):
        """Test mode values are correct"""
        assert PermissionMode.ALWAYS_ASK.value == "always_ask"
        assert PermissionMode.AUTO_APPROVE_SAFE.value == "auto_approve_safe"
        assert PermissionMode.AUTO_APPROVE_ALL.value == "auto_approve_all"
        assert PermissionMode.SKIP_ALL.value == "skip_all"


@pytest.mark.unit
class TestPermissionEdgeCases:
    """Tests for edge cases"""

    def test_duplicate_tools_in_config(self):
        """Test handling of duplicate tools in config"""
        config = {
            "always_allow": ["tool1", "tool1"],
            "never_allow": ["tool2", "tool2"]
        }
        manager = PermissionManager(config=config)

        # Sets should deduplicate
        assert len(manager.approved_tools) == 1
        assert len(manager.denied_tools) == 1

    def test_empty_config(self):
        """Test with empty config dict"""
        manager = PermissionManager(config={})
        assert manager.approved_tools == set()
        assert manager.denied_tools == set()
        assert manager.tool_permissions == {}

    def test_none_config(self):
        """Test with None config"""
        manager = PermissionManager(config=None)
        assert manager.config == {}

    def test_permission_priority_hierarchy(self):
        """Test the permission check priority"""
        # Priority: SKIP_ALL > AUTO_APPROVE_ALL > tool_config > pre_approved > session > mode
        config = {
            "always_allow": ["tool1"],
            "tool_permissions": {"tool2": "allow"}
        }
        manager = PermissionManager(mode=PermissionMode.AUTO_APPROVE_SAFE, config=config)

        # Approved tool should remain approved even with AUTO_APPROVE_SAFE
        # (because pre-approved > mode logic)
        assert "tool1" in manager.approved_tools

    def test_multiple_managers_independent(self):
        """Test that multiple manager instances are independent"""
        manager1 = PermissionManager()
        manager2 = PermissionManager()

        manager1.approved_tools.add("tool1")
        manager2.approved_tools.add("tool2")

        assert "tool1" in manager1.approved_tools
        assert "tool1" not in manager2.approved_tools


@pytest.mark.asyncio
@pytest.mark.unit
class TestPermissionPromptUser:
    """Tests for user prompt functionality"""

    async def test_prompt_user_called_for_unspecified_tool(self):
        """Test that _prompt_user is called for tools without pre-set permissions"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = MockTool(name="unknown", permission_level=ToolPermissionLevel.NORMAL)

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (True, "")
            await manager.request_permission(tool, {})

            mock_prompt.assert_called_once_with(tool, {})

    async def test_prompt_user_receives_tool_and_params(self):
        """Test that _prompt_user receives correct arguments"""
        manager = PermissionManager(mode=PermissionMode.ALWAYS_ASK)
        tool = MockTool(name="test", permission_level=ToolPermissionLevel.NORMAL)
        params = {"path": "/test/file", "data": "content"}

        with patch.object(manager, '_prompt_user', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = (True, "")
            await manager.request_permission(tool, params)

            called_tool, called_params = mock_prompt.call_args[0]
            assert called_tool.name == "test"
            assert called_params == params
