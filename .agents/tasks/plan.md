# Implementation Plan — Polsia `app/` Module for TapReview

**Worktree root:** `/Users/gauravshewale/Development/business/NFC/polsia`  
**All file paths below are relative to that root unless otherwise stated.**  
**Test command (run from worktree root):** `CLAUDE_CLI_MOCK=true python -m pytest tests/unit/ -v`  
**Note:** CLAUDE.md says `cd backend` but there is no `backend/` subdirectory. All source and tests live at the project root. Run pytest from `/Users/gauravshewale/Development/business/NFC/polsia`.

---

## Phase 0 — Housekeeping (do first, no dependencies)

### 0-A  Fix duplicate conftest

- **What:** Delete `/Users/gauravshewale/Development/business/NFC/polsia/conftest.py`  
  The root `conftest.py` is byte-for-byte identical to `tests/conftest.py`. `pyproject.toml` sets `testpaths = ["tests"]`, but pytest always loads root-level conftest files, causing duplicate-fixture errors. Delete the root one; `tests/conftest.py` is the canonical copy.
- **File to delete:** `conftest.py` (root)
- **Verify:** `python -m pytest --co -q tests/unit/` — no "duplicate fixture" warnings.

### 0-B  Fix docker-compose.yml build contexts

- **What:** In `docker-compose.yml`, change every `context: ./backend` to `context: .`  
  Three occurrences: under services `backend`, `celery_worker`, `celery_beat`.
- **File:** `docker-compose.yml`
- **Verify:** `grep 'context:' docker-compose.yml` — should show only `context: .` (three times) and `context: ./frontend` (once).

### 0-C  Fix celery_config.py timezone

- **What:** Change `timezone = "UTC"` → `timezone = "Asia/Kolkata"` in `celery_app/celery_config.py`.
- **File:** `celery_app/celery_config.py`
- **Verify:** `grep "Asia/Kolkata" celery_app/celery_config.py` confirms the change.

### 0-D  Create `.env`

Create `/Users/gauravshewale/Development/business/NFC/polsia/.env` with exactly these contents:

```
API_KEY=polsia-nfc-dev-key-2026
SANDBOX_MODE=true
POSTGRES_USER=polsia
POSTGRES_PASSWORD=polsia_secret_2026
POSTGRES_DB=polsia
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CLAUDE_CLI_PATH=/usr/local/bin/claude
MORNING_CYCLE_HOUR=10
EVENING_CYCLE_HOUR=20
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
SENDGRID_API_KEY=
IMAP_HOST=
IMAP_USER=
IMAP_PASSWORD=
TAVILY_API_KEY=
GOOGLE_ADS_DEVELOPER_TOKEN=
META_APP_ID=
META_APP_SECRET=
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=
GITHUB_TOKEN=
```

### 0-E  Update `scripts/seed_company.py`

Replace the `CompanyConfig(...)` call with TapReview values:

```python
company = CompanyConfig(
    name="TapReview",
    mission="Help small businesses collect more Google reviews with a single NFC tap.",
    vision="Every restaurant, cafe, and convenience store in India has a tap-to-review system at the counter.",
    description="NFC tags pre-programmed to open customised Google review flows, with a management dashboard for business owners.",
    target_market="Small businesses in India — restaurants, cafes, convenience stores.",
    value_prop="Get 5x more Google reviews by making it effortless — customers tap, review, done in under 10 seconds.",
    pricing_model={"plans": [{"name": "Starter", "price_inr": 999, "nfc_cards": 2}, {"name": "Business", "price_inr": 2499, "nfc_cards": 10}]},
    goals={"2026": ["Validate product-market fit with 10 paying beta customers", "Launch in Mumbai and Pune", "Build waitlist of 500 businesses"]},
    kpis={"mrr_inr": 0, "active_customers": 0, "nfc_cards_shipped": 0, "avg_reviews_per_card_per_month": 0},
    website_url="https://tapreview.in",
    github_repo="placeholder/tapreview",
    product_type="Hardware + SaaS",
    industry="Local Business Tech",
    timezone="Asia/Kolkata",
    daily_cycle_hour=10,
)
```

Keep the rest of the file (imports, asyncio, engine creation, guard logic) unchanged.

---

## Phase 1 — `app/` Core Infrastructure

All files in this phase must be created before any service or route.

### 1-A  `app/__init__.py`

Empty file. Just creates the package.

### 1-B  `app/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    database_url: str = "postgresql+asyncpg://polsia:polsia_secret_2026@postgres:5432/polsia"
    api_key: str = "polsia-nfc-dev-key-2026"
    sandbox_mode: bool = True
    claude_cli_path: str = "/usr/local/bin/claude"
    claude_cli_mock: bool = False          # env: CLAUDE_CLI_MOCK
    claude_cli_mock_response: str = '{"result": "Mock response"}'  # env: CLAUDE_CLI_MOCK_RESPONSE
    morning_cycle_hour: int = 10           # env: MORNING_CYCLE_HOUR
    evening_cycle_hour: int = 20           # env: EVENING_CYCLE_HOUR
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    redis_url: str = "redis://redis:6379/0"
    chroma_persist_dir: str = "/app/data/chroma"
    stripe_webhook_secret: str = ""

settings = Settings()
```

**Gotcha:** `api_key` must be a mutable attribute. The test fixture does `settings.api_key = "test-key"` at runtime. `SettingsConfigDict` without `frozen=True` allows this.

**Gotcha:** `case_sensitive=False` means environment variables `MORNING_CYCLE_HOUR` → `morning_cycle_hour`, `CLAUDE_CLI_MOCK` → `claude_cli_mock`, etc. Use lowercase field names.

### 1-C  `app/core/__init__.py`

Empty file.

### 1-D  `app/core/database.py`

```python
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.config import settings


class Base(DeclarativeBase):
    type_annotation_map = {dict: sa.JSON, list: sa.JSON}


engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Exports:** `Base`, `get_db`, `engine`

**Gotcha:** `create_async_engine` with asyncpg defers the actual import of `asyncpg` until the first connection attempt. Module-level engine creation is safe in unit tests (which use SQLite and override `get_db`).

**Gotcha:** `get_db` auto-commits on successful yield. This means API handlers must NOT call `await db.commit()`. They call `await db.flush()` + `await db.refresh(obj)` when they need the server-set `updated_at` before returning.

**Gotcha:** The conftest overrides `get_db` with `lambda: async_db_session` (returns session directly, not a generator). FastAPI handles this correctly.

### 1-E  `app/core/redis_client.py`

```python
import redis.asyncio as aioredis
from app.config import settings

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client
```

**Gotcha:** The conftest patches `app.core.redis_client.get_redis` — the name and module path must match exactly.

### 1-F  `app/core/events.py`

```python
import json
from app.core.redis_client import get_redis


async def broadcast_activity(payload: dict) -> None:
    redis = await get_redis()
    await redis.publish("polsia:activity", json.dumps(payload))
```

**Gotcha:** The conftest patches `app.core.events.get_redis` — the `from app.core.redis_client import get_redis` import means the name `get_redis` lives in the `app.core.events` namespace. So patching `app.core.events.get_redis` works.

### 1-G  `app/core/chroma_client.py`

```python
from app.config import settings


def get_collection():
    """Lazy-import chromadb so unit tests can import this module without chromadb installed."""
    import chromadb  # noqa: PLC0415 — intentional lazy import
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return client.get_or_create_collection("polsia_memory")
```

**Gotcha:** NEVER import chromadb at module level. The conftest patches `app.core.chroma_client.get_collection`. This is fine because `get_collection` is defined (and thus named) at module level in this file; it's just the body that's lazy.

### 1-H  `app/core/security.py`

```python
from fastapi import Header, HTTPException


async def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    from app.config import settings  # imported inside function to always read current value
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
```

**Gotcha:** `from app.config import settings` is inside the function body, not at module level. The test fixture sets `settings.api_key = "test-key"` on the already-imported `settings` singleton. The import inside the function will get the same singleton (Python module cache), so it reads the updated value. Alternatively, import `settings` at module level — it's the same object. Either works because `settings` is a module-level singleton.

**Gotcha:** Using `Header(default=None)` means a missing header sends `None` which != any valid key → 401. If you use `Header(...)` (required), FastAPI returns 422 before the function runs. The test `test_trigger_requires_auth` expects 401, not 422.

**Gotcha:** FastAPI converts header names to Python params: `X-API-Key` → `x_api_key` (lowercase, `-` → `_`). This is automatic.

---

## Phase 2 — SQLAlchemy Models

All models **must use `sa.JSON` for every JSON/dict/list column**. Never use `postgresql.JSONB` or `postgresql.ARRAY`. The unit tests use SQLite which does not support those Postgres types.

**Pattern for every model file:**
```python
import sqlalchemy as sa
from sqlalchemy.orm import relationship  # only if needed
from app.core.database import Base

class MyModel(Base):
    __tablename__ = "my_table"
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    # ... columns with Python-side defaults (default=...), not only server_default
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())
```

Use Python-side `default=` for columns the tests check before a DB round-trip (e.g., `status="pending"`, `priority=3`). Use `server_default` for timestamps.

### 2-A  `app/models/__init__.py`

```python
from app.models.company import CompanyConfig
from app.models.task import Task, AgentRun
from app.models.activity import ActivityLog
from app.models.memory import MemoryEntry
from app.models.social import SocialPost, SocialEngagement
from app.models.outreach import Prospect, EmailCampaign, EmailLog
from app.models.ads import AdCampaign, AdMetric
from app.models.competitors import Competitor
from app.models.finance import StripeEvent, RevenueSnapshot, ExpenseRecord
from app.models.reports import DailyReport

__all__ = [
    "CompanyConfig", "Task", "AgentRun", "ActivityLog", "MemoryEntry",
    "SocialPost", "SocialEngagement", "Prospect", "EmailCampaign", "EmailLog",
    "AdCampaign", "AdMetric", "Competitor", "StripeEvent", "RevenueSnapshot",
    "ExpenseRecord", "DailyReport",
]
```

### 2-B  `app/models/company.py`

Table: `company_config`

```
id            Integer PK autoincrement
name          String(255) nullable=False
mission       Text
vision        Text
description   Text
target_market Text
value_prop    Text
pricing_model sa.JSON  (nullable)
goals         sa.JSON  (nullable)
kpis          sa.JSON  (nullable)
website_url   String(512)
github_repo   String(512)
product_type  String(100)
industry      String(100)
timezone      String(50)  default="UTC"
daily_cycle_hour Integer default=6
created_at    DateTime(timezone=True) server_default=sa.func.now()
updated_at    DateTime(timezone=True) server_default=sa.func.now() onupdate=sa.func.now()
```

### 2-C  `app/models/task.py`

Table `tasks` → class `Task`:
```
id             Integer PK autoincrement
title          String(512) nullable=False
description    Text
agent_type     String(100) nullable=False
priority       Integer default=3
status         String(50)  default="pending"
source         String(100) default="orchestrator"
scheduled_date DateTime(timezone=True)
result_summary Text
error_message  Text
metadata       sa.JSON
created_at     DateTime(timezone=True) server_default=sa.func.now()
updated_at     DateTime(timezone=True) server_default=sa.func.now() onupdate=sa.func.now()
```

Table `agent_runs` → class `AgentRun`:
```
id             Integer PK autoincrement
task_id        Integer ForeignKey("tasks.id")
agent_type     String(100) nullable=False
run_type       String(100) default="task"
status         String(50)  default="running"
input_context  sa.JSON
output         sa.JSON
raw_log        Text
tokens_used    Integer
cost_usd       Float
duration_secs  Float
started_at     DateTime(timezone=True) server_default=sa.func.now()
ended_at       DateTime(timezone=True)
```

### 2-D  `app/models/activity.py`

Table `activity_log` → class `ActivityLog`:
```
id         Integer PK autoincrement
agent_type String(100) nullable=False
action     String(255) nullable=False
summary    Text nullable=False
detail     sa.JSON
level      String(20) default="info"
created_at DateTime(timezone=True) server_default=sa.func.now()
```

### 2-E  `app/models/memory.py`

Table `memory_entries` → class `MemoryEntry`:
```
id         Integer PK autoincrement
category   String(100) nullable=False
title      String(512) nullable=False
content    Text nullable=False
source     String(100)
tags       sa.JSON   ← NOT ARRAY. Store as JSON list: default=[]
chroma_id  String(255) unique=True
created_at DateTime(timezone=True) server_default=sa.func.now()
```

**Gotcha:** The alembic migration uses `postgresql.ARRAY(sa.String())` for `tags`, but the ORM model must use `sa.JSON` for SQLite compatibility. These diverge — the migration stays as-is (it runs against real Postgres in Docker), but the ORM model uses JSON.

### 2-F  `app/models/social.py`

Table `social_posts` → class `SocialPost`:
```
id           Integer PK autoincrement
platform     String(50) default="twitter"
content      Text nullable=False
status       String(50) default="draft"
tweet_id     String(100)
scheduled_for DateTime(timezone=True)
published_at  DateTime(timezone=True)
engagement   sa.JSON
created_at   DateTime(timezone=True) server_default=sa.func.now()
```

Table `social_engagements` → class `SocialEngagement`:
```
id           Integer PK autoincrement
mention_id   String(100) unique=True
author_handle String(100)
content      Text
our_reply    Text
reply_id     String(100)
created_at   DateTime(timezone=True) server_default=sa.func.now()
```

### 2-G  `app/models/outreach.py`

Table `prospects` → class `Prospect`:
```
id         Integer PK autoincrement
email      String(255) unique=True nullable=False
first_name String(100)
last_name  String(100)
company    String(255)
title      String(255)
source     String(100)
status     String(50) default="new"
created_at DateTime(timezone=True) server_default=sa.func.now()
```

Table `email_campaigns` → class `EmailCampaign`:
```
id             Integer PK autoincrement
name           String(255) nullable=False
goal           Text
target_segment String(255)
status         String(50) default="active"
total_sent     Integer default=0
total_opened   Integer default=0
total_replied  Integer default=0
created_at     DateTime(timezone=True) server_default=sa.func.now()
```

Table `email_logs` → class `EmailLog`:
```
id           Integer PK autoincrement
prospect_id  Integer ForeignKey("prospects.id") nullable=False
campaign_id  Integer ForeignKey("email_campaigns.id")
sequence_step Integer default=1
subject      String(512)
body         Text
sendgrid_id  String(255)
status       String(50) default="sent"
sent_at      DateTime(timezone=True)
opened_at    DateTime(timezone=True)
replied_at   DateTime(timezone=True)
follow_up_due DateTime(timezone=True)
created_at   DateTime(timezone=True) server_default=sa.func.now()
```

### 2-H  `app/models/ads.py`

Table `ad_campaigns` → class `AdCampaign`:
```
id              Integer PK autoincrement
platform        String(50) nullable=False
external_id     String(255)
name            String(512) nullable=False
goal            String(255)
status          String(50) default="active"
daily_budget_usd Float default=0.0
total_spent_usd  Float default=0.0
created_at      DateTime(timezone=True) server_default=sa.func.now()
```

Table `ad_metrics` → class `AdMetric`:
```
id          Integer PK autoincrement
campaign_id Integer ForeignKey("ad_campaigns.id") nullable=False
date        Date nullable=False
impressions Integer default=0
clicks      Integer default=0
conversions Integer default=0
spend_usd   Float default=0.0
ctr         Float default=0.0
cpc         Float default=0.0
roas        Float default=0.0
```

### 2-I  `app/models/competitors.py`

Table `competitors` → class `Competitor`:
```
id             Integer PK autoincrement
name           String(255) nullable=False
website        String(512)
pricing_info   sa.JSON   ← NOT JSONB
positioning    Text
strengths      sa.JSON   ← NOT ARRAY
weaknesses     sa.JSON   ← NOT ARRAY
last_researched DateTime(timezone=True)
created_at     DateTime(timezone=True) server_default=sa.func.now()
```

### 2-J  `app/models/finance.py`

Table `stripe_events` → class `StripeEvent`:
```
id              Integer PK autoincrement
stripe_event_id String(255) unique=True nullable=False
event_type      String(255) nullable=False
customer_id     String(255)
amount_cents    Integer
currency        String(10)
status          String(50) default="processed"
raw_payload     sa.JSON
processed_at    DateTime(timezone=True) server_default=sa.func.now()
```

Table `revenue_snapshots` → class `RevenueSnapshot`:
```
id                      Integer PK autoincrement
snapshot_date           Date unique=True nullable=False
mrr_cents               Integer default=0
arr_cents               Integer default=0
active_subscribers      Integer default=0
churned_today           Integer default=0
new_today               Integer default=0
total_revenue_month_cents Integer default=0
stripe_balance_cents    Integer default=0
created_at              DateTime(timezone=True) server_default=sa.func.now()
```

Table `expense_records` → class `ExpenseRecord`:
```
id          Integer PK autoincrement
category    String(100) nullable=False
vendor      String(255) nullable=False
amount_cents Integer nullable=False
currency    String(10) default="usd"
description Text
date        Date nullable=False
external_ref String(255)
created_at  DateTime(timezone=True) server_default=sa.func.now()
```

### 2-K  `app/models/reports.py`

Table `daily_reports` → class `DailyReport`:
```
id               Integer PK autoincrement
report_date      Date unique=True nullable=False
morning_plan     Text
evening_summary  Text
tasks_planned    Integer default=0
tasks_completed  Integer default=0
tasks_failed     Integer default=0
metrics_snapshot sa.JSON    ← NOT JSONB
insights         sa.JSON    ← NOT ARRAY (store as JSON list)
created_at       DateTime(timezone=True) server_default=sa.func.now()
updated_at       DateTime(timezone=True) server_default=sa.func.now() onupdate=sa.func.now()
```

**Gotcha:** `insights` in `test_save_evening_summary` is checked as a Python list:
```python
assert report.insights == ["Referral traffic up 20%", "Support load low"]
```
Using `sa.JSON` stores it as JSON and returns a Python list on read — this works fine with both SQLite and Postgres.

---

## Phase 3 — Services

### 3-A  `app/services/__init__.py`

Empty file.

### 3-B  `app/services/task_service.py`

All functions are `async`. Import `Task`, `AgentRun` from `app.models.task`.

```python
async def create_task(db, title, agent_type, description=None, priority=3, source="orchestrator") -> Task
```
- Creates and adds `Task` instance; calls `await db.flush(); await db.refresh(task)`; returns task.

```python
async def get_task(db, task_id: int) -> Task | None
```
- `await db.get(Task, task_id)` — returns None if not found.

```python
async def list_tasks(db, status=None, agent_type=None, limit=50) -> list[Task]
```
- Builds a `select(Task)` query; adds `.where(Task.status == status)` if status given; `.where(Task.agent_type == agent_type)` if given; `.limit(limit)`.
- Returns `result.scalars().all()`.

```python
async def update_task_status(db, task_id, status, result_summary=None, error_message=None) -> Task | None
```
- Gets task via `get_task`; sets `.status`, `.result_summary`, `.error_message` if provided; flushes; refreshes; returns task or None.

```python
async def create_agent_run(db, agent_type, task_id=None, input_context=None) -> AgentRun
```
- Creates `AgentRun`; flushes; refreshes; returns.

```python
async def finish_agent_run(db, run_id, status, output=None, duration_secs=None) -> AgentRun
```
- Gets `AgentRun` by `await db.get(AgentRun, run_id)`; sets `.status`, `.output`, `.duration_secs`, `.ended_at = datetime.utcnow()`; flushes; refreshes; returns.

```python
async def get_tasks_today_summary(db) -> dict
```
- Queries tasks created today (since `datetime.combine(date.today(), time.min)`).
- Returns `{"total": int, "pending": int, "in_progress": int, "completed": int, "failed": int}`.
- Uses `GROUP BY status` aggregation or individual count queries.

### 3-C  `app/services/activity_service.py`

```python
async def log_activity(db, agent_type, action, summary, level="info", detail=None) -> ActivityLog
```
- Creates `ActivityLog`; flushes; refreshes.
- Then publishes to Redis: `redis = await get_redis(); await redis.publish("polsia:activity", json.dumps({...}))`.
- Import `get_redis` from `app.core.redis_client` at top of file (so patching `app.core.events.get_redis` doesn't affect this — patching `app.core.redis_client.get_redis` does).
- The conftest patches `app.core.redis_client.get_redis` — since this service imports `from app.core.redis_client import get_redis`, the patch target `app.core.redis_client.get_redis` will work.

**Gotcha (test_log_activity_publishes_to_redis):**
```python
mock_redis.publish.assert_called_once()
call_args = mock_redis.publish.call_args
assert "polsia:activity" in call_args[0]
```
`call_args[0]` is the positional args tuple. So `redis.publish("polsia:activity", json_str)` where the channel is the first positional arg.

```python
async def get_recent_activity(db, limit=50) -> list[ActivityLog]
```
- `select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)`
- Returns list in most-recent-first order.

### 3-D  `app/services/company_service.py`

```python
async def get_full_context(db) -> dict
```
- `result = await db.execute(select(CompanyConfig).limit(1)); company = result.scalar_one_or_none()`
- If `company is None`: return `{}`
- Get yesterday's report: `select(DailyReport).where(DailyReport.report_date == date.today() - timedelta(days=1))`; extract `.evening_summary` or None.
- Get today's tasks: `select(Task).where(Task.created_at >= datetime.combine(date.today(), time.min)).limit(20)`
- Return:
  ```python
  {
      "company": {col.key: getattr(company, col.key) for col in inspect(company.__class__).mapper.column_attrs},
      "kpis": company.kpis or {},
      "yesterday_summary": yesterday_summary,
      "todays_tasks": [{"title": t.title, "agent_type": t.agent_type, "status": t.status} for t in tasks],
  }
  ```
- Import: `from sqlalchemy import inspect as sa_inspect`

**Test check:** `result["company"]["name"] == "Test Co"` and `result["kpis"]["mrr_usd"] == 1000`. The `company` dict is built from all column attributes, so it includes `name`. The `kpis` field is the JSON value of `company.kpis`.

```python
def build_context_prompt(context: dict) -> str
```
- If `not context`: return `"No company context available."`
- Build a multi-line string that MUST include: the company name, `"mrr_usd"` key name, yesterday summary text, and task titles.
- Suggested structure:
  ```
  Company: {name}
  Mission: {mission}
  
  KPIs:
    mrr_usd: {val}
    {other_key}: {val}
  
  Yesterday: {yesterday_summary}
  
  Today's tasks:
    - {task_title} ({agent_type}) [{status}]
  ```
- The test asserts: `"No company context" in result` (empty), `"ACME" in result`, `"mrr_usd" in result`, `"Good day" in result`, `"Do thing" in result`.

### 3-E  `app/services/memory_service.py`

**Critical:** This file must re-export `get_collection` at module level:
```python
from app.core.chroma_client import get_collection  # re-export for patching
```

The conftest patches `app.services.memory_service.get_collection`. This only works if `get_collection` is a name in the `app.services.memory_service` namespace (i.e., imported at module level here).

```python
async def store_memory(db, category, title, content, source=None, tags=None) -> MemoryEntry
```
- `chroma_id = str(uuid4())`
- Create `MemoryEntry(category=category, title=title, content=content, source=source, tags=tags or [], chroma_id=chroma_id)`
- `db.add(entry); await db.flush(); await db.refresh(entry)`
- Call: `get_collection().add(documents=[content], metadatas=[{"category": category, "title": title, "source": source or ""}], ids=[chroma_id])`
- Return entry.

**Gotcha (test_store_memory_calls_chroma):** The test checks `mock_chroma.add.call_args[1]` (kwargs), specifically `call_args[1]["documents"][0]`. So pass all arguments as keyword arguments to `collection.add(...)`.

```python
async def search_memory(db, query, n_results=5) -> list[dict]
```
- `results = get_collection().query(query_texts=[query], n_results=n_results)`
- Unpack: `documents = results["documents"][0]`, `metadatas = results["metadatas"][0]`
- Return `[{"content": doc, "category": meta.get("category"), "title": meta.get("title"), "source": meta.get("source")} for doc, meta in zip(documents, metadatas)]`

```python
async def list_memories(db, category=None, limit=50) -> list[MemoryEntry]
```
- `select(MemoryEntry)`, optional `.where(MemoryEntry.category == category)`, `.limit(limit)`
- Returns list. Does NOT call chroma.

### 3-F  `app/services/report_service.py`

```python
async def get_or_create_daily_report(db, report_date) -> DailyReport
```
- `select(DailyReport).where(DailyReport.report_date == report_date)`
- If exists, return it.
- If not: create `DailyReport(report_date=report_date)`, `db.add(r)`, `await db.flush(); await db.refresh(r)`, return.

**Idempotency test:** two calls with same date must return same `id`. The second call finds the existing row and returns it.

```python
async def save_morning_plan(db, report_date, plan_text, tasks_planned=0) -> DailyReport
```
- `get_or_create_daily_report` then set `.morning_plan = plan_text`, `.tasks_planned = tasks_planned`; flush; refresh; return.

```python
async def save_evening_summary(db, report_date, summary, insights=None, tasks_completed=0, tasks_failed=0, metrics_snapshot=None) -> DailyReport
```
- Get or create; set `.evening_summary`, `.insights = insights or []`, `.tasks_completed`, `.tasks_failed`, `.metrics_snapshot`; flush; refresh; return.

```python
async def get_daily_report(db, report_date) -> DailyReport | None
```
- `select(DailyReport).where(DailyReport.report_date == report_date)`, return scalar or None.

---

## Phase 4 — Agents

### 4-A  `app/agents/__init__.py`

Empty.

### 4-B  `app/agents/base_agent.py`

```python
import json
import os
import subprocess
import time
from abc import ABC, abstractmethod
from app.config import settings


class BasePolsiaAgent(ABC):
    agent_type: str = "base"

    def call_claude(self, prompt: str) -> str:
        """Call Claude CLI or return mock response."""
        if os.getenv("CLAUDE_CLI_MOCK", "").lower() in ("true", "1", "yes"):
            raw = os.getenv("CLAUDE_CLI_MOCK_RESPONSE", settings.claude_cli_mock_response)
            return json.loads(raw)["result"]
        
        result = subprocess.run(
            [settings.claude_cli_path, "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return json.loads(result.stdout)["result"]

    def call_claude_json(self, prompt: str) -> dict:
        """Call Claude and parse the result as JSON."""
        raw = self.call_claude(prompt)
        return json.loads(raw)

    def timed_run(self, task: dict, context: dict) -> dict:
        """Run agent and add duration_secs to result."""
        start = time.monotonic()
        result = self.run(task, context)
        duration = round(time.monotonic() - start, 3)
        return {**result, "duration_secs": duration}

    @abstractmethod
    def run(self, task: dict, context: dict) -> dict:
        """Implement in subclass. Must return dict with at least {"summary": str}."""
        ...
```

**Gotcha (test_call_claude_returns_mock_when_env_set):**
```python
result = agent.call_claude("test prompt")
assert result == "hello from mock"
```
`CLAUDE_CLI_MOCK_RESPONSE = json.dumps({"result": "hello from mock"})`. So `json.loads(raw)["result"]` = `"hello from mock"` (a string). `call_claude` returns a string. ✓

**Gotcha (test_call_claude_json_parses_result):**
`CLAUDE_CLI_MOCK_RESPONSE = json.dumps({"result": '{"key": "value", "number": 42}'})`.
`call_claude` returns `'{"key": "value", "number": 42}'` (a JSON string).
`call_claude_json` calls `json.loads(...)` on that → `{"key": "value", "number": 42}`. ✓

**Gotcha (test_call_claude_does_not_invoke_subprocess_in_mock_mode):** `call_claude` must check `os.getenv("CLAUDE_CLI_MOCK")` BEFORE calling `subprocess.run`. ✓

**Gotcha:** `timed_run` returns `{**result, "duration_secs": duration}`. The test `test_timed_run_adds_duration` creates a `ConcreteAgent` (whose `run` returns `{"summary": "test"}`), calls `agent.timed_run({"title": "test"}, {})`, and asserts `"duration_secs" in result` and `isinstance(result["duration_secs"], float)`. `round(..., 3)` returns a float. ✓

### 4-C  `app/agents/crew_factory.py`

```python
import importlib

AGENT_MAP: dict[str, tuple[str, str]] = {
    "orchestrator":          ("app.agents.orchestrator.agent",          "OrchestratorAgent"),
    "social_media":          ("app.agents.social_media.agent",          "SocialMediaAgent"),
    "competitor_research":   ("app.agents.competitor_research.agent",   "CompetitorResearchAgent"),
    "business_planning":     ("app.agents.business_planning.agent",     "BusinessPlanningAgent"),
    "email_outreach":        ("app.agents.email_outreach.agent",        "EmailOutreachAgent"),
    "customer_support":      ("app.agents.customer_support.agent",      "CustomerSupportAgent"),
    "ads_management":        ("app.agents.ads_management.agent",        "AdsManagementAgent"),
    "code_generation":       ("app.agents.code_generation.agent",       "CodeGenerationAgent"),
    "finance":               ("app.agents.finance.agent",               "FinanceAgent"),
}


def run_agent_for_task(agent_type: str, task: dict, context: dict) -> dict:
    if agent_type not in AGENT_MAP:
        raise ValueError(f"Unknown agent type: {agent_type}")
    module_path, class_name = AGENT_MAP[agent_type]
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    agent = cls()
    return agent.timed_run(task, context)
```

**Gotcha (test_crew_factory_raises_on_unknown_agent):** `pytest.raises(ValueError, match="Unknown agent")` — the error message `"Unknown agent type: nonexistent_agent"` contains `"Unknown agent"`. ✓

**Gotcha (test_crew_factory_returns_result):** The test patches `app.agents.social_media.agent.SocialMediaAgent.run` — so the module path `"app.agents.social_media.agent"` and class name `"SocialMediaAgent"` must be exact. ✓

### 4-D  9 Agent Implementations

For each of the 9 agents, create:
- `app/agents/{name}/__init__.py` (empty)
- `app/agents/{name}/agent.py` (the agent class)

The agent list with folder names and class names:

| folder name          | class name                  |
|----------------------|-----------------------------|
| `orchestrator`       | `OrchestratorAgent`         |
| `social_media`       | `SocialMediaAgent`          |
| `competitor_research`| `CompetitorResearchAgent`   |
| `business_planning`  | `BusinessPlanningAgent`     |
| `email_outreach`     | `EmailOutreachAgent`        |
| `customer_support`   | `CustomerSupportAgent`      |
| `ads_management`     | `AdsManagementAgent`        |
| `code_generation`    | `CodeGenerationAgent`       |
| `finance`            | `FinanceAgent`              |

Template for each agent:

```python
from app.agents.base_agent import BasePolsiaAgent
from app.services.company_service import build_context_prompt


class SocialMediaAgent(BasePolsiaAgent):  # rename per agent
    agent_type = "social_media"  # rename per agent

    def run(self, task: dict, context: dict) -> dict:
        context_str = build_context_prompt(context)
        prompt = f"""You are the Social Media agent for a company.
Task: {task.get('title', 'No title')}
Description: {task.get('description', 'No description')}

Company context:
{context_str}

Respond with a JSON object containing:
- "summary": one-sentence summary of what you did
- "result": detailed output of the task
"""
        try:
            result = self.call_claude_json(prompt)
        except Exception as e:
            result = {"summary": f"Task failed: {e}", "result": {}}
        
        return {
            "summary": result.get("summary", str(result)),
            "result": result,
        }
```

Each agent sets its own `agent_type` string matching the key in `AGENT_MAP`. The `run` method returns a dict with at least `{"summary": str, "result": ...}`.

---

## Phase 5 — API Routes

### 5-A  `app/api/__init__.py` and `app/api/v1/__init__.py`

Both empty.

### 5-B  Serialization helper

In each router that returns ORM objects, use this pattern to convert to a JSON-safe dict:

```python
from sqlalchemy import inspect as sa_inspect
from fastapi.encoders import jsonable_encoder

def _row(obj):
    """Convert SQLAlchemy ORM row to JSON-safe dict."""
    return jsonable_encoder(
        {c.key: getattr(obj, c.key) for c in sa_inspect(obj.__class__).mapper.column_attrs}
    )
```

Put this function inline in each router file that needs it, or in a shared `app/api/utils.py`. Either approach works; keep it consistent.

### 5-C  `app/api/v1/health.py`

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}
```

No auth. No database.

### 5-D  `app/api/v1/dashboard.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import require_api_key
from app.services.task_service import get_tasks_today_summary
from app.services.activity_service import get_recent_activity
from app.services.company_service import get_full_context
from app.services.report_service import get_daily_report
from datetime import date

router = APIRouter(prefix="/dashboard", dependencies=[Depends(require_api_key)])
```

**GET `/dashboard/summary`:**
- Call `get_tasks_today_summary(db)` → `{"total", "pending", "in_progress", "completed", "failed"}`
- Call `get_full_context(db)` → extract `kpis`
- Call `get_recent_activity(db, limit=1)` → take first item or None
- Return:
  ```python
  {
      "tasks_today_total": summary["total"],
      "tasks_today_pending": summary["pending"],
      "tasks_today_completed": summary["completed"],
      "tasks_today_failed": summary["failed"],
      "kpis": context.get("kpis", {}),
      "last_activity": _row(activities[0]) if activities else None,
  }
  ```

**GET `/dashboard/activity?limit=50`:**
- Calls `get_recent_activity(db, limit=limit)` → returns `[_row(a) for a in activities]`

**GET `/dashboard/reports/daily`:**
- Calls `get_daily_report(db, date.today())` → return `_row(report)` if found, else `null` (return `None`; FastAPI serializes to JSON null).

### 5-E  `app/api/v1/tasks.py`

```python
router = APIRouter(prefix="/tasks", dependencies=[Depends(require_api_key)])
```

**GET `/tasks?status=&agent_type=&limit=50`:**
- `list_tasks(db, status=status, agent_type=agent_type, limit=limit)` → `[_row(t) for t in tasks]`

**POST `/tasks` → 201:**
Body schema (use a Pydantic model or `Body`):
```python
class TaskCreate(BaseModel):
    title: str
    agent_type: str
    description: str | None = None
    priority: int = 3
```
- `create_task(db, title=body.title, agent_type=body.agent_type, description=body.description, priority=body.priority)`
- Return `_row(task)` with `status_code=201`.

**GET `/tasks/{task_id}`:**
- `get_task(db, task_id)` → `_row(task)` or 404.

### 5-F  `app/api/v1/agents.py`

```python
VALID_AGENT_TYPES = [
    "orchestrator", "social_media", "competitor_research", "business_planning",
    "email_outreach", "customer_support", "ads_management", "code_generation", "finance",
]

router = APIRouter(prefix="/agents", dependencies=[Depends(require_api_key)])
```

**POST `/agents/{agent_type}/trigger` → 202:**
```python
@router.post("/{agent_type}/trigger", status_code=202)
async def trigger_agent(agent_type: str, body: dict = Body(default={}), db: AsyncSession = Depends(get_db)):
    if agent_type not in VALID_AGENT_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid agent type: {agent_type}")
    
    task_title = body.get("task_title") or f"Manual trigger: {agent_type}"
    task = await create_task(db, title=task_title, agent_type=agent_type, source="api")
    await db.flush()
    
    from celery_app.tasks.agent_tasks import run_agent_task
    run_agent_task.delay(task.id)
    
    return {"status": "queued", "task_id": task.id}
```

**Gotcha:** The test patches `celery_app.tasks.agent_tasks.run_agent_task.delay` — the import must be inside the function body to be patchable at that path. Or import at top of file and patch the function's `.delay` attribute. The test uses `with patch("celery_app.tasks.agent_tasks.run_agent_task.delay")`, which patches the `.delay` attribute on the task. Importing `run_agent_task` from anywhere still uses the same object, so top-level import works too. Just import it at module top or inside the handler — either is fine since the patch target is the object attribute.

**GET `/agents/status`:**
For each agent type in `VALID_AGENT_TYPES`, query `AgentRun` table:
```python
@router.get("/status")
async def get_agent_status(db: AsyncSession = Depends(get_db)):
    from datetime import date, datetime
    today_start = datetime.combine(date.today(), datetime.min.time())
    result = []
    for agent_type in VALID_AGENT_TYPES:
        # Latest run
        last_run = await db.execute(
            select(AgentRun)
            .where(AgentRun.agent_type == agent_type)
            .order_by(AgentRun.started_at.desc())
            .limit(1)
        )
        last = last_run.scalar_one_or_none()
        
        # Runs today
        count_result = await db.execute(
            select(func.count(AgentRun.id))
            .where(AgentRun.agent_type == agent_type, AgentRun.started_at >= today_start)
        )
        runs_today = count_result.scalar() or 0
        
        result.append({
            "agent_type": agent_type,
            "last_run_at": last.started_at.isoformat() if last else None,
            "last_status": last.status if last else None,
            "runs_today": runs_today,
        })
    return result
```

**Gotcha:** Test expects exactly 9 items and checks that `"social_media"` and `"finance"` are in the list. `VALID_AGENT_TYPES` has exactly 9 entries. ✓

### 5-G  `app/api/v1/config.py`

```python
router = APIRouter(prefix="/config", dependencies=[Depends(require_api_key)])
```

**GET `/config`:**
- `select(CompanyConfig).limit(1)` → `_row(company)` or 404.

**PUT `/config` (partial update):**
Body: `dict = Body(...)`. Iterate over keys, `setattr(company, key, value)` if `hasattr(company, key)`.
- `await db.flush(); await db.refresh(company)`; return `_row(company)`.
- If no company exists: 404.

### 5-H  `app/api/v1/social.py`

```python
router = APIRouter(prefix="/social", dependencies=[Depends(require_api_key)])
```

**GET `/social/posts?status=&limit=50`:**
- `select(SocialPost)`, optional `where(SocialPost.status == status)`, `.limit(limit)`
- Return `[_row(p) for p in posts]`

### 5-I  `app/api/v1/finance.py`

**Do NOT put `require_api_key` on the Stripe webhook** — it's called by Stripe's servers, not our dashboard. Use `require_api_key` on all other endpoints individually (or use a sub-router).

```python
router = APIRouter(prefix="/finance")
```

**GET `/finance/summary` (auth required):**
```python
@router.get("/summary", dependencies=[Depends(require_api_key)])
async def finance_summary(db: AsyncSession = Depends(get_db)):
    snap = (await db.execute(
        select(RevenueSnapshot).order_by(RevenueSnapshot.snapshot_date.desc()).limit(1)
    )).scalar_one_or_none()
    if snap is None:
        return {"mrr_cents": 0, "arr_cents": 0, "active_subscribers": 0, 
                "stripe_balance_cents": 0, "last_snapshot_date": None}
    return {
        "mrr_cents": snap.mrr_cents,
        "arr_cents": snap.arr_cents,
        "active_subscribers": snap.active_subscribers,
        "stripe_balance_cents": snap.stripe_balance_cents,
        "last_snapshot_date": str(snap.snapshot_date),
    }
```

**GET `/finance/revenue?limit=30` (auth required):**
- `select(RevenueSnapshot).order_by(RevenueSnapshot.snapshot_date.desc()).limit(limit)` → `[_row(s) for s in snaps]`

**GET `/finance/expenses?category=&limit=50` (auth required):**
- Optional filter by category; return list.

**GET `/finance/events?limit=50` (auth required):**
- `select(StripeEvent).limit(limit)` → list.

**POST `/finance/stripe/webhook` (NO auth dependency — Stripe-verified instead):**
```python
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    
    try:
        import stripe as stripe_lib
        stripe_lib.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    
    return {"received": True}
```

**Gotcha:** `test_stripe_webhook_missing_secret` sends NO `auth_headers`. If we used `require_api_key` on this endpoint, it would return 401 instead of 500. The webhook must be unauthenticated. ✓

**Gotcha:** `test_stripe_webhook_invalid_signature` sets `settings.stripe_webhook_secret = "whsec_test"` and sends a bad sig. `stripe.Webhook.construct_event` raises `SignatureVerificationError`. We catch all exceptions → 400. ✓

### 5-J  `app/api/v1/memory.py`

```python
router = APIRouter(prefix="/memory", dependencies=[Depends(require_api_key)])
```

**POST `/memory` → 201:**
Body: `{category: str, title: str, content: str, tags?: list[str]}` via Pydantic model.
- `await store_memory(db, category=body.category, title=body.title, content=body.content, tags=body.tags)`
- Return `_row(entry)` with `status_code=201`.

**GET `/memory?q=&category=&limit=50`:**
- If `q`: `await search_memory(db, q, n_results=limit)` → return list of dicts.
- Else: `await list_memories(db, category=category, limit=limit)` → `[_row(m) for m in entries]`.

**Gotcha:** `test_list_memory_empty` does NOT include `mock_chroma` fixture, so `list_memories` must NOT call `get_collection()`. ✓

---

## Phase 6 — `app/main.py`

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health, dashboard, tasks, agents, config, social, finance, memory

app = FastAPI(title="Polsia AI Business Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")
app.include_router(social.router, prefix="/api/v1")
app.include_router(finance.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")


@app.websocket("/ws/activity")
async def ws_activity(websocket: WebSocket):
    from app.core.redis_client import get_redis
    await websocket.accept()
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe("polsia:activity")
    try:
        async for message in pubsub.listen():
            if message.get("type") == "message":
                await websocket.send_text(message["data"])
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe("polsia:activity")
```

**Gotcha:** Health router has no prefix in its definition (`router = APIRouter()`), so `app.include_router(health.router, prefix="/api/v1")` produces `GET /api/v1/health`. ✓

**Gotcha:** Dashboard, tasks, etc. routers have prefixes like `/dashboard`, `/tasks`. Combined with `prefix="/api/v1"` in `include_router`, paths become `/api/v1/dashboard/...`, `/api/v1/tasks/...`. ✓

---

## Complete File List

### Modified files (4)
```
docker-compose.yml                    — fix 3 context: ./backend → context: .
celery_app/celery_config.py           — timezone = "Asia/Kolkata"
scripts/seed_company.py               — TapReview company data
```

### Deleted files (1)
```
conftest.py                           — duplicate of tests/conftest.py
```

### New files (62)
```
.env

app/__init__.py
app/config.py
app/core/__init__.py
app/core/database.py
app/core/redis_client.py
app/core/events.py
app/core/chroma_client.py
app/core/security.py

app/models/__init__.py
app/models/company.py
app/models/task.py
app/models/activity.py
app/models/memory.py
app/models/social.py
app/models/outreach.py
app/models/ads.py
app/models/competitors.py
app/models/finance.py
app/models/reports.py

app/services/__init__.py
app/services/task_service.py
app/services/activity_service.py
app/services/company_service.py
app/services/memory_service.py
app/services/report_service.py

app/agents/__init__.py
app/agents/base_agent.py
app/agents/crew_factory.py
app/agents/orchestrator/__init__.py
app/agents/orchestrator/agent.py
app/agents/social_media/__init__.py
app/agents/social_media/agent.py
app/agents/competitor_research/__init__.py
app/agents/competitor_research/agent.py
app/agents/business_planning/__init__.py
app/agents/business_planning/agent.py
app/agents/email_outreach/__init__.py
app/agents/email_outreach/agent.py
app/agents/customer_support/__init__.py
app/agents/customer_support/agent.py
app/agents/ads_management/__init__.py
app/agents/ads_management/agent.py
app/agents/code_generation/__init__.py
app/agents/code_generation/agent.py
app/agents/finance/__init__.py
app/agents/finance/agent.py

app/api/__init__.py
app/api/v1/__init__.py
app/api/v1/health.py
app/api/v1/dashboard.py
app/api/v1/tasks.py
app/api/v1/agents.py
app/api/v1/config.py
app/api/v1/social.py
app/api/v1/finance.py
app/api/v1/memory.py

app/main.py
```

---

## Consolidated Gotcha List

1. **Duplicate conftest** — Delete `/polsia/conftest.py`; keep `tests/conftest.py`. Both are identical; pytest loads both because it always scans for root conftest files regardless of `testpaths`.

2. **No JSONB or ARRAY in models** — Use `sa.JSON` everywhere. The unit test DB is SQLite.

3. **`memory.tags` uses `sa.JSON`**, not `postgresql.ARRAY(String)` — the alembic migration can keep ARRAY for real Postgres, but the ORM model must use JSON.

4. **`memory_service` re-exports `get_collection`** at module level via `from app.core.chroma_client import get_collection`. The conftest patches `app.services.memory_service.get_collection`. If this line is missing, patching fails.

5. **`get_collection` is lazy** — Never `import chromadb` at module level. The import lives inside `get_collection()`'s function body.

6. **`require_api_key` reads `settings.api_key` dynamically** — The test sets `settings.api_key = "test-key"`. Security must not cache the value at import time.

7. **`Header(default=None)` not `Header(...)`** — Missing API key must return 401 (not 422). `Header(...)` (required) returns 422 when missing.

8. **Stripe webhook has NO `require_api_key`** — `test_stripe_webhook_missing_secret` sends no auth header; expects 500. Adding `require_api_key` would cause 401 instead.

9. **`call_claude` mock checks `os.getenv("CLAUDE_CLI_MOCK")`** directly (not `settings.claude_cli_mock`). The test uses `monkeypatch.setenv("CLAUDE_CLI_MOCK", "true")`. Both approaches actually work (settings reads from env), but `os.getenv` is safer for test isolation.

10. **`CLAUDE_CLI_MOCK_RESPONSE` value structure**: It is a JSON string `{"result": "..."}`. `call_claude` returns `json.loads(raw)["result"]` — a string. `call_claude_json` calls `json.loads(that_string)` to get a dict.

11. **`run_agent_for_task` error message**: `f"Unknown agent type: {agent_type}"` — contains `"Unknown agent"` which matches `pytest.raises(ValueError, match="Unknown agent")`. ✓

12. **9 agents, not 10** — CLAUDE.md mentions a "Deployment" agent, but VALID_AGENT_TYPES and `test_get_agent_status` (`assert len(data) == 9`) both require exactly 9. No deployment agent.

13. **`get_db` auto-commits** — `get_db()` calls `await session.commit()` on successful yield. API handlers use `await db.flush()` + `await db.refresh(obj)` if they need server-generated values before returning. Never call `await db.commit()` in API handlers.

14. **CLAUDE.md says `cd backend`** — there is no `backend/` subdirectory. Run all pytest commands from the project root `/Users/gauravshewale/Development/business/NFC/polsia`.

15. **`alembic/versions/0001_initial_schema.py` uses `postgresql.JSONB` and `postgresql.ARRAY`** — do NOT update the migration to match the ORM models. The migration is for real Postgres; the ORM models use dialect-agnostic types. They intentionally diverge.

16. **`activity_service` publishes to redis before the session commits** — The publish happens after `flush()`. This means the activity event is broadcast even if the outer transaction later rolls back. This is acceptable for the project's purposes and matches what the tests expect.

17. **`test_finance_revenue_returns_snapshots` checks most-recent-first**: `data[0]["mrr_cents"] >= data[1]["mrr_cents"]`. Query must `ORDER BY snapshot_date DESC`. ✓
