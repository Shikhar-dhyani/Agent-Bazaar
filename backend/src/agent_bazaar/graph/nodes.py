import asyncio
from datetime import datetime
from typing import Any, Dict, List
from agent_bazaar.graph.state import MarketplaceState
from agent_bazaar.utils.llm_client import complete
from agent_bazaar.utils.cost_tracker import log_usage
from agent_bazaar.models.task import Task, TaskStatus
from agent_bazaar.models.subtask import Subtask, SubtaskStatus
from agent_bazaar.models.bid import Bid
from agent_bazaar.agents.broker import BrokerAgent
from agent_bazaar.agents.scorer import ScorerAgent
from agent_bazaar.agents.base_specialist import BaseSpecialist
from agent_bazaar.agents.registry import get_agents_for_capability, get_registry, update_agent
from agent_bazaar.auction.clearing import clear_auction
from agent_bazaar.auction.reputation import update_reputation
from agent_bazaar.config import settings


def _build_context(subtasks: List[Subtask], results: Dict[str, str], dep_ids: List[str]) -> str:
    parts = []
    for dep_id in dep_ids:
        st = next((s for s in subtasks if s.id == dep_id), None)
        if st and dep_id in results:
            parts.append(f"[{st.description}]\n{results[dep_id]}")
    return "\n\n---\n\n".join(parts) if parts else ""


async def decompose_node(state: MarketplaceState) -> dict:
    task = state["task"]
    task.status = TaskStatus.DECOMPOSING
    broker = BrokerAgent()
    subtasks = await broker.decompose(task)
    return {
        "task": task,
        "subtasks": subtasks,
        "events": state["events"] + [{
            "type": "task_decomposed",
            "task_id": task.id,
            "subtasks": [s.model_dump() for s in subtasks],
        }],
    }


async def select_next_subtask_node(state: MarketplaceState) -> dict:
    completed_ids = set(state["completed_subtask_ids"])
    ready = [
        s for s in state["subtasks"]
        if s.status == SubtaskStatus.PENDING
        and all(dep in completed_ids for dep in s.dependency_ids)
    ]
    ready.sort(key=lambda s: s.order)
    return {"current_subtask_id": ready[0].id if ready else None}


async def collect_bids_node(state: MarketplaceState) -> dict:
    current_id = state["current_subtask_id"]
    subtasks = state["subtasks"]
    subtask = next(s for s in subtasks if s.id == current_id)
    subtask.status = SubtaskStatus.BIDDING

    capability = subtask.required_capability.value
    eligible_agents = get_agents_for_capability(capability)
    context = _build_context(subtasks, state.get("execution_results", {}), subtask.dependency_ids)

    raw_bids = await asyncio.gather(*[
        BaseSpecialist(agent).bid(subtask, context)
        for agent in eligible_agents
    ])

    bid_list = list(raw_bids)
    new_bids = {**state.get("bids", {}), current_id: bid_list}
    bid_events = [{
        "type": "bid_submitted",
        "task_id": state["task"].id,
        "subtask_id": current_id,
        "bid": b.model_dump(),
    } for b in bid_list]

    return {
        "subtasks": subtasks,
        "bids": new_bids,
        "events": state["events"] + bid_events,
    }


async def clear_auction_node(state: MarketplaceState) -> dict:
    current_id = state["current_subtask_id"]
    subtasks = state["subtasks"]
    subtask = next(s for s in subtasks if s.id == current_id)
    bids = state["bids"].get(current_id, [])
    registry = get_registry()
    winner = clear_auction(subtask, bids, registry)

    new_winners = {**state.get("winners", {})}
    if winner:
        new_winners[current_id] = winner
        subtask.status = SubtaskStatus.ASSIGNED
        subtask.assigned_agent_id = winner.agent_id

    return {
        "subtasks": subtasks,
        "winners": new_winners,
        "events": state["events"] + [{
            "type": "auction_cleared",
            "task_id": state["task"].id,
            "subtask_id": current_id,
            "winner": winner.model_dump() if winner else None,
            "all_bids": [b.model_dump() for b in bids],
        }],
    }


async def execute_node(state: MarketplaceState) -> dict:
    current_id = state["current_subtask_id"]
    subtasks = state["subtasks"]
    subtask = next(s for s in subtasks if s.id == current_id)
    winner_bid = state["winners"].get(current_id)
    task = state["task"]

    if not winner_bid:
        subtask.status = SubtaskStatus.FAILED
        return {
            "subtasks": subtasks,
            "events": state["events"] + [{
                "type": "subtask_failed",
                "task_id": task.id,
                "subtask_id": current_id,
                "reason": "No winner selected",
            }],
        }

    subtask.status = SubtaskStatus.EXECUTING
    task.status = TaskStatus.EXECUTING
    registry = get_registry()
    specialist = BaseSpecialist(registry[winner_bid.agent_id])
    context = _build_context(subtasks, state.get("execution_results", {}), subtask.dependency_ids)
    result = await specialist.execute(subtask, context)
    subtask.result = result

    new_results = {**state.get("execution_results", {}), current_id: result}
    return {
        "task": task,
        "subtasks": subtasks,
        "execution_results": new_results,
        "events": state["events"] + [{
            "type": "subtask_executing",
            "task_id": task.id,
            "subtask_id": current_id,
            "agent_id": winner_bid.agent_id,
            "result_preview": result[:300],
        }],
    }


async def score_node(state: MarketplaceState) -> dict:
    current_id = state["current_subtask_id"]
    subtasks = state["subtasks"]
    subtask = next(s for s in subtasks if s.id == current_id)
    result = state["execution_results"].get(current_id, "")
    task = state["task"]
    task.status = TaskStatus.SCORING

    scorer = ScorerAgent()
    quality_score, feedback = await scorer.score(subtask, result)
    subtask.quality_score = quality_score

    new_scores = {**state.get("quality_scores", {}), current_id: quality_score}
    return {
        "task": task,
        "subtasks": subtasks,
        "quality_scores": new_scores,
        "events": state["events"] + [{
            "type": "subtask_scored",
            "task_id": task.id,
            "subtask_id": current_id,
            "quality_score": quality_score,
            "feedback": feedback,
        }],
    }


async def update_reputation_node(state: MarketplaceState) -> dict:
    current_id = state["current_subtask_id"]
    subtasks = state["subtasks"]
    subtask = next(s for s in subtasks if s.id == current_id)
    winner_bid = state["winners"].get(current_id)
    quality_score = state["quality_scores"].get(current_id, 0.5)

    events = list(state["events"])
    if winner_bid:
        registry = get_registry()
        agent = registry[winner_bid.agent_id]
        capability = subtask.required_capability.value
        updated_agent, old_rep, new_rep = update_reputation(agent, capability, quality_score)
        update_agent(updated_agent)
        subtask.status = SubtaskStatus.COMPLETED

        events.append({
            "type": "reputation_updated",
            "task_id": state["task"].id,
            "agent_id": winner_bid.agent_id,
            "capability": capability,
            "old_reputation": old_rep,
            "new_reputation": new_rep,
            "quality_score": quality_score,
        })

    completed = list(state["completed_subtask_ids"]) + [current_id]
    return {
        "subtasks": subtasks,
        "completed_subtask_ids": completed,
        "events": events,
    }


async def aggregate_node(state: MarketplaceState) -> dict:
    subtasks = state["subtasks"]
    results = state.get("execution_results", {})
    task = state["task"]

    parts = []
    for st in sorted(subtasks, key=lambda s: s.order):
        if st.id in results:
            parts.append(f"### {st.description}\n{results[st.id]}")

    combined = "\n\n".join(parts)
    final_answer, response = await complete(
        settings.aggregator_model,
        "You are an aggregation agent. Synthesize the results of multiple completed subtasks into a single coherent, well-structured final answer. Do not just concatenate — synthesize.",
        f"Original request: {task.raw_request}\n\nSubtask results:\n{combined}\n\nProvide a comprehensive final answer.",
        max_tokens=4096,
    )
    log_usage(settings.aggregator_model, response, "aggregate/synthesize")
    task.final_answer = final_answer
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()

    return {
        "task": task,
        "final_answer": final_answer,
        "events": state["events"] + [{
            "type": "task_completed",
            "task_id": task.id,
            "final_answer": final_answer,
        }],
    }


def route_after_select(state: MarketplaceState) -> str:
    return "collect_bids" if state["current_subtask_id"] is not None else "aggregate"
