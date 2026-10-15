"""Company config endpoints — GET and PUT."""
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_api_key
from app.models.company import CompanyConfig

router = APIRouter(prefix="/config", dependencies=[Depends(require_api_key)])


def _row(obj):
    """Convert an ORM row to a JSON-safe dict."""
    return jsonable_encoder(
        {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}
    )


@router.get("")
async def get_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompanyConfig).limit(1))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="Company config not found")
    return _row(company)


@router.put("")
async def update_config(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CompanyConfig).limit(1))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="Company config not found")

    for key, value in body.items():
        if hasattr(company, key):
            setattr(company, key, value)

    await db.flush()
    await db.refresh(company)
    return _row(company)
