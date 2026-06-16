from typing import Dict, List, Optional
from agent_bazaar.models.bid import Bid
from agent_bazaar.models.agent_profile import AgentProfile
from agent_bazaar.models.subtask import Subtask

CONFIDENCE_WEIGHT = 0.40
COST_WEIGHT = 0.30
REPUTATION_WEIGHT = 0.30


def compute_bid_score(bid: Bid, agent: AgentProfile, capability: str) -> float:
    reputation = agent.reputation.get(capability, 0.5)
    # Sigmoid-like cost normalization: higher cost → lower score
    cost_score = 1.0 / (1.0 + bid.estimated_cost / 10.0)
    return (
        CONFIDENCE_WEIGHT * bid.confidence_score
        + COST_WEIGHT * cost_score
        + REPUTATION_WEIGHT * reputation
    )


def clear_auction(
    subtask: Subtask,
    bids: List[Bid],
    agents: Dict[str, AgentProfile],
    min_confidence: float = 0.3,
) -> Optional[Bid]:
    eligible = [b for b in bids if b.confidence_score >= min_confidence]
    if not eligible:
        eligible = bids
    if not eligible:
        return None

    scored: List[tuple[Bid, float]] = []
    for bid in eligible:
        agent = agents.get(bid.agent_id)
        if agent is None:
            continue
        score = compute_bid_score(bid, agent, subtask.required_capability.value)
        bid.auction_score = round(score, 4)
        scored.append((bid, score))

    scored.sort(key=lambda x: (-x[1], x[0].estimated_latency))
    return scored[0][0] if scored else None
