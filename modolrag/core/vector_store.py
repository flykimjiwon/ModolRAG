"""pgvector-based vector store operations."""
from __future__ import annotations

import uuid

from modolrag.db import fetch, fetchrow, execute


def _format_halfvec(embedding: list[float]) -> str:
    """Format embedding as PostgreSQL halfvec literal."""
    return "[" + ",".join(str(v) for v in embedding) + "]"


async def upsert_chunks(
    document_id: str,
    chunks: list[dict],  # [{content, embedding, chunk_index, chunk_level, parent_chunk_id, metadata}]
) -> int:
    """Insert or update document chunks with embeddings. Returns count inserted."""
    count = 0
    for chunk in chunks:
        chunk_id = str(uuid.uuid4())
        embedding_str = _format_halfvec(chunk["embedding"]) if chunk.get("embedding") else None

        await execute(
            """
            INSERT INTO modolrag_document_chunks
                (id, document_id, content, embedding, chunk_index, chunk_level, parent_chunk_id, metadata)
            VALUES ($1, $2::uuid, $3, $4::halfvec, $5, $6, $7::uuid, $8::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata
            """,
            chunk_id, document_id, chunk["content"],
            embedding_str, chunk.get("chunk_index", 0),
            chunk.get("chunk_level", 0), chunk.get("parent_chunk_id"),
            chunk.get("metadata", "{}")
        )
        count += 1
    return count


async def search_similar(
    query_embedding: list[float],
    top_k: int = 20,
    threshold: float = 0.7,
    document_ids: list[str] | None = None,
) -> list[dict]:
    """Search for similar chunks using cosine distance. Returns ranked results."""
    embedding_str = _format_halfvec(query_embedding)

    if document_ids:
        rows = await fetch(
            """
            SELECT
                c.id, c.document_id, c.content, c.chunk_index, c.metadata,
                1 - (c.embedding <=> $1::halfvec) AS similarity,
                d.file_name, d.original_name
            FROM modolrag_document_chunks c
            JOIN modolrag_documents d ON c.document_id = d.id
            WHERE c.embedding IS NOT NULL AND c.document_id = ANY($3::uuid[])
            ORDER BY c.embedding <=> $1::halfvec
            LIMIT $2
            """,
            embedding_str, top_k, document_ids
        )
    else:
        rows = await fetch(
            """
            SELECT
                c.id, c.document_id, c.content, c.chunk_index, c.metadata,
                1 - (c.embedding <=> $1::halfvec) AS similarity,
                d.file_name, d.original_name
            FROM modolrag_document_chunks c
            JOIN modolrag_documents d ON c.document_id = d.id
            WHERE c.embedding IS NOT NULL
            ORDER BY c.embedding <=> $1::halfvec
            LIMIT $2
            """,
            embedding_str, top_k
        )

    results = []
    for row in rows:
        sim = float(row["similarity"]) if row["similarity"] else 0.0
        if sim >= threshold:
            results.append({
                "chunk_id": str(row["id"]),
                "document_id": str(row["document_id"]),
                "content": row["content"],
                "similarity": sim,
                "chunk_index": row["chunk_index"],
                "metadata": row["metadata"],
                "file_name": row["file_name"],
                "original_name": row["original_name"],
            })
    return results


async def delete_by_document(document_id: str) -> int:
    """Delete all chunks for a document. Returns deleted count."""
    result = await execute(
        "DELETE FROM modolrag_document_chunks WHERE document_id = $1::uuid",
        document_id
    )
    # asyncpg returns "DELETE N"
    return int(result.split()[-1]) if result else 0


async def get_chunk_by_id(chunk_id: str) -> dict | None:
    """Get a single chunk by ID."""
    row = await fetchrow(
        """
        SELECT c.*, d.file_name, d.original_name
        FROM modolrag_document_chunks c
        JOIN modolrag_documents d ON c.document_id = d.id
        WHERE c.id = $1::uuid
        """,
        chunk_id
    )
    if row is None:
        return None
    return dict(row)


async def get_chunks_by_document(document_id: str) -> list[dict]:
    """Get all chunks for a document, ordered by index."""
    rows = await fetch(
        """
        SELECT * FROM modolrag_document_chunks
        WHERE document_id = $1::uuid
        ORDER BY chunk_index
        """,
        document_id
    )
    return [dict(row) for row in rows]
