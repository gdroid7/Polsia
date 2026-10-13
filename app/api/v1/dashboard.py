"""Dashboard endpoints — summary, activity feed, daily report."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_api_key
from app.services.activity_service import get_recent_activity
from app.services.company_service import get_full_context
from app.services.report_service import get_daily_report
from app.services.task_service import get_tasks_today_summary

router = APIRouter(prefix="/dashboard", dependencies=[Depends(require_api_key)])


def _row(obj):
    """Convert an ORM row to a JSON-safe dict."""
    return jsonable_encoder(
        {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}
    )


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    summary = await get_tasks_today_summary(db)
    context = await get_full_context(db)
    activities = await get_recent_activity(db, limit=1)
    return {
        "tasks_today_total": summary["total"],
        "tasks_today_pending": summary["pending"],
        "tasks_today_completed": summary["completed"],
        "tasks_today_failed": summary["failed"],
        "kpis": context.get("kpis", {}),
        "last_activity": _row(activities[0]) if activities else None,
    }


@router.get("/activity")
async def get_activity(
    limit: int = Query(default=50),
    db: AsyncSession = Depends(get_db),
):
    activities = await get_recent_activity(db, limit=limit)
    return [_row(a) for a in activities]


@router.get("/reports/daily")
async def get_daily_report_endpoint(db: AsyncSession = Depends(get_db)):
    report = await get_daily_report(db, date.today())
    return _row(report) if report else None
