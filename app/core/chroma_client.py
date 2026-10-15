from app.config import settings


def get_collection():
    """Lazy-import chromadb so unit tests can import this module without chromadb installed."""
    import chromadb  # noqa: PLC0415 — intentional lazy import
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return client.get_or_create_collection("polsia_memory")
