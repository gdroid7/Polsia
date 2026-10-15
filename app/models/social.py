import sqlalchemy as sa
from app.core.database import Base


class SocialPost(Base):
    __tablename__ = "social_posts"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    platform = sa.Column(sa.String(50), default="twitter")
    content = sa.Column(sa.Text, nullable=False)
    status = sa.Column(sa.String(50), default="draft")
    tweet_id = sa.Column(sa.String(100))
    scheduled_for = sa.Column(sa.DateTime(timezone=True))
    published_at = sa.Column(sa.DateTime(timezone=True))
    engagement = sa.Column(sa.JSON)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())


class SocialEngagement(Base):
    __tablename__ = "social_engagements"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    mention_id = sa.Column(sa.String(100), unique=True)
    author_handle = sa.Column(sa.String(100))
    content = sa.Column(sa.Text)
    our_reply = sa.Column(sa.Text)
    reply_id = sa.Column(sa.String(100))
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
