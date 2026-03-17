"""FastAPI application for ModolRAG."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(
    title="ModolRAG",
    description="PostgreSQL-native hybrid RAG engine with vector + full-text + knowledge graph search",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Mount dashboard static files if they exist
static_dir = Path(__file__).parent / "static"
if static_dir.exists() and any(static_dir.iterdir()):
    app.mount("/dashboard", StaticFiles(directory=str(static_dir), html=True), name="dashboard")
