"""CLI entry point for ModolRAG."""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="ModolRAG — PostgreSQL-native hybrid RAG engine")
    subparsers = parser.add_subparsers(dest="command")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the ModolRAG server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # init-db command (placeholder)
    subparsers.add_parser("init-db", help="Initialize database schema")

    args = parser.parse_args()

    if args.command == "serve":
        uvicorn.run("modolrag.main:app", host=args.host, port=args.port, reload=args.reload)
    elif args.command == "init-db":
        print("Database initialization not yet implemented.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
