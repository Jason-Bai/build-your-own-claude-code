"""Summarization prompts for context compression"""


def get_summarization_prompt(
    old_messages: str,
    previous_summary: str = ""
) -> str:
    """
    生成用于摘要的 prompt

    Args:
        old_messages: 需要摘要的旧消息
        previous_summary: 之前的摘要（如果有）

    Returns:
        摘要 prompt
    """
    summary_section = f"Previous summary: {previous_summary}" if previous_summary else "Previous summary: None"

    return f"""
{summary_section}

New messages to summarize:
{old_messages}

Please provide a concise summary (3-5 sentences) of the key actions,
decisions, and context from these messages. Focus on:
- Files that were modified
- Commands that were executed
- Important decisions made
- Current state of the task

Keep the summary focused on facts and outcomes, not on the conversation flow.
"""


def get_task_decomposition_prompt(task: str) -> str:
    """
    生成用于任务分解的 prompt

    Args:
        task: 需要分解的任务描述

    Returns:
        任务分解 prompt
    """
    return f"""
Task to decompose: {task}

Please break down this task into specific, actionable steps.
For each step, provide:
1. A clear description of what needs to be done
2. Which tools should be used
3. Expected outcome

Format your response as a numbered list of steps.
"""
