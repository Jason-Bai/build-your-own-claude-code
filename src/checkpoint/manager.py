from typing import List, Optional, Tuple
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

    async def get_formatted_checkpoint_history(self) -> List[Tuple[str, str]]:
        """
        获取格式化为交互式选择器的检查点历史记录。
        返回格式: [(execution_id, display_text), ...]
        """
        # 获取所有检查点
        try:
            checkpoint_ids = await self.persistence.storage.list("checkpoint")
            if not checkpoint_ids:
                return []

            # 按 execution_id 分组
            checkpoints_by_exec = {}
            for cp_id in checkpoint_ids:
                data = await self.persistence.load_checkpoint(cp_id)
                if data:
                    cp = Checkpoint.from_dict(data)
                    exec_id = cp.execution_id
                    if exec_id not in checkpoints_by_exec:
                        checkpoints_by_exec[exec_id] = []
                    checkpoints_by_exec[exec_id].append(cp)

            # 为每个 execution 创建显示项
            formatted_items = []
            for exec_id in sorted(checkpoints_by_exec.keys(), reverse=True):
                checkpoints = checkpoints_by_exec[exec_id]
                # 获取最后一个检查点的信息
                last_cp = checkpoints[-1] if checkpoints else None
                if last_cp:
                    display_text = f"Restore {exec_id}\n  Step: {last_cp.step_name}"
                    formatted_items.append((exec_id, display_text))

            return formatted_items
        except:
            # 如果出错，返回空列表而不是崩溃
            return []
