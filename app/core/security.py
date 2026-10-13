from fastapi import Header, HTTPException


async def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    from app.config import settings  # imported inside function to always read current value
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
