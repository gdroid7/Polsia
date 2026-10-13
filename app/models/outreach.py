import sqlalchemy as sa
from app.core.database import Base


class Prospect(Base):
    __tablename__ = "prospects"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    email = sa.Column(sa.String(255), unique=True, nullable=False)
    first_name = sa.Column(sa.String(100))
    last_name = sa.Column(sa.String(100))
    company = sa.Column(sa.String(255))
    title = sa.Column(sa.String(255))
    source = sa.Column(sa.String(100))
    status = sa.Column(sa.String(50), default="new")
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(255), nullable=False)
    goal = sa.Column(sa.Text)
    target_segment = sa.Column(sa.String(255))
    status = sa.Column(sa.String(50), default="active")
    total_sent = sa.Column(sa.Integer, default=0)
    total_opened = sa.Column(sa.Integer, default=0)
    total_replied = sa.Column(sa.Integer, default=0)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    prospect_id = sa.Column(sa.Integer, sa.ForeignKey("prospects.id"), nullable=False)
    campaign_id = sa.Column(sa.Integer, sa.ForeignKey("email_campaigns.id"))
    sequence_step = sa.Column(sa.Integer, default=1)
    subject = sa.Column(sa.String(512))
    body = sa.Column(sa.Text)
    sendgrid_id = sa.Column(sa.String(255))
    status = sa.Column(sa.String(50), default="sent")
    sent_at = sa.Column(sa.DateTime(timezone=True))
    opened_at = sa.Column(sa.DateTime(timezone=True))
    replied_at = sa.Column(sa.DateTime(timezone=True))
    follow_up_due = sa.Column(sa.DateTime(timezone=True))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
