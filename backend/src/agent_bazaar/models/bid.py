from datetime import datetime
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Bid(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    subtask_id: str
    agent_id: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    estimated_cost: float = Field(ge=0.0)
    estimated_latency: float = Field(ge=0.0)
    rationale: str
    auction_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
