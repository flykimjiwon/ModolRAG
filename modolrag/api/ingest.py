"""Document ingestion endpoints."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, Field
from modolrag.api.auth import require_api_key
from modolrag.db import execute, fetch, fetchrow

router = APIRouter(prefix="/api", tags=["documents"])


class IngestResponse(BaseModel):
    document_id: str = Field(..., description="UUID of the created document")
    status: str = Field(..., description="Processing status (uploaded → processing → vectorized)")
    file_name: str | None = Field(None, description="Original file name")

    model_config = {"json_schema_extra": {"example": {"document_id": "550e8400-e29b-41d4-a716-446655440000", "status": "processing", "file_name": "report.pdf"}}}


class DocumentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str | object  # UUID from DB
    original_name: str
    mime_type: str
    category: str
    status: str
    chunk_count: int
    file_size: int | None = None
    created_at: str | object | None = None  # datetime from DB


class DocumentListResponse(BaseModel):
    documents: list[dict]  # Raw dicts from DB — flexible schema
    count: int


@router.post("/ingest", response_model=IngestResponse, summary="Upload a document")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file (PDF, DOCX, XLSX, PPTX, MD, TXT)"),
    _: str = Depends(require_api_key),
):
    """Upload a document for ingestion. The file is parsed, chunked, embedded, and stored asynchronously.
    
    Processing pipeline: **Upload → Parse → Chunk → Embed → Store → Extract Entities → Build Graph**
    
    Track progress via `GET /api/documents/{id}` — check `status` and `vectorization_progress` fields.
    """
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


@router.get("/documents", response_model=DocumentListResponse, summary="List documents")
async def list_documents(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200, description="Max documents to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    _: str = Depends(require_api_key),
):
    """List all documents with optional status filter.
    
    Filter by status: `uploaded`, `processing`, `vectorizing`, `vectorized`, `error`
    """
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


@router.get("/documents/{doc_id}", summary="Get document details")
async def get_document(doc_id: str, _: str = Depends(require_api_key)):
    """Get full details for a single document including processing status, chunk count, and error messages."""
    row = await fetchrow(
        "SELECT * FROM modolrag_documents WHERE id = $1::uuid", doc_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return dict(row)


@router.delete("/documents/{doc_id}", summary="Delete a document")
async def delete_document(doc_id: str, _: str = Depends(require_api_key)):
    """Delete a document and all associated data (chunks, embeddings, graph entities). This action is irreversible."""
    row = await fetchrow("SELECT id FROM modolrag_documents WHERE id = $1::uuid", doc_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    await execute("DELETE FROM modolrag_documents WHERE id = $1::uuid", doc_id)
    return {"deleted": True, "document_id": doc_id}
