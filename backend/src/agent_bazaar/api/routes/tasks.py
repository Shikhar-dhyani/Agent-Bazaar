import asyncio
from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel
from agent_bazaar.models.task import Task, TaskStatus
from agent_bazaar.models.subtask import Subtask
from agent_bazaar.models.bid import Bid
from agent_bazaar.graph.marketplace import marketplace_graph
from agent_bazaar.graph.state import MarketplaceState

router = APIRouter()

_tasks: Dict[str, Task] = {}
_task_states: Dict[str, MarketplaceState] = {}
_task_events: Dict[str, List[Dict[str, Any]]] = {}
_task_subscribers: Dict[str, List[asyncio.Queue]] = {}


class CreateTaskRequest(BaseModel):
    request: str


@router.post("", response_model=Task)
async def create_task(body: CreateTaskRequest):
    task = Task(raw_request=body.request)
    _tasks[task.id] = task
    _task_events[task.id] = []
    asyncio.create_task(_run_task(task))
    return task


@router.get("", response_model=List[Task])
async def list_tasks():
    return list(_tasks.values())


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    from fastapi import HTTPException
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/subtasks", response_model=List[Subtask])
async def get_subtasks(task_id: str):
    state = _task_states.get(task_id)
    return state.get("subtasks", []) if state else []


@router.get("/{task_id}/bids")
async def get_bids(task_id: str):
    state = _task_states.get(task_id)
    if not state:
        return {}
    return {
        k: [b.model_dump() for b in v]
        for k, v in state.get("bids", {}).items()
    }


@router.get("/{task_id}/events")
async def get_events(task_id: str):
    return _task_events.get(task_id, [])


async def _run_task(task: Task) -> None:
    initial_state: MarketplaceState = {
        "task": task,
        "subtasks": [],
        "completed_subtask_ids": [],
        "current_subtask_id": None,
        "bids": {},
        "winners": {},
        "execution_results": {},
        "quality_scores": {},
        "final_answer": None,
        "events": [],
        "error": None,
    }

    event_cursor = 0
    try:
        async for state in marketplace_graph.astream(initial_state, stream_mode="values"):
            _task_states[task.id] = state
            _tasks[task.id] = state["task"]

            all_events = state.get("events", [])
            new_events = all_events[event_cursor:]
            event_cursor = len(all_events)

            _task_events[task.id].extend(new_events)
            _broadcast(task.id, new_events)

    except Exception as exc:
        error_event: Dict[str, Any] = {
            "type": "error",
            "task_id": task.id,
            "message": str(exc),
        }
        _task_events.setdefault(task.id, []).append(error_event)
        _broadcast(task.id, [error_event])
        task.status = TaskStatus.FAILED
        _tasks[task.id] = task


def _broadcast(task_id: str, events: List[Dict[str, Any]]) -> None:
    subscribers = _task_subscribers.get(task_id, [])
    for event in events:
        for queue in subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass


def subscribe(task_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=256)
    _task_subscribers.setdefault(task_id, []).append(q)
    return q


def unsubscribe(task_id: str, queue: asyncio.Queue) -> None:
    subscribers = _task_subscribers.get(task_id, [])
    try:
        subscribers.remove(queue)
    except ValueError:
        pass


def get_historical_events(task_id: str) -> List[Dict[str, Any]]:
    return _task_events.get(task_id, [])
