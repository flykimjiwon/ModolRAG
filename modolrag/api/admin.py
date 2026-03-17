"""Admin and settings endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from modolrag.api.auth import require_api_key
from modolrag.db import fetchrow, execute

router = APIRouter(tags=["admin"])


@router.get("/health")
async def health():
    """Health check (no auth required)."""
    from modolrag import __version__
    return {"status": "ok", "version": __version__}


class SettingsUpdate(BaseModel):
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    embedding_model: str | None = None
    embedding_dimensions: int | None = None
    similarity_top_k: int | None = None
    similarity_threshold: float | None = None


@router.get("/api/settings")
async def get_settings(_: str = Depends(require_api_key)):
    """Get current settings."""
    row = await fetchrow("SELECT * FROM modolrag_settings LIMIT 1")
    return dict(row) if row else {}


@router.put("/api/settings")
async def update_settings(settings: SettingsUpdate, _: str = Depends(require_api_key)):
    """Update settings."""
    updates = {k: v for k, v in settings.model_dump().items() if v is not None}
    if not updates:
        return {"updated": False}

    set_clauses = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(updates.keys()))
    values = list(updates.values())

    await execute(
        f"UPDATE modolrag_settings SET {set_clauses}, updated_at = now()",
        *values
    )
    return {"updated": True, "fields": list(updates.keys())}
