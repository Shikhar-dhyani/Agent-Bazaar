from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    DECOMPOSING = "decomposing"
    BIDDING = "bidding"
    EXECUTING = "executing"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    raw_request: str
    status: TaskStatus = TaskStatus.PENDING
    final_answer: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
