"""
Global Hooks System

Event-driven architecture for non-invasive system integration and monitoring.
"""

from .types import HookEvent, HookContext, HookHandler
from .manager import HookManager
from .builder import HookContextBuilder

__all__ = [
    "HookEvent",
    "HookContext",
    "HookHandler",
    "HookManager",
    "HookContextBuilder",
]
