import asyncio
import os
import sys
from pathlib import Path

from ..commands import CLIContext, command_registry, register_builtin_commands
from ..utils import OutputFormatter, OutputLevel, get_input_manager
from ..events import get_event_bus
from ..config.loader import load_config
from ..config.args import parse_args
from ..initialization.setup import initialize_agent, _setup_event_listeners

async def main():
    """Main CLI application entry point"""
    args = parse_args()

    # Configure output level
    if args.verbose:
        OutputFormatter.set_level(OutputLevel.VERBOSE)
    elif args.quiet:
        OutputFormatter.set_level(OutputLevel.QUIET)
    else:
        OutputFormatter.set_level(OutputLevel.NORMAL)

    # Load configuration and initialize agent
    config = load_config(args.config)
    agent = await initialize_agent(config, args)
    await _setup_event_listeners(get_event_bus())

    # Register all built-in commands
    register_builtin_commands()

    # Create CLI context
    cli_context = CLIContext(agent, config={})

    # Print welcome message
    claude_md_info = None
    claude_md_path = Path.cwd() / "CLAUDE.md"
    if claude_md_path.exists():
        try:
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                claude_md_info = f.read()
        except:
            pass

    OutputFormatter.print_welcome(
        model_name=agent.client.model_name,
        provider=config.get("model", {}).get("provider", "unknown"),
        tools_count=len(agent.tool_manager.tools) if hasattr(agent, 'tool_manager') else 0,
        claude_md_info=claude_md_info
    )

    # Load project context from CLAUDE.md if present
    if claude_md_info:
        try:
            agent.context_manager.add_user_message(
                f"[System: Project Context]\n\n{claude_md_info}"
            )
            OutputFormatter.success(
                f"Auto-loaded CLAUDE.md ({len(claude_md_info)} chars)")
        except Exception as e:
            OutputFormatter.warning(f"Failed to load CLAUDE.md: {e}")

    # Initialize input manager with command registry (dependency injection)
    input_manager = get_input_manager()

    # Main REPL loop
    while True:
        try:
            user_input = await input_manager.async_get_input()
            if not user_input:
                continue

            # Check if it's a command
            if command_registry.is_command(user_input):
                result = await command_registry.execute(user_input, cli_context)
                if result:
                    OutputFormatter.print_assistant_response(result)
                continue

            # Otherwise, send to agent
            result = await agent.run(user_input, verbose=True)
            if isinstance(result, dict):
                final_response = result.get("final_response", "")
                if final_response:
                    OutputFormatter.print_assistant_response(final_response)

        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            OutputFormatter.error(str(e))

def cli():
    """CLI entry point"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
