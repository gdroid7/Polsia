"""Company context and prompt building."""
from datetime import date, datetime, time, timedelta

from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyConfig
from app.models.reports import DailyReport
from app.models.task import Task


async def get_full_context(db: AsyncSession) -> dict:
    result = await db.execute(select(CompanyConfig).limit(1))
    company = result.scalar_one_or_none()
    if company is None:
        return {}

    yesterday = date.today() - timedelta(days=1)
    report_result = await db.execute(
        select(DailyReport).where(DailyReport.report_date == yesterday)
    )
    report = report_result.scalar_one_or_none()
    yesterday_summary = report.evening_summary if report else None

    today_start = datetime.combine(date.today(), time.min)
    tasks_result = await db.execute(
        select(Task).where(Task.created_at >= today_start).limit(20)
    )
    tasks = list(tasks_result.scalars().all())

    company_dict = {
        col.key: getattr(company, col.key)
        for col in sa_inspect(company.__class__).mapper.column_attrs
    }

    return {
        "company": company_dict,
        "kpis": company.kpis or {},
        "yesterday_summary": yesterday_summary,
        "todays_tasks": [
            {"title": t.title, "agent_type": t.agent_type, "status": t.status}
            for t in tasks
        ],
    }


def build_context_prompt(context: dict) -> str:
    if not context:
        return "No company context available."

    company = context.get("company", {})
    kpis = context.get("kpis", {})
    yesterday_summary = context.get("yesterday_summary")
    todays_tasks = context.get("todays_tasks", [])

    lines = [
        f"Company: {company.get('name', 'Unknown')}",
        f"Mission: {company.get('mission', '')}",
        "",
        "KPIs:",
    ]

    for key, val in kpis.items():
        lines.append(f"  {key}: {val}")

    if yesterday_summary:
        lines.append("")
        lines.append(f"Yesterday: {yesterday_summary}")

    if todays_tasks:
        lines.append("")
        lines.append("Today's tasks:")
        for t in todays_tasks:
            lines.append(f"  - {t['title']} ({t['agent_type']}) [{t['status']}]")

    return "\n".join(lines)
