"""API Key authentication."""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from modolrag.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """Validate X-API-Key header. Returns the key if valid."""
    settings = get_settings()
    valid_keys = [k.strip() for k in settings.API_KEYS.split(",") if k.strip()]
    
    # If no API keys configured, allow all requests
    if not valid_keys:
        return "no-auth"
    
    if api_key is None or api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
