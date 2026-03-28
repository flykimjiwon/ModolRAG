"""Collection management endpoints — group documents into searchable sets."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from modolrag.api.auth import require_api_key
from modolrag.db import execute, fetch, fetchrow

router = APIRouter(prefix="/api", tags=["collections"])


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Unique collection name")
    description: str = Field("", description="What this collection is for")

    model_config = {"json_schema_extra": {"example": {"name": "Product Docs", "description": "All product documentation"}}}


class CollectionDocuments(BaseModel):
    document_ids: list[str] = Field(..., description="List of document UUIDs to add/remove")


@router.post("/collections", summary="Create a collection")
async def create_collection(body: CollectionCreate, _: str = Depends(require_api_key)):
    """Create a new document collection. Use collections to scope search to specific document sets."""
    coll_id = str(uuid.uuid4())
    try:
        await execute(
            "INSERT INTO modolrag_collections (id, name, description) VALUES ($1::uuid, $2, $3)",
            coll_id, body.name, body.description,
        )
    except Exception:
        raise HTTPException(status_code=409, detail=f"Collection '{body.name}' already exists")
    return {"id": coll_id, "name": body.name, "description": body.description}


@router.get("/collections", summary="List collections")
async def list_collections(_: str = Depends(require_api_key)):
    """List all collections with document counts."""
    rows = await fetch(
        """
        SELECT c.id, c.name, c.description, c.created_at,
               COUNT(cd.document_id) AS document_count
        FROM modolrag_collections c
        LEFT JOIN modolrag_collection_documents cd ON c.id = cd.collection_id
        GROUP BY c.id
        ORDER BY c.name
        """
    )
    return {"collections": [dict(r) for r in rows]}


@router.get("/collections/{collection_id}", summary="Get collection details")
async def get_collection(collection_id: str, _: str = Depends(require_api_key)):
    """Get collection details with its document list."""
    coll = await fetchrow("SELECT * FROM modolrag_collections WHERE id = $1::uuid", collection_id)
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")

    docs = await fetch(
        """
        SELECT d.id, d.original_name, d.mime_type, d.status, d.chunk_count, cd.added_at
        FROM modolrag_collection_documents cd
        JOIN modolrag_documents d ON cd.document_id = d.id
        WHERE cd.collection_id = $1::uuid
        ORDER BY cd.added_at DESC
        """,
        collection_id,
    )
    return {"collection": dict(coll), "documents": [dict(d) for d in docs]}


@router.delete("/collections/{collection_id}", summary="Delete a collection")
async def delete_collection(collection_id: str, _: str = Depends(require_api_key)):
    """Delete a collection. Documents are NOT deleted — only the grouping is removed."""
    row = await fetchrow("SELECT id FROM modolrag_collections WHERE id = $1::uuid", collection_id)
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")
    await execute("DELETE FROM modolrag_collections WHERE id = $1::uuid", collection_id)
    return {"deleted": True}


@router.post("/collections/{collection_id}/documents", summary="Add documents to collection")
async def add_documents(collection_id: str, body: CollectionDocuments, _: str = Depends(require_api_key)):
    """Add one or more documents to a collection. Same document can belong to multiple collections."""
    coll = await fetchrow("SELECT id FROM modolrag_collections WHERE id = $1::uuid", collection_id)
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")

    added = 0
    for doc_id in body.document_ids:
        try:
            await execute(
                "INSERT INTO modolrag_collection_documents (collection_id, document_id) VALUES ($1::uuid, $2::uuid) ON CONFLICT DO NOTHING",
                collection_id, doc_id,
            )
            added += 1
        except Exception:
            pass
    return {"added": added, "collection_id": collection_id}


@router.delete("/collections/{collection_id}/documents", summary="Remove documents from collection")
async def remove_documents(collection_id: str, body: CollectionDocuments, _: str = Depends(require_api_key)):
    """Remove documents from a collection. Documents are NOT deleted — only unlinked."""
    removed = 0
    for doc_id in body.document_ids:
        result = await execute(
            "DELETE FROM modolrag_collection_documents WHERE collection_id = $1::uuid AND document_id = $2::uuid",
            collection_id, doc_id,
        )
        if result and "DELETE 1" in result:
            removed += 1
    return {"removed": removed, "collection_id": collection_id}
