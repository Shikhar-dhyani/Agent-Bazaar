from enum import Enum
from typing import Dict, List
from pydantic import BaseModel, Field


class AgentTier(str, Enum):
    FAST = "fast"
    THOROUGH = "thorough"


class AgentProfile(BaseModel):
    id: str
    name: str
    tier: AgentTier
    capabilities: List[str]
    reputation: Dict[str, float] = Field(default_factory=dict)
    base_cost: float
    base_latency: float
    model: str
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
