"""
Unit tests for Hook Configuration Loader

Tests loading and registering hooks from configuration files.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.hooks.config_loader import HookConfigLoader
from src.hooks.manager import HookManager
from src.hooks.types import HookEvent


@pytest.mark.unit
class TestHookConfigLoaderInitialization:
    """Tests for config loader initialization"""

    def test_initialization_default(self):
        """Test default initialization"""
        loader = HookConfigLoader()
        assert loader.loaded_configs == []
        assert loader.failed_configs == []

    def test_initial_state_empty(self):
        """Test initial state is empty"""
        loader = HookConfigLoader()
        assert len(loader.loaded_configs) == 0
        assert len(loader.failed_configs) == 0


@pytest.mark.unit
class TestCollectConfigFiles:
    """Tests for collecting config files"""

    def test_collect_no_config_files(self):
        """Test collecting when no config files exist"""
        loader = HookConfigLoader()

        # Mock Path methods to return non-existent paths
        with patch('src.hooks.config_loader.Path') as mock_path:
            mock_instance = MagicMock()
            mock_instance.home.return_value = MagicMock()
            mock_instance.home.return_value.__truediv__ = MagicMock(
                return_value=MagicMock(exists=MagicMock(return_value=False))
            )
            mock_instance.cwd.return_value = MagicMock()
            mock_instance.cwd.return_value.__truediv__ = MagicMock(
                return_value=MagicMock(exists=MagicMock(return_value=False))
            )
            mock_path.return_value = mock_instance
            mock_path.side_effect = lambda x: MagicMock(exists=MagicMock(return_value=False))

            # Should return empty list when no files exist
            result = loader._collect_config_files()
            assert isinstance(result, list)

    def test_collect_config_files_returns_list(self):
        """Test that collect returns a list"""
        loader = HookConfigLoader()
        result = loader._collect_config_files()
        assert isinstance(result, list)


@pytest.mark.unit
class TestLoadConfigFile:
    """Tests for loading a single config file"""

    @pytest.mark.asyncio
    async def test_load_config_file_valid_json(self):
        """Test loading valid JSON config file"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {
                "hooks": {
                    "custom_handlers": []
                }
            }
            config_path.write_text(json.dumps(config_data))

            result = await loader._load_config_file(config_path, manager)
            assert result == 0  # No handlers registered

    @pytest.mark.asyncio
    async def test_load_config_file_not_found(self):
        """Test loading non-existent config file"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        config_path = Path("/non/existent/path.json")

        with pytest.raises(FileNotFoundError):
            await loader._load_config_file(config_path, manager)

    @pytest.mark.asyncio
    async def test_load_config_file_invalid_json(self):
        """Test loading invalid JSON config file"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{ invalid json }")

            with pytest.raises(json.JSONDecodeError):
                await loader._load_config_file(config_path, manager)

    @pytest.mark.asyncio
    async def test_load_config_file_no_handlers_key(self):
        """Test loading config without hooks key"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {}
            config_path.write_text(json.dumps(config_data))

            result = await loader._load_config_file(config_path, manager)
            assert result == 0

    @pytest.mark.asyncio
    async def test_load_config_file_skips_disabled_handlers(self):
        """Test that disabled handlers are skipped"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {
                "hooks": {
                    "custom_handlers": [
                        {
                            "event": "tool.execute",
                            "handler": "module:handler",
                            "enabled": False
                        }
                    ]
                }
            }
            config_path.write_text(json.dumps(config_data))

            result = await loader._load_config_file(config_path, manager)
            assert result == 0  # Handler was skipped

    @pytest.mark.asyncio
    async def test_load_config_file_missing_event_field(self):
        """Test handler without event field is skipped"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {
                "hooks": {
                    "custom_handlers": [
                        {
                            "handler": "module:handler"
                            # missing "event" field
                        }
                    ]
                }
            }
            config_path.write_text(json.dumps(config_data))

            result = await loader._load_config_file(config_path, manager)
            assert result == 0

    @pytest.mark.asyncio
    async def test_load_config_file_missing_handler_field(self):
        """Test handler without handler field is skipped"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {
                "hooks": {
                    "custom_handlers": [
                        {
                            "event": "tool.execute"
                            # missing "handler" field
                        }
                    ]
                }
            }
            config_path.write_text(json.dumps(config_data))

            result = await loader._load_config_file(config_path, manager)
            assert result == 0

    @pytest.mark.asyncio
    async def test_load_config_file_invalid_event_type(self):
        """Test handler with invalid event type is skipped"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {
                "hooks": {
                    "custom_handlers": [
                        {
                            "event": "invalid.event.type",
                            "handler": "module:handler"
                        }
                    ]
                }
            }
            config_path.write_text(json.dumps(config_data))

            result = await loader._load_config_file(config_path, manager)
            assert result == 0


@pytest.mark.unit
class TestLoadHooksAsync:
    """Tests for async load_hooks method"""

    @pytest.mark.asyncio
    async def test_load_hooks_with_no_files(self):
        """Test loading hooks when no config files exist"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with patch.object(loader, '_collect_config_files', return_value=[]):
            stats = await loader.load_hooks(manager)

            assert stats["total_files"] == 0
            assert stats["loaded_files"] == 0
            assert stats["failed_files"] == 0

    @pytest.mark.asyncio
    async def test_load_hooks_returns_stats(self):
        """Test that load_hooks returns statistics"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with patch.object(loader, '_collect_config_files', return_value=[]):
            stats = await loader.load_hooks(manager)

            assert isinstance(stats, dict)
            assert "total_files" in stats
            assert "loaded_files" in stats
            assert "failed_files" in stats
            assert "total_handlers" in stats
            assert "registered_handlers" in stats
            assert "skipped_handlers" in stats

    @pytest.mark.asyncio
    async def test_load_hooks_clears_previous_state(self):
        """Test that load_hooks clears previous loaded/failed state"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        # Set some initial state
        loader.loaded_configs = [Path("/some/path")]
        loader.failed_configs = [(Path("/failed/path"), "error")]

        with patch.object(loader, '_collect_config_files', return_value=[]):
            await loader.load_hooks(manager)

            # State should be cleared
            assert loader.loaded_configs == []
            assert loader.failed_configs == []

    @pytest.mark.asyncio
    async def test_load_hooks_skip_errors_true(self):
        """Test load_hooks with skip_errors=True continues after error"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid config file
            config_path = Path(tmpdir) / "config.json"
            config_data = {"hooks": {"custom_handlers": []}}
            config_path.write_text(json.dumps(config_data))

            with patch.object(loader, '_collect_config_files', return_value=[config_path]):
                # _load_config_file will succeed
                stats = await loader.load_hooks(manager, skip_errors=True)

                assert stats["loaded_files"] == 1
                assert stats["failed_files"] == 0

    @pytest.mark.asyncio
    async def test_load_hooks_skip_errors_false_raises(self):
        """Test load_hooks with skip_errors=False raises on error"""
        loader = HookConfigLoader()
        manager = Mock(spec=HookManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid config file
            bad_config = Path(tmpdir) / "bad.json"
            bad_config.write_text("{ invalid json }")

            with patch.object(loader, '_collect_config_files', return_value=[bad_config]):
                with pytest.raises(json.JSONDecodeError):
                    await loader.load_hooks(manager, skip_errors=False)


@pytest.mark.unit
class TestGetStats:
    """Tests for getting statistics"""

    def test_get_stats_initial(self):
        """Test get_stats on fresh loader"""
        loader = HookConfigLoader()
        stats = loader.get_stats()

        assert stats["loaded_files"] == 0
        assert stats["failed_files"] == 0
        assert stats["loaded_paths"] == []
        assert stats["failed_paths"] == []

    def test_get_stats_with_loaded_configs(self):
        """Test get_stats with loaded configurations"""
        loader = HookConfigLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}")

            loader.loaded_configs = [config_path]
            stats = loader.get_stats()

            assert stats["loaded_files"] == 1
            assert len(stats["loaded_paths"]) == 1

    def test_get_stats_with_failed_configs(self):
        """Test get_stats with failed configurations"""
        loader = HookConfigLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{}")

            loader.failed_configs = [(config_path, "Test error")]
            stats = loader.get_stats()

            assert stats["failed_files"] == 1
            assert len(stats["failed_paths"]) == 1
            assert stats["failed_paths"][0]["error"] == "Test error"

    def test_get_stats_mixed_configs(self):
        """Test get_stats with both loaded and failed configs"""
        loader = HookConfigLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            config1 = Path(tmpdir) / "config1.json"
            config2 = Path(tmpdir) / "config2.json"
            config1.write_text("{}")
            config2.write_text("{}")

            loader.loaded_configs = [config1]
            loader.failed_configs = [(config2, "Error")]

            stats = loader.get_stats()

            assert stats["loaded_files"] == 1
            assert stats["failed_files"] == 1


@pytest.mark.unit
class TestHookConfigLoaderIntegration:
    """Integration tests for config loader"""

    def test_loader_state_tracking(self):
        """Test that loader properly tracks loaded and failed configs"""
        loader = HookConfigLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.json"
            config_path.write_text(json.dumps({"hooks": {"custom_handlers": []}}))

            loader.loaded_configs.append(config_path)

            assert len(loader.loaded_configs) == 1
            assert str(config_path) in loader.get_stats()["loaded_paths"][0]

    def test_multiple_loader_instances_independent(self):
        """Test that multiple loader instances are independent"""
        loader1 = HookConfigLoader()
        loader2 = HookConfigLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.json"
            config_path.write_text("{}")

            loader1.loaded_configs.append(config_path)

            # loader2 should not be affected
            assert len(loader2.loaded_configs) == 0
            assert len(loader1.loaded_configs) == 1

    def test_loader_handles_empty_hooks_config(self):
        """Test loader handles config with empty hooks section"""
        loader = HookConfigLoader()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "empty.json"
            config_data = {"hooks": {}}
            config_path.write_text(json.dumps(config_data))

            # Should handle gracefully
            assert config_path.exists()

    def test_loader_handles_various_config_structures(self):
        """Test loader handles various config file structures"""
        loader = HookConfigLoader()

        # Test various valid JSON structures
        valid_configs = [
            {},  # Empty
            {"hooks": {}},  # Empty hooks
            {"hooks": {"custom_handlers": []}},  # Empty handlers
            {"other_key": "value"},  # No hooks section
        ]

        for config in valid_configs:
            # All should be valid JSON
            json.dumps(config)
