from typing import Any, Optional, List
from datetime import datetime
from ..persistence.manager import PersistenceManager
from .types import StepRecord, ExecutionHistory

class ExecutionTracker:
    def __init__(self, persistence_manager: PersistenceManager):
        self.persistence = persistence_manager

    async def track_step(
        self,
        execution_id: str,
        step_name: str,
        step_index: int,
        status: str,
        result: Optional[Any] = None,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ):
        record = StepRecord(
            execution_id=execution_id,
            step_name=step_name,
            step_index=step_index,
            status=status,
            result=result,
            duration=duration,
            error=error,
            timestamp=datetime.now()
        )
        history_data = await self.persistence.load_history(execution_id)
        
        # A bit complex to deserialize full history here.
        # For now, we'll just append to a list of dicts.
        if history_data:
            history_data.setdefault('steps', []).append(record.__dict__)
        else:
            history_data = ExecutionHistory(execution_id=execution_id, start_time=datetime.now()).__dict__
            history_data['steps'] = [record.__dict__]

        if status == "success":
            history_data['total_duration'] = history_data.get('total_duration', 0) + (duration if duration is not None else 0)
        elif status == "failed":
            history_data['status'] = "failed"
        
        await self.persistence.save_history(execution_id, history_data)

    async def track_error(
        self,
        execution_id: str,
        step_name: str,
        step_index: int,
        error: Exception
    ):
        await self.track_step(
            execution_id=execution_id,
            step_name=step_name,
            step_index=step_index,
            status="failed",
            error=str(error)
        )

    async def get_execution_history(self, execution_id: str) -> Optional[ExecutionHistory]:
        history_data = await self.persistence.load_history(execution_id)
        # This would require a proper from_dict method in ExecutionHistory
        return history_data if history_data else None
