import sqlalchemy as sa
from app.core.database import Base


class Competitor(Base):
    __tablename__ = "competitors"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(255), nullable=False)
    website = sa.Column(sa.String(512))
    pricing_info = sa.Column(sa.JSON)
    positioning = sa.Column(sa.Text)
    strengths = sa.Column(sa.JSON)
    weaknesses = sa.Column(sa.JSON)
    last_researched = sa.Column(sa.DateTime(timezone=True))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
