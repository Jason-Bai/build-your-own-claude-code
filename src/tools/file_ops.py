"""File operation tools: Read, Write, Edit"""

import os
from pathlib import Path
from typing import Optional, Callable, Awaitable
from .base import BaseTool, ToolResult, ToolPermissionLevel


class ReadTool(BaseTool):
    """读取文件内容"""

    permission_level = ToolPermissionLevel.SAFE  # 只读操作

    @property
    def name(self) -> str:
        return "Read"

    @property
    def description(self) -> str:
        return """Reads a file from the filesystem. Returns content with line numbers.

Usage:
- file_path: absolute path to the file
- offset: line number to start from (optional)
- limit: number of lines to read (optional, default 2000)"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to read"
                },
                "offset": {
                    "type": "number",
                    "description": "The line number to start reading from"
                },
                "limit": {
                    "type": "number",
                    "description": "The number of lines to read"
                }
            },
            "required": ["file_path"]
        }

    async def execute(self, file_path: str, on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
                     offset: int = 0, limit: int = 2000) -> ToolResult:
        """读取文件内容"""
        try:
            path = Path(file_path)

            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}"
                )

            if not path.is_file():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path is not a file: {file_path}"
                )

            # 读取文件
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 应用 offset 和 limit
            start = offset
            end = min(offset + limit, len(lines))
            selected_lines = lines[start:end]

            # 格式化输出（带行号）
            output_lines = []
            for i, line in enumerate(selected_lines, start=start + 1):
                # 截断过长的行
                if len(line) > 2000:
                    line = line[:2000] + "... (truncated)\n"
                output_lines.append(f"{i:6d}\t{line.rstrip()}")

            output = "\n".join(output_lines)

            metadata = {
                "total_lines": len(lines),
                "displayed_lines": len(selected_lines),
                "offset": start,
                "limit": limit
            }

            return ToolResult(
                success=True,
                output=output,
                metadata=metadata
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                output="",
                error=f"File is not a text file or uses unsupported encoding: {file_path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error reading file: {str(e)}"
            )


class WriteTool(BaseTool):
    """写入文件（创建或覆盖）"""

    permission_level = ToolPermissionLevel.NORMAL  # 文件写入操作

    @property
    def name(self) -> str:
        return "Write"

    @property
    def description(self) -> str:
        return """Writes content to a file. Creates new file or overwrites existing file.

Usage:
- file_path: absolute path to the file
- content: content to write"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }

    async def execute(self, file_path: str, content: str,
                     on_chunk: Optional[Callable[[str], Awaitable[None]]] = None) -> ToolResult:
        """写入文件"""
        try:
            path = Path(file_path)

            # 确保父目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            lines = content.count('\n') + 1

            return ToolResult(
                success=True,
                output=f"File written successfully: {file_path} ({lines} lines)",
                metadata={"lines": lines, "bytes": len(content.encode('utf-8'))}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error writing file: {str(e)}"
            )


class EditTool(BaseTool):
    """编辑文件（精确字符串替换）"""

    permission_level = ToolPermissionLevel.NORMAL  # 文件编辑操作

    @property
    def name(self) -> str:
        return "Edit"

    @property
    def description(self) -> str:
        return """Performs exact string replacement in a file.

Usage:
- file_path: absolute path to the file
- old_string: exact string to find and replace
- new_string: replacement string
- replace_all: if True, replace all occurrences; if False (default), only replace if unique"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to edit"
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact string to find and replace"
                },
                "new_string": {
                    "type": "string",
                    "description": "The replacement string"
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Whether to replace all occurrences",
                    "default": False
                }
            },
            "required": ["file_path", "old_string", "new_string"]
        }

    async def execute(self, file_path: str, old_string: str, new_string: str,
                     replace_all: bool = False,
                     on_chunk: Optional[Callable[[str], Awaitable[None]]] = None) -> ToolResult:
        """编辑文件"""
        try:
            path = Path(file_path)

            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}"
                )

            # 读取文件
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查 old_string 是否存在
            if old_string not in content:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"String not found in file: {old_string[:100]}..."
                )

            # 计数
            count = content.count(old_string)

            # 检查唯一性
            if not replace_all and count > 1:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"String appears {count} times in file. Use replace_all=True to replace all occurrences, or provide a more specific string."
                )

            # 替换
            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)

            # 写回文件
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            replacements = count if replace_all else 1

            return ToolResult(
                success=True,
                output=f"File edited successfully: {file_path} ({replacements} replacement(s))",
                metadata={"replacements": replacements}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error editing file: {str(e)}"
            )
