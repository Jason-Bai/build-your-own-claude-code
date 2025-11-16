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

    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "step_name": self.step_name,
            "step_index": self.step_index,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "result": self.result,
            "error": self.error,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "StepRecord":
        return cls(
            execution_id=data["execution_id"],
            step_name=data["step_name"],
            step_index=data["step_index"],
            status=data["status"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            result=data.get("result"),
            error=data.get("error"),
            duration=data.get("duration"),
        )

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

    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": [s.to_dict() for s in self.steps],
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "total_duration": self.total_duration,
            "status": self.status,
            "recovery_attempts": self.recovery_attempts,
            "last_checkpoint": self.last_checkpoint.to_dict() if self.last_checkpoint else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ExecutionHistory":
        return cls(
            execution_id=data["execution_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            steps=[StepRecord.from_dict(s) for s in data.get("steps", [])],
            checkpoints=[Checkpoint.from_dict(c) for c in data.get("checkpoints", [])],
            total_duration=data.get("total_duration", 0.0),
            status=data.get("status", "pending"),
            recovery_attempts=data.get("recovery_attempts", 0),
            last_checkpoint=Checkpoint.from_dict(data["last_checkpoint"]) if data.get("last_checkpoint") else None,
        )

@dataclass
class ExecutionResult:
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
