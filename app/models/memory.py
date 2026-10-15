import sqlalchemy as sa
from app.core.database import Base


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    category = sa.Column(sa.String(100), nullable=False)
    title = sa.Column(sa.String(512), nullable=False)
    content = sa.Column(sa.Text, nullable=False)
    source = sa.Column(sa.String(100))
    tags = sa.Column(sa.JSON, default=list)
    chroma_id = sa.Column(sa.String(255), unique=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
