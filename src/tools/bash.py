"""Bash command execution tool"""

import asyncio
import shlex
from .base import BaseTool, ToolResult, ToolPermissionLevel


class BashTool(BaseTool):
    """执行 Bash 命令"""

    permission_level = ToolPermissionLevel.DANGEROUS  # 命令执行是危险操作

    @property
    def name(self) -> str:
        return "Bash"

    @property
    def description(self) -> str:
        return """Executes a bash command with optional timeout.

Usage:
- command: the bash command to execute
- timeout: timeout in milliseconds (default 120000 = 2 minutes)
- description: brief description of what the command does"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in milliseconds",
                    "default": 120000
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what this command does"
                }
            },
            "required": ["command"]
        }

    async def execute(self, command: str, timeout: int = 120000,
                     description: str = "") -> ToolResult:
        """执行 Bash 命令"""
        try:
            # 转换超时时间为秒
            timeout_seconds = timeout / 1000.0

            # 执行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command timed out after {timeout_seconds}s"
                )

            # 解码输出
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            # 合并输出
            output_parts = []
            if stdout_text:
                output_parts.append(stdout_text)
            if stderr_text:
                output_parts.append(f"[stderr]\n{stderr_text}")

            output = "\n".join(output_parts) if output_parts else "(no output)"

            # 检查返回码
            success = process.returncode == 0

            if not success:
                error_msg = f"Command exited with code {process.returncode}"
                if stderr_text:
                    error_msg += f"\n{stderr_text}"
            else:
                error_msg = None

            return ToolResult(
                success=success,
                output=output,
                error=error_msg,
                metadata={
                    "return_code": process.returncode,
                    "command": command
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error executing command: {str(e)}"
            )
