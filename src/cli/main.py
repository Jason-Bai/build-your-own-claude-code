import asyncio
import sys
from datetime import datetime
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
        tools_count=len(agent.tool_manager.tools) if hasattr(
            agent, 'tool_manager') else 0,
    )

    # Load project context from CLAUDE.md if present
    if claude_md_info:
        try:
            agent.context_manager.set_system_prompt(
                f"[System: Project Context]\n\n{claude_md_info}"
            )
        except Exception as e:
            OutputFormatter.warning(f"Failed to load CLAUDE.md: {e}")

    # Initialize input manager with command registry (dependency injection)
    input_manager = get_input_manager()

    # Initialize SessionManager (now always enabled for production)
    session_manager = agent.session_manager
    project_name = Path.cwd().name
    session = session_manager.start_session(project_name)
    OutputFormatter.info(f"📝 Session started: {session.session_id}")

    # Sync existing command history to session (if any)
    if input_manager.history:
        try:
            existing_commands = list(input_manager.history.get_strings())
            for cmd in existing_commands:
                session_manager.record_command(cmd)
            if existing_commands:
                OutputFormatter.info(
                    f"📚 Loaded {len(existing_commands)} existing commands")
        except Exception:
            pass

    # Main REPL loop
    is_first_iteration = True
    try:
        while True:
            try:
                # Print separator (but not on first iteration)
                if not is_first_iteration:
                    OutputFormatter.print_separator()
                is_first_iteration = False

                user_input = await input_manager.async_get_input()
                if not user_input:
                    continue

                # Check if it's a command
                if command_registry.is_command(user_input):
                    session_manager.record_command(user_input)
                    result = await command_registry.execute(user_input, cli_context)
                    if result:
                        OutputFormatter.print_assistant_response(result)
                    continue

                # Record user input in session
                session_manager.record_command(user_input)

                # Otherwise, send to agent
                OutputFormatter.print_separator()
                OutputFormatter.print_assistant_response_header()
                result = await agent.run(user_input, verbose=True)

                if isinstance(result, dict):
                    # Show feedback messages
                    feedback_messages = result.get("feedback", [])
                    for feedback_msg in feedback_messages:
                        OutputFormatter.info(feedback_msg)

                    final_response = result.get("final_response", "")
                    if final_response:
                        OutputFormatter.print_assistant_response(
                            final_response)

                    # Record conversation in session and save
                    session_manager.record_message({
                        "role": "user",
                        "content": user_input,
                        "timestamp": datetime.now().isoformat()
                    })
                    session_manager.record_message({
                        "role": "assistant",
                        "content": final_response,
                        "timestamp": datetime.now().isoformat()
                    })
                    # Save session after each interaction
                    await session_manager.save_session_async()

            except KeyboardInterrupt:
                OutputFormatter.info("Use /exit to quit properly")
                continue
            except EOFError:
                OutputFormatter.success("Goodbye!")
                break
            except Exception as e:
                OutputFormatter.error(str(e))
                import traceback
                traceback.print_exc()
                OutputFormatter.info("Type /clear to reset if needed")

    finally:
        # End session (always enabled in production)
        try:
            session_manager.end_session()
            OutputFormatter.info("📝 Session saved and closed")
        except Exception as e:
            OutputFormatter.warning(f"Failed to save session: {e}")

        # Clean up MCP connections
        if agent.mcp_client:
            OutputFormatter.info("Disconnecting MCP servers...")
            await agent.mcp_client.disconnect_all()


def cli():
    """CLI entry point"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
