from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from agent_bazaar.models.task import Task
from agent_bazaar.models.subtask import Subtask
from agent_bazaar.models.bid import Bid


class MarketplaceState(TypedDict):
    task: Task
    subtasks: List[Subtask]
    completed_subtask_ids: List[str]
    current_subtask_id: Optional[str]
    bids: Dict[str, List[Bid]]
    winners: Dict[str, Bid]
    execution_results: Dict[str, str]
    quality_scores: Dict[str, float]
    final_answer: Optional[str]
    events: List[Dict[str, Any]]
    error: Optional[str]
