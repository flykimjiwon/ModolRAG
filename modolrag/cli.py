"""CLI entry point for ModolRAG."""
import argparse
import asyncio
from typing import Optional

import uvicorn


def main():
    parser = argparse.ArgumentParser(
        description="ModolRAG — PostgreSQL-native hybrid RAG engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  modolrag serve                          Start server on port 8000
  modolrag serve --port 3000 --reload     Dev mode on port 3000
  modolrag init-db                        Initialize database schema
  modolrag ingest report.pdf              Ingest a document
  modolrag search "인증 방법"              Search documents
  modolrag ask "매출 현황은?"              Ask a question
  modolrag quickstart                     Auto-setup Docker + DB + Ollama
  modolrag status                         Check system status
        """,
    )
    subparsers = parser.add_subparsers(dest="command")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the ModolRAG server")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--reload", action="store_true")
    serve_parser.add_argument("--db", help="PostgreSQL URI (overrides MODOLRAG_POSTGRES_URI)")

    # init-db
    init_parser = subparsers.add_parser("init-db", help="Initialize database schema")
    init_parser.add_argument("--db", help="PostgreSQL URI")

    # ingest
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a document")
    ingest_parser.add_argument("file", help="Path to document file")
    ingest_parser.add_argument("--db", help="PostgreSQL URI")
    ingest_parser.add_argument("--collection", "-c", help="Add to collection")

    # search
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    search_parser.add_argument("--mode", "-m", default="hybrid", choices=["hybrid", "vector", "fts", "graph"])
    search_parser.add_argument("--collection", "-c", help="Search within collection")
    search_parser.add_argument("--db", help="PostgreSQL URI")

    # ask
    ask_parser = subparsers.add_parser("ask", help="Ask a question (RAG)")
    ask_parser.add_argument("question", help="Your question")
    ask_parser.add_argument("--top-k", "-k", type=int, default=5)
    ask_parser.add_argument("--mode", "-m", default="hybrid", choices=["hybrid", "vector", "fts", "graph"])
    ask_parser.add_argument("--collection", "-c", help="Search within collection")
    ask_parser.add_argument("--stream", "-s", action="store_true", help="Stream output")
    ask_parser.add_argument("--db", help="PostgreSQL URI")

    # quickstart
    subparsers.add_parser("quickstart", help="Auto-setup Docker + PostgreSQL + Ollama")

    # status
    subparsers.add_parser("status", help="Check system status")

    args = parser.parse_args()

    if args.command == "serve":
        if args.db:
            import os
            os.environ["MODOLRAG_POSTGRES_URI"] = args.db
        uvicorn.run(
            "modolrag.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    elif args.command == "init-db":
        asyncio.run(_init_db(args.db))
    elif args.command == "ingest":
        asyncio.run(_ingest_file(args.file, args.db, getattr(args, "collection", None)))
    elif args.command == "search":
        asyncio.run(_search(args.query, args.top_k, args.mode, getattr(args, "collection", None), args.db))
    elif args.command == "ask":
        asyncio.run(_ask(args.question, args.top_k, args.mode, getattr(args, "collection", None), args.stream, args.db))
    elif args.command == "quickstart":
        asyncio.run(_quickstart())
    elif args.command == "status":
        asyncio.run(_status())
    else:
        parser.print_help()


async def _init_db(db_uri: Optional[str] = None):
    """Initialize database schema."""
    if db_uri:
        import os
        os.environ["MODOLRAG_POSTGRES_URI"] = db_uri

    from modolrag.db import init_schema, close_pool
    try:
        await init_schema()
        print("Database schema initialized successfully.")
    finally:
        await close_pool()


async def _ingest_file(file_path: str, db_uri: Optional[str] = None, collection: Optional[str] = None):
    """Ingest a single file from CLI."""
    if db_uri:
        import os
        os.environ["MODOLRAG_POSTGRES_URI"] = db_uri

    from modolrag import ModolRAG
    rag = ModolRAG(auto_init=True)
    try:
        print(f"Ingesting {file_path}...")
        doc_id = await rag.aingest(file_path, collection)
        print(f"Done. Document ID: {doc_id}")
        if collection:
            print(f"Added to collection: {collection}")
    finally:
        await rag.aclose()


async def _search(query: str, top_k: int, mode: str, collection: Optional[str], db_uri: Optional[str]):
    """Search from CLI."""
    if db_uri:
        import os
        os.environ["MODOLRAG_POSTGRES_URI"] = db_uri

    from modolrag import ModolRAG
    rag = ModolRAG(auto_init=True)
    try:
        results = await rag.asearch(query, top_k, mode, collection)
        if not results:
            print("No results found.")
            return

        print(f"\n--- {len(results)} results for: \"{query}\" ---\n")
        for i, r in enumerate(results, 1):
            source = f" [{r.get('file_name', '')}]" if r.get("file_name") else ""
            score = f" (score: {r['score']:.4f})" if r.get("score") else ""
            match = f" [{r.get('match_type', '')}]" if r.get("match_type") else ""
            print(f"  {i}.{source}{match}{score}")
            content = r["content"][:200].replace("\n", " ")
            print(f"     {content}...")
            print()
    finally:
        await rag.aclose()


async def _ask(question: str, top_k: int, mode: str, collection: Optional[str], stream: bool, db_uri: Optional[str]):
    """Ask a question from CLI."""
    if db_uri:
        import os
        os.environ["MODOLRAG_POSTGRES_URI"] = db_uri

    from modolrag import ModolRAG
    rag = ModolRAG(auto_init=True)
    try:
        if stream:
            print()
            await rag.aask(question, top_k, mode, collection, stream=True)
        else:
            answer = await rag.aask(question, top_k, mode, collection)
            print(f"\n{answer}")
    finally:
        await rag.aclose()


async def _quickstart():
    """Auto-setup Docker + PostgreSQL + Ollama."""
    import shutil
    import subprocess

    print("=" * 50)
    print("  ModolRAG Quickstart")
    print("=" * 50)
    print()

    # 1. Check Docker
    docker = shutil.which("docker")
    if not docker:
        print("Docker not found.")
        print("  macOS: brew install --cask docker")
        print("  Linux: https://docs.docker.com/engine/install/")
        return

    # Check Docker is running
    result = subprocess.run(["docker", "info"], capture_output=True, timeout=10)
    if result.returncode != 0:
        print("Docker is not running. Please start Docker Desktop and try again.")
        return
    print("[1/4] Docker: running")

    # 2. Check/start PostgreSQL via docker compose
    compose_file = _find_compose_file()
    if compose_file:
        print("[2/4] Starting PostgreSQL via docker compose...")
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "up", "-d", "db"],
            capture_output=True, timeout=60,
        )
        # Wait for DB to be ready
        import time
        for attempt in range(15):
            check = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "exec", "-T", "db",
                 "pg_isready", "-U", "modolrag"],
                capture_output=True, timeout=10,
            )
            if check.returncode == 0:
                break
            time.sleep(2)
        print("[2/4] PostgreSQL: ready")
    else:
        print("[2/4] No docker-compose.yml found. Starting standalone PostgreSQL...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", "modolrag-db",
            "-e", "POSTGRES_DB=modolrag",
            "-e", "POSTGRES_USER=modolrag",
            "-e", "POSTGRES_PASSWORD=modolrag",
            "-p", "5432:5432",
            "pgvector/pgvector:pg15",
        ], capture_output=True, timeout=30)
        import time
        time.sleep(5)
        print("[2/4] PostgreSQL: started (port 5432)")

    # 3. Check Ollama
    ollama = shutil.which("ollama")
    if ollama:
        # Check if running
        import httpx
        try:
            httpx.get("http://localhost:11434/api/tags", timeout=5)
            print("[3/4] Ollama: running")
        except Exception:
            print("[3/4] Starting Ollama...")
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import time
            time.sleep(3)

        # Pull embedding model
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if "nomic-embed-text" not in (result.stdout or ""):
            print("     Pulling nomic-embed-text model...")
            subprocess.run(["ollama", "pull", "nomic-embed-text"], timeout=300)
        print("[3/4] Embedding model: ready")
    else:
        print("[3/4] Ollama not found (optional)")
        print("     Install: brew install ollama (macOS) / https://ollama.ai")
        print("     Or use OpenAI: export MODOLRAG_EMBEDDING_PROVIDER=openai")

    # 4. Initialize DB schema
    print("[4/4] Initializing database schema...")
    try:
        from modolrag.db import init_schema, close_pool
        await init_schema()
        await close_pool()
        print("[4/4] Database schema: ready")
    except Exception as e:
        print(f"[4/4] Schema init failed: {e}")
        print("     Check MODOLRAG_POSTGRES_URI setting")
        return

    print()
    print("=" * 50)
    print("  Setup complete!")
    print("=" * 50)
    print()
    print("  Start server:  modolrag serve")
    print("  Ingest file:   modolrag ingest report.pdf")
    print("  Search:        modolrag search \"your query\"")
    print("  Ask question:  modolrag ask \"your question\"")
    print("  Dashboard:     http://localhost:8000/dashboard")
    print()
    print("  Python:")
    print("    from modolrag import ModolRAG")
    print("    rag = ModolRAG()")
    print("    rag.ingest('report.pdf')")
    print("    answer = rag.ask('질문')")
    print()


async def _status():
    """Check system status."""
    import httpx

    print("ModolRAG Status Check")
    print("-" * 40)

    # PostgreSQL
    try:
        from modolrag.db import get_pool, fetchval, close_pool
        await get_pool()
        await fetchval("SELECT version()")
        doc_count = await fetchval("SELECT count(*) FROM modolrag_documents")
        chunk_count = await fetchval("SELECT count(*) FROM modolrag_document_chunks")
        node_count = await fetchval("SELECT count(*) FROM modolrag_graph_nodes")
        await close_pool()
        print("  PostgreSQL:  connected")
        print(f"  Documents:   {doc_count}")
        print(f"  Chunks:      {chunk_count}")
        print(f"  Graph nodes: {node_count}")
    except Exception as e:
        print(f"  PostgreSQL:  NOT connected ({e})")

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            models = [m["name"] for m in resp.json().get("models", [])]
            print(f"  Ollama:      running ({len(models)} models)")
            if "nomic-embed-text:latest" in models:
                print("  Embedding:   nomic-embed-text ready")
            else:
                print("  Embedding:   nomic-embed-text NOT found")
    except Exception:
        print("  Ollama:      NOT running")

    # Config
    from modolrag.config import get_settings
    s = get_settings()
    print(f"  DB URI:      {s.POSTGRES_URI}")
    print(f"  Embedding:   {s.EMBEDDING_PROVIDER}/{s.EMBEDDING_MODEL}")
    print(f"  LLM:         {s.LLM_PROVIDER}/{s.LLM_MODEL}")
    print(f"  Chunk size:  {s.CHUNK_SIZE} (overlap: {s.CHUNK_OVERLAP})")


def _find_compose_file():
    """Find docker-compose.yml in current or parent directories."""
    from pathlib import Path
    for name in ["docker-compose.yml", "docker-compose.yaml", "compose.yml"]:
        # Check current dir
        p = Path(name)
        if p.exists():
            return p
        # Check ModolRAG install dir
        pkg_dir = Path(__file__).parent.parent
        p = pkg_dir / name
        if p.exists():
            return p
    return None


if __name__ == "__main__":
    main()
