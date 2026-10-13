import sqlalchemy as sa
from app.core.database import Base


class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    platform = sa.Column(sa.String(50), nullable=False)
    external_id = sa.Column(sa.String(255))
    name = sa.Column(sa.String(512), nullable=False)
    goal = sa.Column(sa.String(255))
    status = sa.Column(sa.String(50), default="active")
    daily_budget_usd = sa.Column(sa.Float, default=0.0)
    total_spent_usd = sa.Column(sa.Float, default=0.0)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())


class AdMetric(Base):
    __tablename__ = "ad_metrics"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    campaign_id = sa.Column(sa.Integer, sa.ForeignKey("ad_campaigns.id"), nullable=False)
    date = sa.Column(sa.Date, nullable=False)
    impressions = sa.Column(sa.Integer, default=0)
    clicks = sa.Column(sa.Integer, default=0)
    conversions = sa.Column(sa.Integer, default=0)
    spend_usd = sa.Column(sa.Float, default=0.0)
    ctr = sa.Column(sa.Float, default=0.0)
    cpc = sa.Column(sa.Float, default=0.0)
    roas = sa.Column(sa.Float, default=0.0)
