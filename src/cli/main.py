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
from .exceptions import SessionPausedException
from .ui_coordinator import init_coordinator
from .monitor import GlobalKeyboardMonitor
from ..logging import get_action_logger
from ..logging.types import ActionType


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
    
    # Setup Event Bus and UI Coordinator
    event_bus = get_event_bus()
    await _setup_event_listeners(event_bus)

    # ✨ Initialize UI Coordinator (replaces直接 InterfaceManager)
    # This handles mode switching between REACTIVE and INTERACTIVE
    coordinator = init_coordinator(
        event_bus,
        OutputFormatter.console,
        enable_reactive_ui=True  # Set to False to disable Live Display
    )

    # Register all built-in commands
    register_builtin_commands()

    # Create CLI context
    cli_context = CLIContext(agent, config=config)

    # Load project context from CLAUDE.md if present
    claude_md_path = Path.cwd() / "CLAUDE.md"
    if claude_md_path.exists():
        try:
            with open(claude_md_path, 'r', encoding='utf-8') as f:
                claude_md_info = f.read()
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

    # P11: Set session_manager in action_logger for automatic session_id resolution
    action_logger = get_action_logger()
    action_logger.set_session_manager(session_manager)

    # P12: Initialize GlobalKeyboardMonitor for ESC cancellation
    # Note: require_window_focus=False allows ESC to work even when terminal not focused
    # This is useful during development/debugging. Set to True for stricter behavior.
    keyboard_monitor = None
    esc_monitoring_enabled = False

    try:
        keyboard_monitor = GlobalKeyboardMonitor(
            session_manager,
            input_manager,
            require_window_focus=False  # Disabled by default for easier testing
        )
        keyboard_monitor.start()
        esc_monitoring_enabled = True
        # Success - no message needed, feature works silently
    except PermissionError:
        # Explicitly disable monitoring
        keyboard_monitor = None
        OutputFormatter.warning(
            "⚠️  ESC Cancellation Unavailable\n"
            "\n"
            "   Reason: macOS Accessibility permissions not granted\n"
            "   Impact: You cannot interrupt operations by pressing ESC\n"
            "\n"
            "   💡 Alternative: Use Ctrl+C to interrupt operations\n"
            "\n"
            "   To enable ESC cancellation:\n"
            "   1. Open System Settings (System Preferences on older macOS)\n"
            "   2. Go to: Privacy & Security → Accessibility\n"
            "   3. Click the lock icon and authenticate\n"
            "   4. Add your terminal app to the list:\n"
            "      - Terminal.app (built-in)\n"
            "      - iTerm2\n"
            "      - VS Code\n"
            "      - Or your current terminal emulator\n"
            "   5. Restart this CLI\n"
            "\n"
            "   For diagnostics: Type '/check-permissions'\n"
        )
    except Exception as e:
        keyboard_monitor = None
        OutputFormatter.warning(
            f"⚠️  ESC Cancellation Unavailable: {e}\n"
            f"   💡 Alternative: Use Ctrl+C to interrupt operations\n"
            f"   Type '/check-permissions' for diagnostic information\n"
        )

    # Display Welcome Message
    if OutputFormatter.level != OutputLevel.QUIET:
        OutputFormatter.display_welcome_message(session.session_id)

    # Sync existing command history to session (if any)
    if input_manager.history:
        try:
            existing_commands = list(input_manager.history.get_strings())
            for cmd in existing_commands:
                session_manager.record_command(cmd)
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

                # 检查是否是session暂停标记
                if user_input == "__SESSION_PAUSED__":
                    # 清除exit()后多余的"You: "提示（向上移动一行并清除）
                    print('\033[F\033[K', end='', flush=True)

                    # 暂停当前session（使用async版本）
                    await session_manager.pause_session_async(reason="user_input_paused")
                    continue

                if not user_input:
                    continue

                # P11: Get logger for action logging
                action_logger = get_action_logger()

                # Check if it's a command
                if command_registry.is_command(user_input):
                    session_manager.record_command(user_input)

                    # P11: Log user command
                    action_logger.log(
                        action_type=ActionType.USER_COMMAND,
                        session_id=session.session_id,
                        command=user_input
                    )

                    result = await command_registry.execute(user_input, cli_context)
                    if result:
                        OutputFormatter.print_assistant_response(result)
                    continue

                # Record user input in session
                session_manager.record_command(user_input)

                # P11: Log user input
                action_logger.log(
                    action_type=ActionType.USER_INPUT,
                    session_id=session.session_id,
                    content=user_input
                )

                # P12: Start new execution (creates fresh cancellation token)
                session_manager.start_new_execution()

                # Otherwise, send to agent
                # Note: UI Manager handles the "Thinking..." and tool execution visualization
                # We disable verbose output in agent.run to avoid duplicate printing
                result = await agent.run(
                    user_input,
                    verbose=False,
                    cancellation_token=session_manager.cancellation_token
                )

                if isinstance(result, dict):
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
            except asyncio.CancelledError:
                # P12: Handle ESC cancellation
                OutputFormatter.warning("\n⚠️  Execution cancelled by user (ESC pressed)")

                # Log the cancellation
                action_logger.log(
                    action_type=ActionType.EXECUTION_CANCELLED,
                    session_id=session.session_id,
                    reason="User pressed ESC"
                )

                # Pause session
                await session_manager.pause_session_async(reason="execution_cancelled")
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
        # Clean up on abnormal exit (EOFError, exceptions)
        # Note: Normal exit via /exit command handles cleanup in ExitCommand
        from ..logging.constants import DEFAULT_BATCH_TIMEOUT
        import time

        # P12: Stop GlobalKeyboardMonitor
        if keyboard_monitor is not None:
            keyboard_monitor.stop()

        # Check if session still exists - if so, this is an abnormal exit
        if session_manager.current_session:
            try:
                await session_manager.end_session_async()
            except Exception as e:
                OutputFormatter.warning(f"Failed to save session: {e}")

            # Wait for worker thread to process logs
            wait_time = DEFAULT_BATCH_TIMEOUT + 0.5
            time.sleep(wait_time)

            # Shutdown logger (stops worker, flushes queue, closes files)
            action_logger.shutdown()

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
