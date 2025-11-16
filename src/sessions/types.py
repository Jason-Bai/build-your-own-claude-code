"""Session data model - Core data structure for session management"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

from ..checkpoint.types import ExecutionHistory


@dataclass
class Session:
    """Represents a complete user interaction session"""

    session_id: str
    project_name: str
    start_time: datetime

    # Session state
    status: str = "active"  # active, paused, completed
    end_time: Optional[datetime] = None

    # Aggregated history records
    conversation_history: List[Dict] = field(default_factory=list)
    command_history: List[str] = field(default_factory=list)
    execution_histories: List[ExecutionHistory] = field(default_factory=list)

    # Metadata
    metadata: Dict = field(default_factory=dict)

    # ========== Convenience Methods ==========

    def to_dict(self) -> Dict:
        """Serialize session to dictionary"""
        return {
            "session_id": self.session_id,
            "project_name": self.project_name,
            "start_time": self.start_time.isoformat(),
            "status": self.status,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "conversation_history": self.conversation_history,
            "command_history": self.command_history,
            "execution_histories": [eh.to_dict() for eh in self.execution_histories],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Session":
        """Deserialize session from dictionary"""
        return cls(
            session_id=data["session_id"],
            project_name=data["project_name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            status=data.get("status", "active"),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            conversation_history=data.get("conversation_history", []),
            command_history=data.get("command_history", []),
            execution_histories=[
                ExecutionHistory.from_dict(eh) for eh in data.get("execution_histories", [])
            ],
            metadata=data.get("metadata", {}),
        )

    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == "active"

    def is_completed(self) -> bool:
        """Check if session is completed"""
        return self.status == "completed"

    def is_paused(self) -> bool:
        """Check if session is paused"""
        return self.status == "paused"
