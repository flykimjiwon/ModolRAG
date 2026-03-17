"""Search endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from modolrag.api.auth import require_api_key

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    mode: str = "hybrid"  # vector, fts, graph, hybrid
    namespace: str = "default"


@router.post("/search")
async def search(req: SearchRequest, _: str = Depends(require_api_key)):
    """Execute hybrid search."""
    from modolrag.core.embedder import get_embedder
    from modolrag.core.hybrid_search import hybrid_search

    embedder = get_embedder()
    query_embedding = await embedder.embed(req.query)

    results = await hybrid_search(
        query_text=req.query,
        query_embedding=query_embedding,
        top_k=req.top_k,
        mode=req.mode,
        namespace=req.namespace,
    )

    return {
        "results": [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "content": r.content,
                "score": r.score,
                "match_type": r.match_type,
                "file_name": r.file_name,
            }
            for r in results
        ],
        "query": req.query,
        "mode": req.mode,
        "count": len(results),
    }
