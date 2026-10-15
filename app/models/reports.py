import sqlalchemy as sa
from app.core.database import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    report_date = sa.Column(sa.Date, unique=True, nullable=False)
    morning_plan = sa.Column(sa.Text)
    evening_summary = sa.Column(sa.Text)
    tasks_planned = sa.Column(sa.Integer, default=0)
    tasks_completed = sa.Column(sa.Integer, default=0)
    tasks_failed = sa.Column(sa.Integer, default=0)
    metrics_snapshot = sa.Column(sa.JSON)
    insights = sa.Column(sa.JSON)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
