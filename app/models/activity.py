import sqlalchemy as sa
from app.core.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    agent_type = sa.Column(sa.String(100), nullable=False)
    action = sa.Column(sa.String(255), nullable=False)
    summary = sa.Column(sa.Text, nullable=False)
    detail = sa.Column(sa.JSON)
    level = sa.Column(sa.String(20), default="info")
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
