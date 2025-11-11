"""Todo management tool"""

from typing import List, Dict
from .base import BaseTool, ToolResult, ToolPermissionLevel


class TodoManager:
    """Todo 管理器"""

    def __init__(self):
        self.todos: List[Dict] = []

    def update(self, todos: List[Dict]):
        """更新 todo 列表"""
        self.todos = todos

    def get_all(self) -> List[Dict]:
        """获取所有 todos"""
        return self.todos

    def clear(self):
        """清空 todos"""
        self.todos = []


class TodoWriteTool(BaseTool):
    """Todo 管理工具"""

    permission_level = ToolPermissionLevel.SAFE  # 只是内存操作，不涉及文件

    def __init__(self, todo_manager: TodoManager = None):
        self.todo_manager = todo_manager or TodoManager()

    @property
    def name(self) -> str:
        return "TodoWrite"

    @property
    def description(self) -> str:
        return """Manage task list for tracking progress.

Usage:
- todos: array of todo items, each with:
  - content: task description (imperative form, e.g., "Run tests")
  - activeForm: present continuous form (e.g., "Running tests")
  - status: "pending", "in_progress", or "completed"

Important:
- Keep exactly ONE task in_progress at a time
- Mark tasks completed immediately after finishing
- Use this for complex multi-step tasks"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "activeForm": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed"]
                            }
                        },
                        "required": ["content", "activeForm", "status"]
                    }
                }
            },
            "required": ["todos"]
        }

    async def execute(self, todos: List[Dict]) -> ToolResult:
        """更新 todo 列表"""
        try:
            # 验证 todos 格式
            for todo in todos:
                if "content" not in todo or "status" not in todo or "activeForm" not in todo:
                    return ToolResult(
                        success=False,
                        output="",
                        error="Each todo must have 'content', 'activeForm', and 'status' fields"
                    )

                if todo["status"] not in ["pending", "in_progress", "completed"]:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Invalid status: {todo['status']}"
                    )

            # 检查 in_progress 数量
            in_progress_count = sum(1 for t in todos if t["status"] == "in_progress")
            if in_progress_count > 1:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Only one task can be in_progress at a time, found {in_progress_count}"
                )

            # 更新 todos
            self.todo_manager.update(todos)

            # 生成摘要
            pending = sum(1 for t in todos if t["status"] == "pending")
            completed = sum(1 for t in todos if t["status"] == "completed")

            summary = f"Todos updated: {len(todos)} total ({pending} pending, {in_progress_count} in progress, {completed} completed)"

            return ToolResult(
                success=True,
                output=summary,
                metadata={
                    "total": len(todos),
                    "pending": pending,
                    "in_progress": in_progress_count,
                    "completed": completed
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error updating todos: {str(e)}"
            )
