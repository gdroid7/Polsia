"""Task CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_api_key
from app.services.task_service import create_task, get_task, list_tasks

router = APIRouter(prefix="/tasks", dependencies=[Depends(require_api_key)])


def _row(obj):
    """Convert an ORM row to a JSON-safe dict."""
    return jsonable_encoder(
        {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}
    )


class TaskCreate(BaseModel):
    title: str
    agent_type: str
    description: str | None = None
    priority: int = 3


@router.get("")
async def list_tasks_endpoint(
    status: str | None = Query(default=None),
    agent_type: str | None = Query(default=None),
    limit: int = Query(default=50),
    db: AsyncSession = Depends(get_db),
):
    tasks = await list_tasks(db, status=status, agent_type=agent_type, limit=limit)
    return [_row(t) for t in tasks]


@router.post("", status_code=201)
async def create_task_endpoint(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = await create_task(
        db,
        title=body.title,
        agent_type=body.agent_type,
        description=body.description,
        priority=body.priority,
    )
    return _row(task)


@router.get("/{task_id}")
async def get_task_endpoint(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _row(task)
