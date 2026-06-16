from fastapi import APIRouter, HTTPException
from agent_bazaar.agents.registry import get_registry, get_agent

router = APIRouter()


@router.get("")
async def list_agents():
    return list(get_registry().values())


@router.get("/{agent_id}")
async def get_agent_by_id(agent_id: str):
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
