from typing import Dict, Any, Optional, List
from .storage import BaseStorage

class PersistenceManager:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    async def save_checkpoint(self, checkpoint_data: Dict) -> str:
        return await self.storage.save(category="checkpoint", key=checkpoint_data["id"], data=checkpoint_data)

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict]:
        return await self.storage.load("checkpoint", checkpoint_id)

    async def list_checkpoints(self, execution_id: str) -> List[str]:
        all_checkpoints = await self.storage.list("checkpoint")
        return [cp for cp in all_checkpoints if cp.startswith(f"ckpt-{execution_id}")]

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        return await self.storage.delete("checkpoint", checkpoint_id)

    async def save_conversation(self, conv_id: str, conversation: Dict) -> str:
        return await self.storage.save(category="conversation", key=conv_id, data=conversation)

    async def load_conversation(self, conv_id: str) -> Optional[Dict]:
        return await self.storage.load("conversation", conv_id)

    async def list_conversations(self) -> List[str]:
        return await self.storage.list("conversation")

    async def delete_conversation(self, conv_id: str) -> bool:
        return await self.storage.delete("conversation", conv_id)

    async def save_history(self, execution_id: str, history: Dict) -> str:
        return await self.storage.save(category="history", key=execution_id, data=history)

    async def load_history(self, execution_id: str) -> Optional[Dict]:
        return await self.storage.load("history", execution_id)

    async def save_config(self, config_name: str, config: Dict) -> str:
        return await self.storage.save(category="config", key=config_name, data=config)

    async def load_config(self, config_name: str) -> Optional[Dict]:
        return await self.storage.load("config", config_name)

    async def save_agent_state(self, agent_id: str, state: Dict) -> str:
        return await self.storage.save(category="agent_state", key=agent_id, data=state)

    async def load_agent_state(self, agent_id: str) -> Optional[Dict]:
        return await self.storage.load("agent_state", agent_id)

    # ========== Session Management APIs ==========

    async def save_session(self, session_id: str, session_data: Dict) -> str:
        """Save a session to persistent storage"""
        return await self.storage.save(category="session", key=session_id, data=session_data)

    async def load_session(self, session_id: str) -> Optional[Dict]:
        """Load a session from persistent storage"""
        return await self.storage.load("session", session_id)

    async def list_sessions(self) -> List[str]:
        """List all session IDs"""
        return await self.storage.list("session")

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session from persistent storage"""
        return await self.storage.delete("session", session_id)

