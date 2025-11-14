from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

@dataclass
class Checkpoint:
    id: str
    execution_id: str
    step_name: str
    step_index: int
    timestamp: datetime
    state: Dict
    context: Dict
    variables: Dict
    status: str = "success"
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "step_name": self.step_name,
            "step_index": self.step_index,
            "timestamp": self.timestamp.isoformat(), # Serialize datetime
            "state": self.state,
            "context": self.context,
            "variables": self.variables,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Checkpoint":
        return cls(
            id=data["id"],
            execution_id=data["execution_id"],
            step_name=data["step_name"],
            step_index=data["step_index"],
            timestamp=datetime.fromisoformat(data["timestamp"]), # Deserialize datetime
            state=data["state"],
            context=data["context"],
            variables=data["variables"],
            status=data.get("status", "success"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )

@dataclass
class StepRecord:
    execution_id: str
    step_name: str
    step_index: int
    status: str
    timestamp: datetime
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: Optional[float] = None

@dataclass
class ExecutionHistory:
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[StepRecord] = field(default_factory=list)
    checkpoints: List[Checkpoint] = field(default_factory=list)
    total_duration: float = 0.0
    status: str = "pending"
    recovery_attempts: int = 0
    last_checkpoint: Optional[Checkpoint] = None

@dataclass
class ExecutionResult:
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
