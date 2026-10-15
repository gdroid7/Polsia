"""Activity logging service — writes to DB and broadcasts via Redis."""
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.redis_client as _redis_module
from app.models.activity import ActivityLog


async def log_activity(
    db: AsyncSession,
    agent_type: str,
    action: str,
    summary: str,
    level: str = "info",
    detail: dict | None = None,
) -> ActivityLog:
    entry = ActivityLog(
        agent_type=agent_type,
        action=action,
        summary=summary,
        level=level,
        detail=detail,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)

    redis = await _redis_module.get_redis()
    await redis.publish(
        "polsia:activity",
        json.dumps(
            {
                "agent_type": agent_type,
                "action": action,
                "summary": summary,
                "level": level,
            }
        ),
    )
    return entry


async def get_recent_activity(db: AsyncSession, limit: int = 50) -> list[ActivityLog]:
    stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
