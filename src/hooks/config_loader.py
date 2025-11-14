"""
User Hook Configuration Loader

Loads and registers user-defined hooks from configuration files.
Supports multiple configuration sources with priority-based loading.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .types import HookEvent
from .manager import HookManager

logger = logging.getLogger(__name__)


class HookConfigLoader:
    """Load and register hooks from configuration files

    Supports configuration files at multiple locations:
    - Enterprise policy (highest priority)
    - ~/.tiny-claude/settings.json (user global)
    - .tiny-claude/settings.json (project)
    - .tiny-claude/settings.local.json (local, lowest priority)
    """

    def __init__(self):
        """Initialize the config loader"""
        self.loaded_configs: List[Path] = []
        self.failed_configs: List[tuple] = []

    async def load_hooks(
        self,
        hook_manager: HookManager,
        skip_errors: bool = True
    ) -> Dict[str, Any]:
        """Load and register hooks from all available config files

        Args:
            hook_manager: HookManager instance to register hooks with
            skip_errors: If True, skip files that can't be loaded; if False, raise exception

        Returns:
            Dictionary with loading statistics and results
        """
        self.loaded_configs.clear()
        self.failed_configs.clear()

        # Collect all config files in priority order
        config_files = self._collect_config_files()

        stats = {
            "total_files": len(config_files),
            "loaded_files": 0,
            "failed_files": 0,
            "total_handlers": 0,
            "registered_handlers": 0,
            "skipped_handlers": 0,
        }

        # Load each config file
        for config_path in config_files:
            try:
                handler_count = await self._load_config_file(
                    config_path, hook_manager
                )
                stats["loaded_files"] += 1
                stats["total_handlers"] += handler_count
                stats["registered_handlers"] += handler_count
                self.loaded_configs.append(config_path)

                logger.info(
                    f"Loaded {handler_count} hooks from {config_path}"
                )

            except Exception as e:
                stats["failed_files"] += 1
                self.failed_configs.append((config_path, str(e)))

                if skip_errors:
                    logger.warning(
                        f"Failed to load hooks from {config_path}: {e}"
                    )
                else:
                    raise

        return stats

    def _collect_config_files(self) -> List[Path]:
        """Collect all hook config files from the unified settings.json.

        Returns:
            List of Path objects in loading order (highest to lowest priority)
        """
        config_files: List[Path] = []

        # Unified config: ~/.tiny-claude-code/settings.json
        unified_config = Path.home() / ".tiny-claude-code" / "settings.json"
        if unified_config.exists():
            config_files.append(unified_config)

        return config_files

    async def _load_config_file(
        self,
        config_path: Path,
        hook_manager: HookManager
    ) -> int:
        """Load hooks from a single configuration file

        Args:
            config_path: Path to the configuration file
            hook_manager: HookManager to register handlers with

        Returns:
            Number of handlers registered

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            ValueError: If configuration is invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load JSON file
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Get hooks configuration
        hooks_config = config.get("hooks", {})
        custom_handlers = hooks_config.get("custom_handlers", [])

        handler_count = 0

        # Register each handler
        for handler_config in custom_handlers:
            try:
                # Skip disabled handlers
                if not handler_config.get("enabled", True):
                    continue

                # Validate configuration
                event_name = handler_config.get("event")
                handler_path = handler_config.get("handler")

                if not event_name or not handler_path:
                    logger.warning(
                        f"Invalid handler config in {config_path}: "
                        f"missing 'event' or 'handler'"
                    )
                    continue

                # Convert event name string to HookEvent
                try:
                    event = HookEvent(event_name)
                except ValueError:
                    logger.warning(
                        f"Unknown event type: {event_name} in {config_path}"
                    )
                    continue

                # Load the handler function
                from .secure_loader import SecureHookLoader
                loader = SecureHookLoader()
                handler = await loader.load_handler(handler_path)

                # Register with priority
                priority = handler_config.get("priority", 0)
                hook_manager.register(event, handler, priority=priority)

                handler_count += 1
                logger.debug(
                    f"Registered handler {handler_path} for {event_name} "
                    f"with priority {priority}"
                )

            except Exception as e:
                logger.warning(
                    f"Failed to load handler {handler_config.get('handler')}: {e}"
                )
                continue

        return handler_count

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded configurations

        Returns:
            Dictionary with loading statistics
        """
        return {
            "loaded_files": len(self.loaded_configs),
            "failed_files": len(self.failed_configs),
            "loaded_paths": [str(p) for p in self.loaded_configs],
            "failed_paths": [
                {"path": str(p), "error": e}
                for p, e in self.failed_configs
            ],
        }
