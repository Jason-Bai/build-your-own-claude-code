"""Output control commands"""

from .base import Command, CLIContext
from ..utils import OutputFormatter, OutputLevel


class VerboseCommand(Command):
    """切换详细输出模式"""

    name = "verbose"
    description = "Toggle verbose mode: /verbose on|off"

    async def execute(self, args: str, context: CLIContext) -> str:
        args = args.strip().lower()

        if args == "on":
            OutputFormatter.set_level(OutputLevel.VERBOSE)
            return "✓ Verbose mode enabled (showing tool parameters and thinking process)"

        elif args == "off":
            OutputFormatter.set_level(OutputLevel.NORMAL)
            return "✓ Verbose mode disabled (normal output level)"

        else:
            current = OutputFormatter.level.name.lower()
            return f"ℹ️  Current level: {current}. Usage: /verbose on|off"


class QuietCommand(Command):
    """切换安静模式"""

    name = "quiet"
    description = "Toggle quiet mode: /quiet on|off"

    async def execute(self, args: str, context: CLIContext) -> str:
        args = args.strip().lower()

        if args == "on":
            OutputFormatter.set_level(OutputLevel.QUIET)
            return "✓ Quiet mode enabled (only showing errors and agent responses)"

        elif args == "off":
            OutputFormatter.set_level(OutputLevel.NORMAL)
            return "✓ Quiet mode disabled (normal output level)"

        else:
            current = OutputFormatter.level.name.lower()
            return f"ℹ️  Current level: {current}. Usage: /quiet on|off"
