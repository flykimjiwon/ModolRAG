"""FastAPI application for ModolRAG."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from modolrag.api.middleware import setup_middleware
from modolrag.api import ingest, search, graph, admin

app = FastAPI(
    title="ModolRAG",
    description="PostgreSQL-native hybrid RAG engine with vector + full-text + knowledge graph search",
    version="0.1.0",
)

# Setup middleware (CORS, etc.)
setup_middleware(app)

# Register routers
app.include_router(admin.router)
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(graph.router)

# Mount dashboard static files if they exist
static_dir = Path(__file__).parent / "static"
if static_dir.exists() and any(static_dir.iterdir()):
    app.mount("/dashboard", StaticFiles(directory=str(static_dir), html=True), name="dashboard")
