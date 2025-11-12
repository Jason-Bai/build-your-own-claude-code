"""
Global Hooks System

Event-driven architecture for non-invasive system integration and monitoring.
"""

from .types import HookEvent, HookContext, HookHandler
from .manager import HookManager
from .builder import HookContextBuilder
from .config_loader import HookConfigLoader
from .validator import HookConfigValidator, SecurityError
from .secure_loader import SecureHookLoader

__all__ = [
    "HookEvent",
    "HookContext",
    "HookHandler",
    "HookManager",
    "HookContextBuilder",
    "HookConfigLoader",
    "HookConfigValidator",
    "SecurityError",
    "SecureHookLoader",
]
