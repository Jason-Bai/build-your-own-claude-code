"""Prompt templates and utilities"""

from .system import (
    get_system_prompt,
    get_custom_system_prompt,
    BASE_SYSTEM,
    CAPABILITIES,
    TOOL_GUIDELINES,
    COMMUNICATION_STYLE,
    WORKFLOW
)
from .summarization import (
    get_summarization_prompt,
    get_task_decomposition_prompt
)
from .roles import (
    get_debugger_prompt,
    get_code_reviewer_prompt,
    get_refactoring_assistant_prompt
)

__all__ = [
    # System prompts
    "get_system_prompt",
    "get_custom_system_prompt",
    "BASE_SYSTEM",
    "CAPABILITIES",
    "TOOL_GUIDELINES",
    "COMMUNICATION_STYLE",
    "WORKFLOW",
    # Summarization prompts
    "get_summarization_prompt",
    "get_task_decomposition_prompt",
    # Role prompts
    "get_debugger_prompt",
    "get_code_reviewer_prompt",
    "get_refactoring_assistant_prompt",
]
