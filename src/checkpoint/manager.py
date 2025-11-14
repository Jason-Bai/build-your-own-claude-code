from typing import List, Optional
from datetime import datetime
from ..persistence.manager import PersistenceManager
from .types import Checkpoint

class CheckpointManager:
    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence = persistence_manager

    async def create_checkpoint(
        self,
        execution_id: str,
        step_name: str,
        step_index: int,
        state: dict,
        context: dict,
        variables: dict,
        status: str = "success",
        error: Optional[str] = None
    ) -> Checkpoint:
        checkpoint = Checkpoint(
            id=f"ckpt-{execution_id}-{step_index}",
            execution_id=execution_id,
            step_name=step_name,
            step_index=step_index,
            timestamp=datetime.now(),
            state=state,
            context=context,
            variables=variables,
            status=status,
            error=error
        )
        await self.persistence.save_checkpoint(checkpoint.to_dict())
        return checkpoint

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        data = await self.persistence.load_checkpoint(checkpoint_id)
        return Checkpoint.from_dict(data) if data else None

    async def list_checkpoints(self, execution_id: str) -> List[Checkpoint]:
        checkpoint_ids = await self.persistence.list_checkpoints(execution_id)
        checkpoints = []
        for cp_id in checkpoint_ids:
            cp = await self.load_checkpoint(cp_id)
            if cp: checkpoints.append(cp)
        return sorted(checkpoints, key=lambda x: x.step_index)

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        return await self.persistence.delete_checkpoint(checkpoint_id)

    async def get_last_successful_checkpoint(
        self,
        execution_id: str,
        before_step: Optional[int] = None
    ) -> Optional[Checkpoint]:
        checkpoints = await self.list_checkpoints(execution_id)
        for cp in reversed(checkpoints):
            if cp.status == "success":
                if before_step is None or cp.step_index < before_step:
                    return cp
        return None
