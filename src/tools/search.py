"""Search tools: Glob and Grep"""

import glob
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Callable, Awaitable
from .base import BaseTool, ToolResult, ToolPermissionLevel


class GlobTool(BaseTool):
    """文件模式匹配工具"""

    permission_level = ToolPermissionLevel.SAFE  # 只读搜索

    @property
    def name(self) -> str:
        return "Glob"

    @property
    def description(self) -> str:
        return """Fast file pattern matching tool.

Usage:
- pattern: glob pattern like "**/*.py" or "src/**/*.ts"
- path: directory to search in (optional, defaults to current directory)"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The glob pattern to match files against"
                },
                "path": {
                    "type": "string",
                    "description": "The directory to search in"
                }
            },
            "required": ["pattern"]
        }

    async def execute(self, pattern: str, path: str = ".",
                     on_chunk: Optional[Callable[[str], Awaitable[None]]] = None) -> ToolResult:
        """执行文件搜索"""
        try:
            search_path = Path(path)

            if not search_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Directory not found: {path}"
                )

            # 执行 glob 搜索
            full_pattern = str(search_path / pattern)
            matches = glob.glob(full_pattern, recursive=True)

            # 过滤掉目录，只保留文件
            files = [f for f in matches if os.path.isfile(f)]

            # 按修改时间排序
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            if not files:
                return ToolResult(
                    success=True,
                    output="No files found",
                    metadata={"count": 0}
                )

            # 格式化输出
            output = "\n".join(files)

            return ToolResult(
                success=True,
                output=output,
                metadata={"count": len(files)}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error in glob search: {str(e)}"
            )


class GrepTool(BaseTool):
    """代码搜索工具（基于 grep）"""

    permission_level = ToolPermissionLevel.SAFE  # 只读搜索

    @property
    def name(self) -> str:
        return "Grep"

    @property
    def description(self) -> str:
        return """Search for patterns in files using regex.

Usage:
- pattern: regex pattern to search for
- path: file or directory to search in (optional, defaults to current directory)
- glob: glob pattern to filter files (e.g., "*.py")
- output_mode: "files_with_matches" (default), "content", or "count"
- case_insensitive: case insensitive search (default False)"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The regex pattern to search for"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in"
                },
                "glob": {
                    "type": "string",
                    "description": "Glob pattern to filter files"
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["files_with_matches", "content", "count"],
                    "description": "Output mode",
                    "default": "files_with_matches"
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Case insensitive search",
                    "default": False
                }
            },
            "required": ["pattern"]
        }

    async def execute(self, pattern: str, path: str = ".", glob: str = None,
                     output_mode: str = "files_with_matches",
                     case_insensitive: bool = False,
                     on_chunk: Optional[Callable[[str], Awaitable[None]]] = None) -> ToolResult:
        """执行代码搜索"""
        try:
            # 构建 grep 命令
            cmd = ["grep", "-r"]

            # 添加选项
            if case_insensitive:
                cmd.append("-i")

            if output_mode == "files_with_matches":
                cmd.append("-l")
            elif output_mode == "count":
                cmd.append("-c")
            else:  # content
                cmd.append("-n")

            # 添加模式
            cmd.append(pattern)

            # 添加路径
            cmd.append(path)

            # 添加 glob 过滤
            if glob:
                cmd.extend(["--include", glob])

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # grep 返回 1 表示没找到匹配，这不算错误
            if result.returncode > 1:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Grep command failed: {result.stderr}"
                )

            output = result.stdout.strip()

            if not output:
                output = "No matches found"

            return ToolResult(
                success=True,
                output=output,
                metadata={"output_mode": output_mode}
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error="Search timed out after 30s"
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                output="",
                error="grep command not found. Please install grep."
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error in grep search: {str(e)}"
            )
