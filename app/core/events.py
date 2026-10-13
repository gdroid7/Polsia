import json
from app.core.redis_client import get_redis


async def broadcast_activity(payload: dict) -> None:
    redis = await get_redis()
    await redis.publish("polsia:activity", json.dumps(payload))
