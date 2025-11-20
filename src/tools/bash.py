"""Bash command execution tool"""

import asyncio
import shlex
from typing import Optional, Callable, Awaitable
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

    async def execute(self, command: str, on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
                     timeout: int = 120000, description: str = "") -> ToolResult:
        """执行 Bash 命令"""
        try:
            # 转换超时时间为秒
            timeout_seconds = timeout / 1000.0

            # 执行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT, # Redirect stderr to stdout for unified streaming
                shell=True
            )

            output_buffer = []

            async def read_stream():
                """Read stream with robust error handling for callbacks"""
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    decoded_line = line.decode('utf-8', errors='replace')
                    output_buffer.append(decoded_line)

                    # Call chunk callback with error handling
                    if on_chunk:
                        try:
                            await on_chunk(decoded_line)
                        except Exception as e:
                            # Log the error but don't interrupt tool execution
                            import logging
                            logging.getLogger(__name__).error(
                                f"Error in chunk callback: {e}", exc_info=True
                            )
                            # Continue execution even if callback fails

            try:
                # Wait for both the process to finish and the stream reading to finish
                # But we need to enforce timeout
                await asyncio.wait_for(read_stream(), timeout=timeout_seconds)
                await process.wait() # Ensure process is actually dead/reaped

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    output="".join(output_buffer),
                    error=f"Command timed out after {timeout_seconds}s"
                )

            output = "".join(output_buffer) if output_buffer else "(no output)"

            # 检查返回码
            success = process.returncode == 0
            error_msg = None if success else f"Command exited with code {process.returncode}"

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