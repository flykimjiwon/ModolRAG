"""CLI entry point for ModolRAG."""
import argparse
import asyncio
import sys
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
  modolrag init-db --db postgresql://...  With custom connection string
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

    # ingest (convenience)
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a document from CLI")
    ingest_parser.add_argument("file", help="Path to document file")
    ingest_parser.add_argument("--db", help="PostgreSQL URI")

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
        asyncio.run(_ingest_file(args.file, args.db))
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


async def _ingest_file(file_path: str, db_uri: Optional[str] = None):
    """Ingest a single file from CLI."""
    import os
    import mimetypes
    
    if db_uri:
        os.environ["MODOLRAG_POSTGRES_URI"] = db_uri
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    
    import uuid
    from modolrag.db import init_schema, execute, close_pool
    
    try:
        await init_schema()
        
        doc_id = str(uuid.uuid4())
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        await execute(
            """INSERT INTO modolrag_documents (id, file_name, original_name, file_size, mime_type, status)
            VALUES ($1::uuid, $2, $3, $4, $5, 'uploaded')""",
            doc_id, file_path, file_name, file_size, mime_type
        )
        
        from modolrag.core.pipeline import ingest_document
        print(f"Ingesting {file_name} ({mime_type})...")
        await ingest_document(doc_id, file_path, mime_type)
        print(f"Done. Document ID: {doc_id}")
    finally:
        await close_pool()


if __name__ == "__main__":
    main()
