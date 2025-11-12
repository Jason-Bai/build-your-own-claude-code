"""
Hook Configuration Validator

Validates hook configurations for security and correctness.
"""

import logging
from typing import List, Set

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a security violation is detected"""
    pass


class HookConfigValidator:
    """Validate hook configurations for security and correctness"""

    # Forbidden modules that cannot be imported as hooks
    FORBIDDEN_MODULES: Set[str] = {
        "os",
        "sys",
        "subprocess",
        "socket",
        "threading",
        "multiprocessing",
        "importlib",
        "__builtin__",
        "builtins",
        "__main__",
        "eval",
        "exec",
        "compile",
    }

    # Forbidden functions/attributes
    FORBIDDEN_FUNCTIONS: Set[str] = {
        "system",
        "exec",
        "eval",
        "compile",
        "open",
        "input",
        "help",
        "__import__",
    }

    # Max priority bounds
    MIN_PRIORITY: int = -1000
    MAX_PRIORITY: int = 1000

    def __init__(self, strict_mode: bool = False):
        """Initialize validator

        Args:
            strict_mode: If True, use stricter validation rules
        """
        self.strict_mode = strict_mode

    def validate_handler_path(self, handler_path: str) -> bool:
        """Validate handler path for security

        Args:
            handler_path: Handler path in format "module:function"

        Returns:
            True if valid

        Raises:
            SecurityError: If handler path violates security rules
            ValueError: If handler path format is invalid
        """
        # Check format
        if ":" not in handler_path:
            raise ValueError(
                f"Invalid handler path format: {handler_path}. "
                f"Expected 'module:function'"
            )

        parts = handler_path.split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid handler path format: {handler_path}. "
                f"Expected single colon separator"
            )

        module_name, func_name = parts

        # Validate module name
        if not module_name:
            raise ValueError("Module name cannot be empty")

        if not func_name:
            raise ValueError("Function name cannot be empty")

        # Check for forbidden modules
        if module_name in self.FORBIDDEN_MODULES:
            raise SecurityError(
                f"Forbidden module: {module_name}. "
                f"Cannot load hooks from: {', '.join(self.FORBIDDEN_MODULES)}"
            )

        # Check for private functions (starting with _)
        if func_name.startswith("_"):
            raise SecurityError(
                f"Cannot load private function: {func_name}. "
                f"Functions starting with '_' are not allowed"
            )

        # Check for forbidden function names
        if func_name in self.FORBIDDEN_FUNCTIONS:
            raise SecurityError(
                f"Forbidden function: {func_name}. "
                f"Cannot load: {', '.join(self.FORBIDDEN_FUNCTIONS)}"
            )

        # In strict mode, check for relative imports or suspicious patterns
        if self.strict_mode:
            if module_name.startswith("."):
                raise SecurityError(
                    f"Relative imports not allowed in strict mode: {module_name}"
                )

            if any(char in module_name for char in ["\\", "/", ";"]):
                raise SecurityError(
                    f"Invalid characters in module name: {module_name}"
                )

        return True

    def validate_priority(self, priority: int) -> bool:
        """Validate priority value

        Args:
            priority: Priority value to validate

        Returns:
            True if valid

        Raises:
            ValueError: If priority is out of bounds
        """
        if not isinstance(priority, int):
            raise TypeError(
                f"Priority must be an integer, got {type(priority).__name__}"
            )

        if not (self.MIN_PRIORITY <= priority <= self.MAX_PRIORITY):
            raise ValueError(
                f"Priority must be between {self.MIN_PRIORITY} and "
                f"{self.MAX_PRIORITY}, got {priority}"
            )

        return True

    def validate_event_name(self, event_name: str) -> bool:
        """Validate event name format

        Args:
            event_name: Event name to validate

        Returns:
            True if valid

        Raises:
            ValueError: If event name is invalid
        """
        if not event_name:
            raise ValueError("Event name cannot be empty")

        if not isinstance(event_name, str):
            raise TypeError(
                f"Event name must be a string, got {type(event_name).__name__}"
            )

        # Event names should be in format: "category.event"
        if "." not in event_name:
            logger.warning(
                f"Event name '{event_name}' doesn't follow 'category.event' format"
            )

        return True

    def validate_handler_config(self, config: dict) -> bool:
        """Validate a complete handler configuration

        Args:
            config: Handler configuration dictionary

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
            SecurityError: If configuration violates security rules
        """
        # Check required fields
        if "handler" not in config:
            raise ValueError("Handler configuration missing 'handler' field")

        if "event" not in config:
            raise ValueError("Handler configuration missing 'event' field")

        # Validate fields
        handler_path = config.get("handler")
        event_name = config.get("event")
        priority = config.get("priority", 0)
        enabled = config.get("enabled", True)

        # Validate types
        if not isinstance(handler_path, str):
            raise TypeError("'handler' must be a string")

        if not isinstance(event_name, str):
            raise TypeError("'event' must be a string")

        if not isinstance(priority, int):
            raise TypeError("'priority' must be an integer")

        if not isinstance(enabled, bool):
            raise TypeError("'enabled' must be a boolean")

        # Validate values
        self.validate_handler_path(handler_path)
        self.validate_event_name(event_name)
        self.validate_priority(priority)

        return True
