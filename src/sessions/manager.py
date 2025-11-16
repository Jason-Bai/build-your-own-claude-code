"""SessionManager - Manages session lifecycle and state"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict

from .types import Session
from ..persistence.manager import PersistenceManager


class SessionManager:
    """Manages session creation, loading, saving, and state transitions"""

    def __init__(self, persistence_manager: PersistenceManager):
        """Initialize SessionManager with persistence backend"""
        self.persistence = persistence_manager
        self.current_session: Optional[Session] = None

    # ========== Session Lifecycle Methods ==========

    def start_session(self, project_name: str, session_id: Optional[str] = None) -> Session:
        """Start a new session or load an existing one"""
        if session_id:
            # Try to load existing session
            session_data = self._load_session_sync(session_id)
            if session_data:
                self.current_session = Session.from_dict(session_data)
                self.current_session.status = "active"
                return self.current_session

        # Create new session
        self.current_session = Session(
            session_id=f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            project_name=project_name,
            start_time=datetime.now()
        )
        return self.current_session

    def end_session(self) -> None:
        """End current session"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.status = "completed"
            self._save_session_sync()
            self.current_session = None

    def pause_session(self) -> None:
        """Pause current session"""
        if self.current_session:
            self.current_session.status = "paused"
            self._save_session_sync()

    def resume_session(self, session_id: str) -> Session:
        """Resume a paused session"""
        session_data = self._load_session_sync(session_id)
        if session_data:
            self.current_session = Session.from_dict(session_data)
            self.current_session.status = "active"
            return self.current_session
        else:
            raise ValueError(f"Session not found: {session_id}")

    # ========== Data Recording Methods ==========

    def record_message(self, message: Dict) -> None:
        """Record a conversation message"""
        if self.current_session:
            self.current_session.conversation_history.append(message)

    def record_command(self, command: str) -> None:
        """Record a command"""
        if self.current_session:
            self.current_session.command_history.append(command)

    def add_execution_history(self, execution_history) -> None:
        """Add an execution history"""
        if self.current_session:
            self.current_session.execution_histories.append(execution_history)

    # ========== Command History Synchronization ==========

    def sync_command_history_to_input_manager(self, input_manager) -> None:
        """
        Load command history from Session to InputManager
        Call this when loading a session
        """
        if self.current_session and hasattr(input_manager, 'history'):
            # Clear InputManager's history
            if hasattr(input_manager.history, '_strings'):
                input_manager.history._strings.clear()

            # Add commands one by one
            for cmd in self.current_session.command_history:
                if hasattr(input_manager.history, 'append_string'):
                    input_manager.history.append_string(cmd)

    def sync_command_history_from_input_manager(self, input_manager) -> None:
        """
        Extract command history from InputManager to Session
        Call this when saving a session
        """
        if self.current_session and hasattr(input_manager, 'history'):
            # Extract all commands
            if hasattr(input_manager.history, 'get_strings'):
                commands = list(input_manager.history.get_strings())
                self.current_session.command_history = commands

    # ========== Query Methods ==========

    def get_current_session(self) -> Optional[Session]:
        """Get current session"""
        return self.current_session

    def list_all_sessions(self) -> List[str]:
        """List all session IDs"""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                return loop.run_until_complete(self.persistence.list_sessions())
        except RuntimeError:
            pass
        return []

    # ========== Persistence Methods ==========

    def _save_session_sync(self) -> None:
        """Synchronously save current session"""
        if self.current_session:
            try:
                asyncio.run(
                    self.persistence.save_session(
                        self.current_session.session_id,
                        self.current_session.to_dict()
                    )
                )
            except RuntimeError:
                pass

    def _load_session_sync(self, session_id: str) -> Optional[Dict]:
        """Synchronously load session"""
        try:
            return asyncio.run(
                self.persistence.load_session(session_id)
            )
        except RuntimeError:
            return None

    async def save_session_async(self) -> None:
        """Asynchronously save current session"""
        if self.current_session:
            await self.persistence.save_session(
                self.current_session.session_id,
                self.current_session.to_dict()
            )

    async def load_session_async(self, session_id: str) -> Optional[Session]:
        """Asynchronously load session"""
        session_data = await self.persistence.load_session(session_id)
        if session_data:
            return Session.from_dict(session_data)
        return None
