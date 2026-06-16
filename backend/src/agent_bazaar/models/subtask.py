from enum import Enum
from typing import Optional, List
from uuid import uuid4
from pydantic import BaseModel, Field


class Capability(str, Enum):
    WEB_SEARCH = "web_search"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    FACT_CHECKING = "fact_checking"
    TEXT_SYNTHESIS = "text_synthesis"


class SubtaskStatus(str, Enum):
    PENDING = "pending"
    BIDDING = "bidding"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class Subtask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    parent_task_id: str
    description: str
    required_capability: Capability
    dependency_ids: List[str] = Field(default_factory=list)
    status: SubtaskStatus = SubtaskStatus.PENDING
    result: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    quality_score: Optional[float] = None
    order: int = 0
