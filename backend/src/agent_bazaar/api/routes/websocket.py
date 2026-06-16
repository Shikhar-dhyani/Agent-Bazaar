import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from agent_bazaar.api.routes.tasks import (
    subscribe,
    unsubscribe,
    get_historical_events,
    _task_states,
)

router = APIRouter()


@router.websocket("/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()

    # Snapshot then replay — avoids sending events twice if _run_task appends
    # to the list while we're still iterating it (await yields the event loop).
    for event in list(get_historical_events(task_id)):
        try:
            await websocket.send_json(event)
        except Exception:
            return

    # If task already finished, nothing more to stream
    state = _task_states.get(task_id)
    if state and state["task"].status in ("completed", "failed"):
        return

    queue = subscribe(task_id)
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event)
                if event.get("type") in ("task_completed", "error"):
                    break
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe(task_id, queue)
