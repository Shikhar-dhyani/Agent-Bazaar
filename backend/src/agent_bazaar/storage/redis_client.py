import json
from typing import Any, Optional
import redis.asyncio as redis
from agent_bazaar.config import settings

_redis: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    global _redis
    if _redis is None and settings.redis_url:
        try:
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
            await _redis.ping()
        except Exception:
            _redis = None
    return _redis


async def publish_event(channel: str, event: dict[str, Any]) -> bool:
    r = await get_redis()
    if r is None:
        return False
    try:
        await r.publish(channel, json.dumps(event, default=str))
        return True
    except Exception:
        return False
