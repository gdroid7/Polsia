import sqlalchemy as sa
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.String(512), nullable=False)
    description = sa.Column(sa.Text)
    agent_type = sa.Column(sa.String(100), nullable=False)
    priority = sa.Column(sa.Integer, default=3)
    status = sa.Column(sa.String(50), default="pending")
    source = sa.Column(sa.String(100), default="orchestrator")
    scheduled_date = sa.Column(sa.DateTime(timezone=True))
    result_summary = sa.Column(sa.Text)
    error_message = sa.Column(sa.Text)
    task_metadata = sa.Column("metadata", sa.JSON)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    task_id = sa.Column(sa.Integer, sa.ForeignKey("tasks.id"))
    agent_type = sa.Column(sa.String(100), nullable=False)
    run_type = sa.Column(sa.String(100), default="task")
    status = sa.Column(sa.String(50), default="running")
    input_context = sa.Column(sa.JSON)
    output = sa.Column(sa.JSON)
    raw_log = sa.Column(sa.Text)
    tokens_used = sa.Column(sa.Integer)
    cost_usd = sa.Column(sa.Float)
    duration_secs = sa.Column(sa.Float)
    started_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    ended_at = sa.Column(sa.DateTime(timezone=True))
