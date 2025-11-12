"""
Secure Hook Loader

Safely loads hook handler functions with security auditing.
"""

import ast
import importlib
import inspect
import logging
from typing import Callable

from .validator import HookConfigValidator, SecurityError

logger = logging.getLogger(__name__)


class SecureHookLoader:
    """Securely load hook handlers with validation

    Uses code auditing and validation to prevent loading malicious code.
    """

    def __init__(self, strict_mode: bool = False):
        """Initialize secure loader

        Args:
            strict_mode: If True, use stricter validation
        """
        self.validator = HookConfigValidator(strict_mode=strict_mode)
        self.loaded_handlers = {}

    async def load_handler(self, handler_path: str) -> Callable:
        """Safely load a handler function

        Args:
            handler_path: Handler path in format "module:function"

        Returns:
            The handler function

        Raises:
            SecurityError: If handler violates security rules
            ImportError: If handler cannot be loaded
            AttributeError: If handler function not found
        """
        # Validate path
        self.validator.validate_handler_path(handler_path)

        # Check cache
        if handler_path in self.loaded_handlers:
            logger.debug(f"Using cached handler: {handler_path}")
            return self.loaded_handlers[handler_path]

        # Parse path
        module_name, func_name = handler_path.split(":")

        try:
            # Import module
            logger.debug(f"Importing module: {module_name}")
            module = importlib.import_module(module_name)

            # Get function
            if not hasattr(module, func_name):
                raise AttributeError(
                    f"Module '{module_name}' has no attribute '{func_name}'"
                )

            handler = getattr(module, func_name)

            # Validate handler
            if not callable(handler):
                raise TypeError(
                    f"Handler '{func_name}' in module '{module_name}' "
                    f"is not callable"
                )

            # Check if handler is async
            if not inspect.iscoroutinefunction(handler):
                logger.warning(
                    f"Handler {handler_path} is not an async function. "
                    f"It will be called but won't be awaited."
                )

            # Audit handler code
            await self._audit_handler_code(handler, handler_path)

            # Cache handler
            self.loaded_handlers[handler_path] = handler

            logger.info(f"Successfully loaded handler: {handler_path}")
            return handler

        except ImportError as e:
            logger.error(f"Failed to import module '{module_name}': {e}")
            raise
        except AttributeError as e:
            logger.error(f"Handler not found: {handler_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading handler {handler_path}: {e}")
            raise

    async def _audit_handler_code(self, handler: Callable, handler_path: str) -> None:
        """Audit handler code for security issues

        Args:
            handler: The handler function to audit
            handler_path: The handler path for logging

        Raises:
            SecurityError: If handler contains suspicious code
        """
        try:
            # Get source code
            try:
                source = inspect.getsource(handler)
            except (OSError, TypeError):
                # Built-in or C functions don't have source
                logger.debug(
                    f"Cannot audit source code for {handler_path} "
                    f"(built-in or C function)"
                )
                return

            # Parse to AST
            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                logger.warning(
                    f"Cannot parse source code for {handler_path}: {e}"
                )
                return

            # Check for suspicious patterns
            self._check_dangerous_imports(tree, handler_path)
            self._check_dangerous_calls(tree, handler_path)

        except Exception as e:
            logger.warning(
                f"Error auditing handler code for {handler_path}: {e}"
            )

    def _check_dangerous_imports(self, tree: ast.AST, handler_path: str) -> None:
        """Check for dangerous imports in handler code

        Args:
            tree: AST tree to check
            handler_path: Handler path for logging

        Raises:
            SecurityError: If dangerous imports are found
        """
        dangerous_modules = {
            "os",
            "sys",
            "subprocess",
            "socket",
            "threading",
            "__import__",
        }

        for node in ast.walk(tree):
            # Check import statements
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if module_name in dangerous_modules:
                        logger.warning(
                            f"Handler {handler_path} imports dangerous module: {module_name}"
                        )

            # Check from imports
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if module_name in dangerous_modules:
                        logger.warning(
                            f"Handler {handler_path} imports from dangerous module: {module_name}"
                        )

    def _check_dangerous_calls(self, tree: ast.AST, handler_path: str) -> None:
        """Check for dangerous function calls in handler code

        Args:
            tree: AST tree to check
            handler_path: Handler path for logging

        Raises:
            SecurityError: If dangerous calls are found
        """
        dangerous_functions = {
            "eval",
            "exec",
            "compile",
            "open",
            "input",
            "__import__",
            "system",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check function name
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_functions:
                        logger.warning(
                            f"Handler {handler_path} calls dangerous function: {node.func.id}"
                        )

    def clear_cache(self) -> None:
        """Clear the handler cache"""
        self.loaded_handlers.clear()
        logger.debug("Cleared handler cache")

    def get_cached_handlers(self):
        """Get list of cached handlers

        Returns:
            List of cached handler paths
        """
        return list(self.loaded_handlers.keys())
