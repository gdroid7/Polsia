"""Agent trigger and status endpoints."""
from datetime import date, datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_api_key
from app.models.task import AgentRun
from app.services.task_service import create_task

router = APIRouter(prefix="/agents", dependencies=[Depends(require_api_key)])

VALID_AGENT_TYPES = [
    "orchestrator",
    "social_media",
    "competitor_research",
    "business_planning",
    "email_outreach",
    "customer_support",
    "ads_management",
    "code_generation",
    "finance",
]


def _row(obj):
    """Convert an ORM row to a JSON-safe dict."""
    return jsonable_encoder(
        {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}
    )


@router.post("/{agent_type}/trigger", status_code=202)
async def trigger_agent(
    agent_type: str,
    body: dict = Body(default={}),
    db: AsyncSession = Depends(get_db),
):
    if agent_type not in VALID_AGENT_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid agent type: {agent_type}")

    task_title = body.get("task_title") or f"Manual trigger: {agent_type}"
    task = await create_task(db, title=task_title, agent_type=agent_type, source="api")
    await db.flush()

    from celery_app.tasks.agent_tasks import run_agent_task  # noqa: PLC0415
    run_agent_task.delay(task.id)

    return {"status": "queued", "task_id": task.id}


@router.get("/status")
async def get_agent_status(db: AsyncSession = Depends(get_db)):
    today_start = datetime.combine(date.today(), datetime.min.time())
    result = []

    for agent_type in VALID_AGENT_TYPES:
        last_run_result = await db.execute(
            select(AgentRun)
            .where(AgentRun.agent_type == agent_type)
            .order_by(AgentRun.started_at.desc())
            .limit(1)
        )
        last = last_run_result.scalar_one_or_none()

        count_result = await db.execute(
            select(func.count(AgentRun.id)).where(
                AgentRun.agent_type == agent_type,
                AgentRun.started_at >= today_start,
            )
        )
        runs_today = count_result.scalar() or 0

        result.append(
            {
                "agent_type": agent_type,
                "last_run_at": last.started_at.isoformat() if last else None,
                "last_status": last.status if last else None,
                "runs_today": runs_today,
            }
        )

    return result
