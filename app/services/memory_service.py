"""Memory service — dual-write to Postgres and ChromaDB."""
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chroma_client import get_collection  # re-export for patching
from app.models.memory import MemoryEntry


async def store_memory(
    db: AsyncSession,
    category: str,
    title: str,
    content: str,
    source: str | None = None,
    tags: list[str] | None = None,
) -> MemoryEntry:
    chroma_id = str(uuid4())
    entry = MemoryEntry(
        category=category,
        title=title,
        content=content,
        source=source,
        tags=tags or [],
        chroma_id=chroma_id,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)

    get_collection().add(
        documents=[content],
        metadatas=[{"category": category, "title": title, "source": source or ""}],
        ids=[chroma_id],
    )
    return entry


async def search_memory(
    db: AsyncSession, query: str, n_results: int = 5
) -> list[dict]:
    results = get_collection().query(query_texts=[query], n_results=n_results)
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    return [
        {
            "content": doc,
            "category": meta.get("category"),
            "title": meta.get("title"),
            "source": meta.get("source"),
        }
        for doc, meta in zip(documents, metadatas)
    ]


async def list_memories(
    db: AsyncSession, category: str | None = None, limit: int = 50
) -> list[MemoryEntry]:
    stmt = select(MemoryEntry)
    if category is not None:
        stmt = stmt.where(MemoryEntry.category == category)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
