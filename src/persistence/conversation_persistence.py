import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .manager import PersistenceManager
from .storage import JSONStorage, SQLiteStorage, BaseStorage

class ConversationPersistence:
    """
    Handles saving and loading of conversation history.
    This class is now a wrapper around the new PersistenceManager
    to maintain backward compatibility with existing commands.
    """
    def __init__(self, persistence_manager: Optional[PersistenceManager] = None):
        if persistence_manager:
            self.manager = persistence_manager
        else:
            self.manager = PersistenceManager(self._get_configured_storage())

    def _get_configured_storage(self) -> BaseStorage:
        project_name = Path.cwd().name
        # This is a fallback. The primary mechanism should be the one
        # initialized in main.py and passed to the agent.
        return JSONStorage(project_name)

    def auto_save_id(self) -> str:
        """Generates a unique ID for auto-saved conversations."""
        # Using a simpler ID now that it's project-specific via directory structure
        return f"conv-auto-save-{os.getpid()}"

    async def save_conversation(
        self,
        conv_id: str,
        messages: List[Dict],
        system_prompt: Optional[str],
        summary: Optional[str],
        metadata: Dict
    ) -> str:
        """Saves a conversation using the PersistenceManager."""
        conversation_data = {
            "messages": messages,
            "system_prompt": system_prompt,
            "summary": summary,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        return await self.manager.save_conversation(conv_id, conversation_data)

    async def load_conversation(self, conv_id: str) -> Optional[Dict]:
        """Loads a conversation using the PersistenceManager."""
        return await self.manager.load_conversation(conv_id)

    async def list_conversations(self) -> List[str]:
        """Lists all conversations using the PersistenceManager."""
        return await self.manager.list_conversations()

    async def delete_conversation(self, conv_id: str) -> bool:
        """Deletes a conversation using the PersistenceManager."""
        return await self.manager.delete_conversation(conv_id)