import sqlalchemy as sa
from app.core.database import Base


class CompanyConfig(Base):
    __tablename__ = "company_config"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(255), nullable=False)
    mission = sa.Column(sa.Text)
    vision = sa.Column(sa.Text)
    description = sa.Column(sa.Text)
    target_market = sa.Column(sa.Text)
    value_prop = sa.Column(sa.Text)
    pricing_model = sa.Column(sa.JSON, nullable=True)
    goals = sa.Column(sa.JSON, nullable=True)
    kpis = sa.Column(sa.JSON, nullable=True)
    website_url = sa.Column(sa.String(512))
    github_repo = sa.Column(sa.String(512))
    product_type = sa.Column(sa.String(100))
    industry = sa.Column(sa.String(100))
    timezone = sa.Column(sa.String(50), default="UTC")
    daily_cycle_hour = sa.Column(sa.Integer, default=6)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
