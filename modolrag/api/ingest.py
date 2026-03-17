"""Document ingestion endpoints."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException
from modolrag.api.auth import require_api_key
from modolrag.db import execute, fetch, fetchrow

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _: str = Depends(require_api_key),
):
    """Upload a document for processing."""
    doc_id = str(uuid.uuid4())
    content = await file.read()
    file_size = len(content)
    mime_type = file.content_type or "application/octet-stream"

    # Determine category from mime type
    category_map = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "word",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "powerpoint",
        "text/markdown": "markdown",
        "text/plain": "text",
    }
    category = category_map.get(mime_type, "other")

    # Save to temp file and create DB record
    import tempfile, os
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename or "upload")
    with open(tmp_path, "wb") as f:
        f.write(content)

    await execute(
        """
        INSERT INTO modolrag_documents (id, file_name, original_name, file_size, mime_type, category, status)
        VALUES ($1::uuid, $2, $3, $4, $5, $6, 'uploaded')
        """,
        doc_id, tmp_path, file.filename or "unknown", file_size, mime_type, category
    )

    # Trigger async ingestion pipeline (parse → chunk → embed → store → graph)
    from modolrag.core.pipeline import ingest_document as run_pipeline
    background_tasks.add_task(run_pipeline, doc_id, tmp_path, mime_type)

    return {"document_id": doc_id, "status": "processing", "file_name": file.filename}


@router.get("/documents")
async def list_documents(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _: str = Depends(require_api_key),
):
    """List all documents with optional status filter."""
    if status:
        rows = await fetch(
            "SELECT id, file_name, original_name, file_size, mime_type, category, status, chunk_count, created_at FROM modolrag_documents WHERE status = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
            status, limit, offset
        )
    else:
        rows = await fetch(
            "SELECT id, file_name, original_name, file_size, mime_type, category, status, chunk_count, created_at FROM modolrag_documents ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, offset
        )
    return {"documents": [dict(r) for r in rows], "count": len(rows)}


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, _: str = Depends(require_api_key)):
    """Get document details."""
    row = await fetchrow(
        "SELECT * FROM modolrag_documents WHERE id = $1::uuid", doc_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return dict(row)


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, _: str = Depends(require_api_key)):
    """Delete a document and all its chunks/graph data."""
    row = await fetchrow("SELECT id FROM modolrag_documents WHERE id = $1::uuid", doc_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    await execute("DELETE FROM modolrag_documents WHERE id = $1::uuid", doc_id)
    return {"deleted": True, "document_id": doc_id}
