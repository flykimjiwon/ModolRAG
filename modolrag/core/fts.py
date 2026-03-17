"""Full-text search using PostgreSQL tsvector + GIN."""
from __future__ import annotations
from modolrag.db import fetch


async def search_fts(
    query_text: str,
    top_k: int = 20,
    language: str = "english",
) -> list[dict]:
    """Full-text search using websearch_to_tsquery.
    
    The fts column is GENERATED from content, so no manual update needed.
    Uses ts_rank_cd with normalization=32 for BM25-like scoring.
    """
    rows = await fetch(
        """
        SELECT 
            c.id, c.document_id, c.content, c.chunk_index, c.metadata,
            ts_rank_cd(c.fts, websearch_to_tsquery($1, $2), 32) AS rank,
            d.file_name, d.original_name
        FROM modolrag_document_chunks c
        JOIN modolrag_documents d ON c.document_id = d.id
        WHERE c.fts @@ websearch_to_tsquery($1, $2)
        ORDER BY rank DESC
        LIMIT $3
        """,
        language, query_text, top_k
    )
    
    return [
        {
            "chunk_id": str(row["id"]),
            "document_id": str(row["document_id"]),
            "content": row["content"],
            "rank": float(row["rank"]),
            "chunk_index": row["chunk_index"],
            "metadata": row["metadata"],
            "file_name": row["file_name"],
            "original_name": row["original_name"],
        }
        for row in rows
    ]


async def search_fts_simple(
    query_text: str,
    top_k: int = 20,
) -> list[dict]:
    """Full-text search using 'simple' config (no stemming — better for non-English)."""
    rows = await fetch(
        """
        SELECT 
            c.id, c.document_id, c.content, c.chunk_index, c.metadata,
            ts_rank_cd(c.fts, plainto_tsquery('simple', $1), 32) AS rank,
            d.file_name, d.original_name
        FROM modolrag_document_chunks c
        JOIN modolrag_documents d ON c.document_id = d.id
        WHERE c.fts @@ plainto_tsquery('simple', $1)
        ORDER BY rank DESC
        LIMIT $2
        """,
        query_text, top_k
    )
    
    return [
        {
            "chunk_id": str(row["id"]),
            "document_id": str(row["document_id"]),
            "content": row["content"],
            "rank": float(row["rank"]),
            "chunk_index": row["chunk_index"],
            "metadata": row["metadata"],
            "file_name": row["file_name"],
            "original_name": row["original_name"],
        }
        for row in rows
    ]
