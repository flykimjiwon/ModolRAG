"""End-to-end document ingestion pipeline."""
from __future__ import annotations
import asyncio
import json
import traceback

from modolrag.db import execute, fetchrow
from modolrag.config import get_settings


async def ingest_document(document_id: str, file_path: str, mime_type: str) -> None:
    """Full ingestion pipeline for a single document.

    Steps:
    1. Parse document → text + pages
    2. Chunk text → chunks[]
    3. Embed chunks → chunks_with_embeddings[]
    4. Store in vector store
    5. Extract entities/relationships (LLM)
    6. Build graph nodes/edges
    7. Update document status
    """
    settings = get_settings()

    try:
        # Update status to processing
        await _update_status(document_id, "processing")

        # Step 1: Parse
        from modolrag.parsers import get_parser
        parser = get_parser(mime_type)
        parsed = parser.parse(file_path)

        await execute(
            "UPDATE modolrag_documents SET extracted_text = $1 WHERE id = $2::uuid",
            parsed.text[:100000], document_id  # Limit stored text
        )

        # Step 2: Chunk
        from modolrag.core.chunker import get_chunker
        chunker = get_chunker(
            "recursive",
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        chunks = chunker.chunk(parsed.text)

        if not chunks:
            await _update_status(document_id, "indexed", chunk_count=0)
            return

        # Step 3: Embed
        await _update_status(document_id, "vectorizing")
        from modolrag.core.embedder import get_embedder
        embedder = get_embedder(settings)

        texts = [c.content for c in chunks]
        total = len(texts)
        embeddings: list[list[float]] = []
        batch_size = 32

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await embedder.embed_batch(batch)
            embeddings.extend(batch_embeddings)
            # Update progress
            progress = min(((i + batch_size) / total) * 80, 80)  # 80% for embedding
            await execute(
                "UPDATE modolrag_documents SET vectorization_progress = $1 WHERE id = $2::uuid",
                progress, document_id
            )

        # Step 4: Store chunks in vector store
        from modolrag.core.vector_store import upsert_chunks
        chunk_data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_data.append({
                "content": chunk.content,
                "embedding": embedding,
                "chunk_index": chunk.chunk_index,
                "chunk_level": chunk.chunk_level,
                "parent_chunk_id": None,
                "metadata": json.dumps(chunk.metadata) if chunk.metadata else "{}",
            })

        await upsert_chunks(document_id, chunk_data)

        await execute(
            "UPDATE modolrag_documents SET vectorization_progress = 90, chunk_count = $1, embedding_model = $2 WHERE id = $3::uuid",
            len(chunks), settings.EMBEDDING_MODEL, document_id
        )

        # Step 5 & 6: Entity extraction + graph building (best-effort)
        try:
            from modolrag.core.extractor import extract_entities_and_relations
            from modolrag.core.graph_store import upsert_node, upsert_edge

            # Extract from first 5 chunks (limit LLM calls)
            sample_text = " ".join(texts[:5])[:4000]
            extraction = await extract_entities_and_relations(sample_text)

            # Build graph — embed entity names for graph search
            node_ids: dict[str, str] = {}
            entity_texts = [e.name + (": " + e.description if e.description else "") for e in extraction.entities]
            entity_embeddings = await embedder.embed_batch(entity_texts) if entity_texts else []

            for i, entity in enumerate(extraction.entities):
                node_id = await upsert_node(
                    namespace="default",
                    title=entity.name,
                    content=entity.description,
                    embedding=entity_embeddings[i] if i < len(entity_embeddings) else None,
                    node_type=entity.type,
                )
                node_ids[entity.name] = node_id

            for rel in extraction.relationships:
                src_id = node_ids.get(rel.subject)
                tgt_id = node_ids.get(rel.object)
                if src_id and tgt_id:
                    await upsert_edge(
                        namespace="default",
                        source_id=src_id,
                        target_id=tgt_id,
                        relation_type=rel.predicate,
                        weight=rel.confidence,
                    )
        except Exception:
            # Graph extraction is best-effort; don't fail the pipeline
            pass

        # Done
        await _update_status(document_id, "vectorized", chunk_count=len(chunks))
        await execute(
            "UPDATE modolrag_documents SET vectorization_progress = 100 WHERE id = $1::uuid",
            document_id
        )

    except Exception as e:
        await execute(
            "UPDATE modolrag_documents SET status = 'error', error_message = $1 WHERE id = $2::uuid",
            str(e)[:1000], document_id
        )


async def _update_status(document_id: str, status: str, chunk_count: int | None = None) -> None:
    if chunk_count is not None:
        await execute(
            "UPDATE modolrag_documents SET status = $1, chunk_count = $2, updated_at = now() WHERE id = $3::uuid",
            status, chunk_count, document_id
        )
    else:
        await execute(
            "UPDATE modolrag_documents SET status = $1, updated_at = now() WHERE id = $2::uuid",
            status, document_id
        )
