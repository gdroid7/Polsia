"""Task and AgentRun CRUD operations."""
from datetime import date, datetime, time

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import AgentRun, Task


async def create_task(
    db: AsyncSession,
    title: str,
    agent_type: str,
    description: str | None = None,
    priority: int = 3,
    source: str = "orchestrator",
) -> Task:
    task = Task(
        title=title,
        agent_type=agent_type,
        description=description,
        priority=priority,
        source=source,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: int) -> Task | None:
    return await db.get(Task, task_id)


async def list_tasks(
    db: AsyncSession,
    status: str | None = None,
    agent_type: str | None = None,
    limit: int = 50,
) -> list[Task]:
    stmt = select(Task)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    if agent_type is not None:
        stmt = stmt.where(Task.agent_type == agent_type)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_task_status(
    db: AsyncSession,
    task_id: int,
    status: str,
    result_summary: str | None = None,
    error_message: str | None = None,
) -> Task | None:
    task = await get_task(db, task_id)
    if task is None:
        return None
    task.status = status
    if result_summary is not None:
        task.result_summary = result_summary
    if error_message is not None:
        task.error_message = error_message
    await db.flush()
    await db.refresh(task)
    return task


async def create_agent_run(
    db: AsyncSession,
    agent_type: str,
    task_id: int | None = None,
    input_context: dict | None = None,
) -> AgentRun:
    run = AgentRun(
        agent_type=agent_type,
        task_id=task_id,
        input_context=input_context,
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def finish_agent_run(
    db: AsyncSession,
    run_id: int,
    status: str,
    output: dict | None = None,
    duration_secs: float | None = None,
) -> AgentRun:
    run = await db.get(AgentRun, run_id)
    run.status = status
    run.output = output
    run.duration_secs = duration_secs
    run.ended_at = datetime.utcnow()
    await db.flush()
    await db.refresh(run)
    return run


async def get_tasks_today_summary(db: AsyncSession) -> dict:
    today_start = datetime.combine(date.today(), time.min)

    stmt = select(Task.status, func.count(Task.id)).where(
        Task.created_at >= today_start
    ).group_by(Task.status)
    result = await db.execute(stmt)
    rows = result.all()

    counts = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
    total = 0
    for row_status, count in rows:
        if row_status in counts:
            counts[row_status] = count
        total += count

    return {
        "total": total,
        "pending": counts["pending"],
        "in_progress": counts["in_progress"],
        "completed": counts["completed"],
        "failed": counts["failed"],
    }
