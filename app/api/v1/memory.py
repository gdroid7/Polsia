"""Memory store endpoints — create and search/list memories."""
from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_api_key
from app.services.memory_service import list_memories, search_memory, store_memory

router = APIRouter(prefix="/memory", dependencies=[Depends(require_api_key)])


def _row(obj):
    """Convert an ORM row to a JSON-safe dict."""
    return jsonable_encoder(
        {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}
    )


class MemoryCreate(BaseModel):
    category: str
    title: str
    content: str
    tags: list[str] = []


@router.post("", status_code=201)
async def create_memory(body: MemoryCreate, db: AsyncSession = Depends(get_db)):
    entry = await store_memory(
        db,
        category=body.category,
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    return _row(entry)


@router.get("")
async def get_memories(
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=50),
    db: AsyncSession = Depends(get_db),
):
    if q:
        return await search_memory(db, q, n_results=limit)
    entries = await list_memories(db, category=category, limit=limit)
    return [_row(m) for m in entries]
