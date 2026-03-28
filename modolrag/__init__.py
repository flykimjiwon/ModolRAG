"""ModolRAG — PostgreSQL-native hybrid RAG engine.

Usage (3 lines):
    from modolrag import ModolRAG

    rag = ModolRAG("postgresql://localhost:5432/modolrag")
    rag.ingest("report.pdf")
    answer = rag.ask("매출 현황은?")
"""

__version__ = "0.1.0"

import asyncio
import mimetypes
import os
import uuid
from pathlib import Path


def _run(coro):
    """Run async coroutine from sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class ModolRAG:
    """High-level facade for ModolRAG.

    Makes the entire RAG pipeline accessible in 3 lines of code.
    Handles DB connection, schema init, embedding, and search automatically.

    Examples:
        # Basic usage
        rag = ModolRAG()
        rag.ingest("report.pdf")
        results = rag.search("인증 방법")
        answer = rag.ask("인증 방법은?")

        # With explicit DB
        rag = ModolRAG(db="postgresql://user:pass@host:5432/mydb")

        # With OpenAI embeddings
        rag = ModolRAG(embedding_provider="openai", openai_api_key="sk-...")

        # Async usage
        async with ModolRAG() as rag:
            await rag.aingest("report.pdf")
            answer = await rag.aask("질문")
    """

    def __init__(
        self,
        db: str | None = None,
        *,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
        ollama_base_url: str | None = None,
        openai_api_key: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        auto_init: bool = True,
    ):
        """Initialize ModolRAG.

        Args:
            db: PostgreSQL connection string. Defaults to MODOLRAG_POSTGRES_URI env var
                or postgresql://localhost:5432/modolrag.
            embedding_provider: "ollama", "openai", or "local". Default: "ollama".
            embedding_model: Model name. Default depends on provider.
            ollama_base_url: Ollama server URL. Default: http://localhost:11434.
            openai_api_key: OpenAI API key (required if provider is "openai").
            llm_provider: "ollama" or "openai". Default: "ollama".
            llm_model: LLM model name. Default: "llama3".
            chunk_size: Text chunk size in characters. Default: 512.
            chunk_overlap: Overlap between chunks. Default: 51.
            auto_init: Automatically initialize DB schema on first use. Default: True.
        """
        # Set env vars for overrides
        if db:
            os.environ["MODOLRAG_POSTGRES_URI"] = db
        if embedding_provider:
            os.environ["MODOLRAG_EMBEDDING_PROVIDER"] = embedding_provider
        if embedding_model:
            os.environ["MODOLRAG_EMBEDDING_MODEL"] = embedding_model
        if ollama_base_url:
            os.environ["MODOLRAG_OLLAMA_BASE_URL"] = ollama_base_url
        if openai_api_key:
            os.environ["MODOLRAG_OPENAI_API_KEY"] = openai_api_key
        if llm_provider:
            os.environ["MODOLRAG_LLM_PROVIDER"] = llm_provider
        if llm_model:
            os.environ["MODOLRAG_LLM_MODEL"] = llm_model
        if chunk_size:
            os.environ["MODOLRAG_CHUNK_SIZE"] = str(chunk_size)
        if chunk_overlap:
            os.environ["MODOLRAG_CHUNK_OVERLAP"] = str(chunk_overlap)

        self._initialized = False
        self._auto_init = auto_init

    async def _ensure_init(self):
        """Initialize DB schema if not done yet."""
        if not self._initialized and self._auto_init:
            try:
                from modolrag.db import init_schema
                await init_schema()
                self._initialized = True
            except Exception as e:
                raise ConnectionError(
                    f"PostgreSQL 연결 실패: {e}\n\n"
                    "해결 방법:\n"
                    "  1. PostgreSQL이 실행 중인지 확인: docker ps\n"
                    "  2. Docker로 빠르게 시작: modolrag quickstart\n"
                    "  3. 직접 시작: docker compose up -d\n"
                    "  4. DB URI 확인: ModolRAG(db='postgresql://...')\n"
                ) from e

    # ─── Sync API (편의용) ──────────────────────────────────

    def ingest(self, file_path: str, collection: str | None = None) -> str:
        """Upload and process a document. Returns document ID.

        Args:
            file_path: Path to file (PDF, DOCX, XLSX, PPTX, MD, TXT).
            collection: Optional collection name to add the document to.
        """
        return _run(self.aingest(file_path, collection))

    def search(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",
        collection: str | None = None,
    ) -> list[dict]:
        """Search for relevant document chunks.

        Args:
            query: Search query text.
            top_k: Number of results to return.
            mode: "hybrid" (all 3), "vector" (semantic), "fts" (keyword), "graph" (relations).
            collection: Optional collection to search within.
        """
        return _run(self.asearch(query, top_k, mode, collection))

    def ask(
        self,
        question: str,
        top_k: int = 5,
        mode: str = "hybrid",
        collection: str | None = None,
        stream: bool = False,
    ) -> str:
        """Ask a question and get an AI-generated answer based on your documents.

        Args:
            question: Your question.
            top_k: Number of context chunks to use.
            mode: Search mode.
            collection: Optional collection to search within.
            stream: If True, prints tokens as they arrive and returns full text.
        """
        return _run(self.aask(question, top_k, mode, collection, stream))

    def close(self):
        """Close database connections."""
        _run(self.aclose())

    # ─── Async API (프로덕션/서버용) ────────────────────────

    async def aingest(self, file_path: str, collection: str | None = None) -> str:
        """Async version of ingest()."""
        await self._ensure_init()

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/octet-stream"

        from modolrag.db import execute

        doc_id = str(uuid.uuid4())
        file_size = path.stat().st_size

        await execute(
            """INSERT INTO modolrag_documents (id, file_name, original_name, file_size, mime_type, status)
            VALUES ($1::uuid, $2, $3, $4, $5, 'uploaded')""",
            doc_id, str(path), path.name, file_size, mime_type,
        )

        from modolrag.core.pipeline import ingest_document
        await ingest_document(doc_id, str(path), mime_type)

        # Add to collection if specified
        if collection:
            await self._ensure_collection(collection, doc_id)

        return doc_id

    async def asearch(
        self,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",
        collection: str | None = None,
    ) -> list[dict]:
        """Async version of search()."""
        await self._ensure_init()

        from modolrag.config import get_settings
        from modolrag.core.embedder import get_embedder
        from modolrag.core.hybrid_search import hybrid_search

        settings = get_settings()
        embedder = get_embedder(settings)
        query_embedding = await embedder.embed(query)

        document_ids = None
        if collection:
            document_ids = await self._get_collection_doc_ids(collection)

        results = await hybrid_search(
            query_text=query,
            query_embedding=query_embedding,
            top_k=top_k,
            mode=mode,
            document_ids=document_ids,
        )

        return [
            {
                "content": r.content,
                "score": r.score,
                "file_name": r.original_name or r.file_name,
                "match_type": r.match_type,
                "document_id": r.document_id,
                "chunk_id": r.chunk_id,
            }
            for r in results
        ]

    async def aask(
        self,
        question: str,
        top_k: int = 5,
        mode: str = "hybrid",
        collection: str | None = None,
        stream: bool = False,
    ) -> str:
        """Async version of ask()."""
        await self._ensure_init()

        # 1. Search for context
        results = await self.asearch(question, top_k, mode, collection)

        if not results:
            return "관련 문서를 찾을 수 없습니다. 먼저 문서를 업로드해주세요."

        # 2. Build context
        context_parts = []
        for i, r in enumerate(results, 1):
            source = f" ({r['file_name']})" if r.get("file_name") else ""
            context_parts.append(f"[{i}]{source} {r['content']}")
        context = "\n\n".join(context_parts)

        # 3. Generate answer
        from modolrag.config import get_settings
        from modolrag.core.llm import get_llm

        settings = get_settings()
        llm = get_llm(settings)

        system_prompt = (
            "You are a helpful assistant. Answer the user's question based on the provided context. "
            "If the context doesn't contain enough information, say so. "
            "Always cite which source [number] you used. Respond in the same language as the question."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

        if stream:
            full_text = ""
            async for token in llm.generate_stream(system_prompt, user_prompt):
                print(token, end="", flush=True)
                full_text += token
            print()
            return full_text
        else:
            return await llm.generate(system_prompt, user_prompt)

    async def aclose(self):
        """Async close database connections."""
        from modolrag.db import close_pool
        await close_pool()

    async def _ensure_collection(self, name: str, doc_id: str):
        """Add document to collection, creating if needed."""
        from modolrag.db import fetchrow, execute

        row = await fetchrow(
            "SELECT id FROM modolrag_collections WHERE name = $1", name
        )
        if row:
            coll_id = str(row["id"])
        else:
            coll_id = str(uuid.uuid4())
            await execute(
                "INSERT INTO modolrag_collections (id, name) VALUES ($1::uuid, $2)",
                coll_id, name,
            )

        await execute(
            """INSERT INTO modolrag_collection_documents (collection_id, document_id)
            VALUES ($1::uuid, $2::uuid) ON CONFLICT DO NOTHING""",
            coll_id, doc_id,
        )

    async def _get_collection_doc_ids(self, name: str) -> list[str] | None:
        """Get document IDs in a collection."""
        from modolrag.db import fetch

        rows = await fetch(
            """SELECT cd.document_id FROM modolrag_collection_documents cd
            JOIN modolrag_collections c ON c.id = cd.collection_id
            WHERE c.name = $1""",
            name,
        )
        if not rows:
            return None
        return [str(r["document_id"]) for r in rows]

    # ─── Context Manager ────────────────────────────────────

    async def __aenter__(self):
        await self._ensure_init()
        return self

    async def __aexit__(self, *args):
        await self.aclose()

    def __enter__(self):
        _run(self._ensure_init())
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self):
        from modolrag.config import get_settings
        s = get_settings()
        return f"ModolRAG(db='{s.POSTGRES_URI}', embedding='{s.EMBEDDING_PROVIDER}/{s.EMBEDDING_MODEL}')"
