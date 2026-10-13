"""Social media post endpoints."""
from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_api_key
from app.models.social import SocialPost

router = APIRouter(prefix="/social", dependencies=[Depends(require_api_key)])


def _row(obj):
    """Convert an ORM row to a JSON-safe dict."""
    return jsonable_encoder(
        {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}
    )


@router.get("/posts")
async def get_posts(
    status: str | None = Query(default=None),
    limit: int = Query(default=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SocialPost)
    if status is not None:
        stmt = stmt.where(SocialPost.status == status)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    posts = result.scalars().all()
    return [_row(p) for p in posts]
