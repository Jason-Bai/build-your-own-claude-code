"""SessionCommand - Interactively manage sessions"""

from typing import Optional
from .base import Command, CLIContext
from ..cli.interactive import InteractiveListSelector


class SessionCommand(Command):
    """Interactively manage sessions: load, resume, or view session details.

    This command mirrors the /checkpoint command design:
    - Single command with no parameters
    - Interactive list selector for choosing sessions
    - Support for aliases (/sess, /resume)
    """

    @property
    def name(self) -> str:
        return "session"

    @property
    def description(self) -> str:
        return "Interactively manage sessions: load, resume, or view session details."

    @property
    def aliases(self):
        return ["sess", "resume"]

    async def execute(self, args: str, context: CLIContext) -> Optional[str]:
        """
        Interactive session management

        Flow:
        1. Get all available sessions from SessionManager
        2. Display interactive selector with (current) option
        3. User selects a session
        4. Load selected session and sync command history
        5. Return confirmation message

        Args:
            args: Command arguments (unused, but kept for interface compatibility)
            context: CLI context with access to agent

        Returns:
            Status message describing the action taken
        """
        # Check if session manager is available
        if not hasattr(context.agent, 'session_manager'):
            return "Session manager not enabled. Set 'features.session_manager=true' in config."

        session_manager = context.agent.session_manager
        current_session = session_manager.get_current_session()

        # Get all available sessions (use async version)
        all_sessions = await session_manager.list_all_sessions_async()

        if not all_sessions:
            return "No sessions found."

        # Format session list for display
        session_items = []

        # Add "(current)" option at the top
        if current_session:
            current_display = (
                f"(current) Session {current_session.session_id}\n"
                f"  Status: {current_session.status}\n"
                f"  Messages: {len(current_session.conversation_history)}\n"
                f"  Commands: {len(current_session.command_history)}"
            )
            session_items.append(("__current__", current_display))

        # Add all available sessions
        for session_id in all_sessions:
            session_data = session_manager._load_session_sync(session_id)
            if session_data:
                from ..sessions.types import Session
                session = Session.from_dict(session_data)
                display = (
                    f"Session {session.session_id}\n"
                    f"  Status: {session.status}\n"
                    f"  Started: {session.start_time}\n"
                    f"  Messages: {len(session.conversation_history)}\n"
                    f"  Commands: {len(session.command_history)}"
                )
                session_items.append((session_id, display))

        # Create and display interactive selector
        selector = InteractiveListSelector(
            title="Sessions",
            items=session_items
        )

        selected_session_id = await selector.run()

        # Handle selection
        if selected_session_id and selected_session_id != "__current__":
            try:
                # Restore the selected session
                session = session_manager.resume_session(selected_session_id)

                # Sync command history to InputManager
                try:
                    from ..utils import get_input_manager
                    input_manager = get_input_manager()
                    session_manager.sync_command_history_to_input_manager(input_manager)
                except Exception:
                    # Silently fail if input_manager is not available
                    pass

                return (
                    f"✓ Restored session {session.session_id}\n"
                    f"  Status: {session.status}\n"
                    f"  Messages: {len(session.conversation_history)}\n"
                    f"  Commands: {len(session.command_history)}"
                )
            except ValueError as e:
                return f"✗ Failed to load session: {str(e)}"
            except Exception as e:
                return f"✗ Error: {str(e)}"

        return "Exited session selection."
