"""FastAPI application entry point."""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import agents, config, dashboard, finance, health, memory, social, tasks

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
    from app.core.redis_client import get_redis  # noqa: PLC0415 — lazy import avoids real Redis on startup

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
