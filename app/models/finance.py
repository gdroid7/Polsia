import sqlalchemy as sa
from app.core.database import Base


class StripeEvent(Base):
    __tablename__ = "stripe_events"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    stripe_event_id = sa.Column(sa.String(255), unique=True, nullable=False)
    event_type = sa.Column(sa.String(255), nullable=False)
    customer_id = sa.Column(sa.String(255))
    amount_cents = sa.Column(sa.Integer)
    currency = sa.Column(sa.String(10))
    status = sa.Column(sa.String(50), default="processed")
    raw_payload = sa.Column(sa.JSON)
    processed_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())


class RevenueSnapshot(Base):
    __tablename__ = "revenue_snapshots"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    snapshot_date = sa.Column(sa.Date, unique=True, nullable=False)
    mrr_cents = sa.Column(sa.Integer, default=0)
    arr_cents = sa.Column(sa.Integer, default=0)
    active_subscribers = sa.Column(sa.Integer, default=0)
    churned_today = sa.Column(sa.Integer, default=0)
    new_today = sa.Column(sa.Integer, default=0)
    total_revenue_month_cents = sa.Column(sa.Integer, default=0)
    stripe_balance_cents = sa.Column(sa.Integer, default=0)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())


class ExpenseRecord(Base):
    __tablename__ = "expense_records"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    category = sa.Column(sa.String(100), nullable=False)
    vendor = sa.Column(sa.String(255), nullable=False)
    amount_cents = sa.Column(sa.Integer, nullable=False)
    currency = sa.Column(sa.String(10), default="usd")
    description = sa.Column(sa.Text)
    date = sa.Column(sa.Date, nullable=False)
    external_ref = sa.Column(sa.String(255))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
