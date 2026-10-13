"""Finance endpoints — revenue, expenses, Stripe events and webhook."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.security import require_api_key
from app.models.finance import ExpenseRecord, RevenueSnapshot, StripeEvent

# No router-level auth — Stripe webhook must be unauthenticated
router = APIRouter(prefix="/finance")


def _row(obj):
    """Convert an ORM row to a JSON-safe dict."""
    return jsonable_encoder(
        {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}
    )


@router.get("/summary", dependencies=[Depends(require_api_key)])
async def finance_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RevenueSnapshot).order_by(RevenueSnapshot.snapshot_date.desc()).limit(1)
    )
    snap = result.scalar_one_or_none()
    if snap is None:
        return {
            "mrr_cents": 0,
            "arr_cents": 0,
            "active_subscribers": 0,
            "stripe_balance_cents": 0,
            "last_snapshot_date": None,
        }
    return {
        "mrr_cents": snap.mrr_cents,
        "arr_cents": snap.arr_cents,
        "active_subscribers": snap.active_subscribers,
        "stripe_balance_cents": snap.stripe_balance_cents,
        "last_snapshot_date": str(snap.snapshot_date),
    }


@router.get("/revenue", dependencies=[Depends(require_api_key)])
async def get_revenue(
    limit: int = Query(default=30),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RevenueSnapshot).order_by(RevenueSnapshot.snapshot_date.desc()).limit(limit)
    )
    snaps = result.scalars().all()
    return [_row(s) for s in snaps]


@router.get("/expenses", dependencies=[Depends(require_api_key)])
async def get_expenses(
    category: str | None = Query(default=None),
    limit: int = Query(default=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExpenseRecord)
    if category is not None:
        stmt = stmt.where(ExpenseRecord.category == category)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    expenses = result.scalars().all()
    return [_row(e) for e in expenses]


@router.get("/events", dependencies=[Depends(require_api_key)])
async def get_stripe_events(
    limit: int = Query(default=50),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StripeEvent).limit(limit))
    events = result.scalars().all()
    return [_row(e) for e in events]


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Stripe-verified webhook — no API key auth."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        import stripe as stripe_lib  # noqa: PLC0415
        stripe_lib.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    return {"received": True}
