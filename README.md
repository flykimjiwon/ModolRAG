# ModolRAG

**PostgreSQL-native Hybrid RAG Engine**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

ModolRAG is a lightweight, pip-installable RAG (Retrieval-Augmented Generation) engine that runs entirely on PostgreSQL. No Elasticsearch, no separate vector database, no graph database — just one PostgreSQL instance with pgvector.

```bash
pip install modolrag
modolrag serve --db postgresql://localhost:5432/modolrag
```

---

## Key Features

- **Hybrid Search** — Vector (pgvector HNSW) + Full-Text (tsvector GIN) + Knowledge Graph (recursive CTE), fused with Reciprocal Rank Fusion (RRF)
- **PostgreSQL-Only** — No Elasticsearch, no Pinecone, no Neo4j. One database, one backup, one connection pool
- **pip Installable** — `pip install modolrag && modolrag serve`. No Docker required for development
- **React SPA Dashboard** — Documents, Search, Graph visualization, Settings — served from FastAPI
- **Multiple Embedding Providers** — Ollama (local) + OpenAI (API) with adapter pattern
- **6 Document Parsers** — PDF, DOCX, XLSX, PPTX, Markdown, Plain Text (all MIT/BSD licensed)
- **Supabase Compatible** — Standard PostgreSQL with `modolrag_` prefixed tables
- **ModolAI Integration** — Designed as a standalone module that connects to ModolAI via HTTP API

---

## Architecture

```
Document → Parser → Chunker → Embedder ─→ PostgreSQL
 (PDF,DOCX,         (recursive,          ├── pgvector (HNSW Vector Search)
  XLSX,PPTX,         semantic,           ├── tsvector (GIN Full-Text Search)
  MD,TXT)            page)               └── Graph Tables (CTE Traversal)
                                                    ↓
                           Query → Embed → [Vector + FTS + Graph] → RRF Fusion → Results
```

### Search Pipeline

1. **Vector Search** — Query embedding vs chunk embeddings using cosine similarity (pgvector HNSW)
2. **Full-Text Search** — Keyword matching using PostgreSQL tsvector with `websearch_to_tsquery`
3. **Graph Search** — Entity-aware traversal: find seed entities → 2-hop BFS expansion → collect related chunks
4. **RRF Fusion** — `score = Σ 1/(k + rank_i)` where k=60, combining ranks from all three sources

---

## Quick Start

### Install

```bash
pip install modolrag
```

### Start Server

```bash
# Initialize database schema
modolrag init-db --db postgresql://user:pass@localhost:5432/modolrag

# Start server
modolrag serve --db postgresql://user:pass@localhost:5432/modolrag
```

### Ingest a Document

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "X-API-Key: your-key" \
  -F "file=@document.pdf"
# → {"document_id": "uuid", "status": "processing"}
```

### Search

```bash
curl -X POST http://localhost:8000/api/search \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "your question", "top_k": 5, "mode": "hybrid"}'
# → {"results": [...], "mode": "hybrid", "count": 5}
```

### Graph Data

```bash
curl http://localhost:8000/api/graph \
  -H "X-API-Key: your-key"
# → {"nodes": [...], "edges": [...]}
```

---

## Docker Quick Start

```bash
git clone https://github.com/your-org/ModolRAG.git
cd ModolRAG

# Start everything (PostgreSQL + Ollama + ModolRAG)
docker compose up -d

# Download embedding model (first time only)
docker compose exec ollama ollama pull nomic-embed-text

# Verify
curl http://localhost:8000/health
# → {"status": "ok", "version": "0.1.0", "docs": "/docs", ...}
```

### Services

| Service | Port | Description |
|---|---|---|
| **modolrag** | `8000` | RAG API + Dashboard + Swagger |
| **postgres** | `5432` | PostgreSQL 15 + pgvector |
| **ollama** | `11434` | Local embedding model |

### Without Ollama (using OpenAI)

```bash
# Start only PostgreSQL + ModolRAG
docker compose up -d postgres modolrag

# Configure OpenAI
MODOLRAG_EMBEDDING_PROVIDER=openai \
MODOLRAG_OPENAI_API_KEY=sk-xxx \
docker compose up -d modolrag
```

### Custom Configuration

Create a `.env` file in the project root:

```env
# Database
POSTGRES_PASSWORD=your-secure-password
PG_PORT=5432

# ModolRAG
MODOLRAG_PORT=8000
MODOLRAG_API_KEYS=key1,key2
MODOLRAG_EMBEDDING_PROVIDER=ollama
MODOLRAG_EMBEDDING_MODEL=nomic-embed-text

# OpenAI (if not using Ollama)
# MODOLRAG_EMBEDDING_PROVIDER=openai
# MODOLRAG_OPENAI_API_KEY=sk-xxx
```

### URLs

| URL | Description |
|---|---|
| `http://localhost:8000/dashboard` | Admin Dashboard (React SPA) |
| `http://localhost:8000/docs` | Swagger UI (interactive API testing) |
| `http://localhost:8000/redoc` | ReDoc (API documentation) |
| `http://localhost:8000/health` | Health check |

---

## Configuration

All settings via environment variables with `MODOLRAG_` prefix:

| Variable | Default | Description |
|---|---|---|
| `MODOLRAG_POSTGRES_URI` | `postgresql://localhost:5432/modolrag` | PostgreSQL connection string |
| `MODOLRAG_API_KEYS` | `""` (no auth) | Comma-separated API keys |
| `MODOLRAG_EMBEDDING_PROVIDER` | `ollama` | `ollama` or `openai` |
| `MODOLRAG_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `MODOLRAG_EMBEDDING_DIMENSIONS` | `768` | Embedding vector dimensions |
| `MODOLRAG_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `MODOLRAG_OPENAI_API_KEY` | `""` | OpenAI API key |
| `MODOLRAG_CHUNK_SIZE` | `512` | Chunk size in characters |
| `MODOLRAG_CHUNK_OVERLAP` | `51` | Overlap between chunks |
| `MODOLRAG_SIMILARITY_TOP_K` | `5` | Number of results to return |
| `MODOLRAG_SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity score |

---

## Search Modes

| Mode | Description | Best For |
|---|---|---|
| `vector` | Semantic similarity search via pgvector HNSW | "Find documents about X" |
| `fts` | Keyword matching via PostgreSQL tsvector | Exact terms, names, codes |
| `graph` | Entity-aware graph traversal (2-hop BFS) | "How is X related to Y?" |
| `hybrid` | All three fused with RRF (default) | General purpose — best quality |

---

## Project Structure

```
ModolRAG/
├── modolrag/
│   ├── __init__.py          # Package version
│   ├── main.py              # FastAPI app + static serving
│   ├── config.py            # pydantic-settings configuration
│   ├── cli.py               # CLI: serve, init-db, ingest
│   ├── api/
│   │   ├── auth.py          # X-API-Key authentication
│   │   ├── middleware.py     # CORS middleware
│   │   ├── ingest.py        # POST /api/ingest, GET/DELETE /api/documents
│   │   ├── search.py        # POST /api/search
│   │   ├── graph.py         # GET /api/graph
│   │   └── admin.py         # GET /health, /api/settings
│   ├── core/
│   │   ├── embedder.py      # Ollama + OpenAI embedding adapters
│   │   ├── chunker.py       # Recursive, semantic, page chunking
│   │   ├── vector_store.py  # pgvector CRUD + HNSW search
│   │   ├── fts.py           # tsvector full-text search
│   │   ├── graph_store.py   # Knowledge graph CRUD + CTE traversal
│   │   ├── hybrid_search.py # RRF fusion across all search types
│   │   ├── extractor.py     # LLM entity/relationship extraction
│   │   └── pipeline.py      # End-to-end ingestion pipeline
│   ├── db/
│   │   ├── schema.sql       # PostgreSQL DDL (6 tables, 8 indexes)
│   │   └── connection.py    # asyncpg connection pool
│   ├── parsers/
│   │   ├── pdf.py           # pypdf + pdfplumber (MIT/BSD)
│   │   ├── docx.py          # python-docx
│   │   ├── xlsx.py          # openpyxl
│   │   ├── pptx.py          # python-pptx
│   │   ├── markdown.py      # Markdown + YAML frontmatter
│   │   └── text.py          # Plain text
│   └── static/              # Dashboard build output
├── dashboard/                # React SPA (Vite + Tailwind)
├── docs/                     # Architecture, Schema, Integration docs
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── Makefile
└── LICENSE (MIT)
```

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **PostgreSQL-only** | One DB = one backup, one connection pool, ACID across vectors+text+graph. pgvector is competitive up to 50M vectors. |
| **No LangChain/LlamaIndex** | Zero framework lock-in. Raw SQL + httpx = full control, minimal dependencies. |
| **RRF over learned ranking** | RRF is parameter-free (k=60), no training data needed, +22% precision over vector-only. |
| **Recursive CTE over Neo4j** | For 2-hop RAG graphs, CTE is 250x faster than Apache AGE and matches Neo4j performance. |
| **pypdf over PyMuPDF** | PyMuPDF is AGPL-3.0 — incompatible with MIT. pypdf+pdfplumber are BSD/MIT. |
| **FastAPI + embedded SPA** | Single process, single port. Dashboard builds to `static/`, served by FastAPI. |
| **X-API-Key auth** | Simple, stateless. No JWT complexity for a backend service. |

---

## API Reference

### Endpoints

| Method | Endpoint | Tag | Description |
|---|---|---|---|
| `GET` | `/health` | admin | Health check (no auth) |
| `POST` | `/api/ingest` | documents | Upload document (multipart) |
| `GET` | `/api/documents` | documents | List documents (filter by status) |
| `GET` | `/api/documents/{id}` | documents | Document details + processing status |
| `DELETE` | `/api/documents/{id}` | documents | Delete document + chunks + graph |
| `POST` | `/api/search` | search | Hybrid search (vector/fts/graph/hybrid) |
| `GET` | `/api/graph` | graph | Knowledge graph nodes + edges |
| `GET` | `/api/graph/node/{id}` | graph | Node details + 1-hop neighbors |
| `GET` | `/api/settings` | admin | Current RAG settings |
| `PUT` | `/api/settings` | admin | Update settings |

### Interactive Documentation

ModolRAG auto-generates full API documentation with request/response schemas and live testing:

| URL | Format | Best For |
|---|---|---|
| [`/docs`](http://localhost:8000/docs) | **Swagger UI** | Interactive testing — try endpoints directly in browser |
| [`/redoc`](http://localhost:8000/redoc) | **ReDoc** | Reading — clean, print-friendly documentation |
| [`/openapi.json`](http://localhost:8000/openapi.json) | **OpenAPI 3.1** | Code generation — import into Postman, Insomnia, etc. |

All endpoints include:
- Pydantic request/response models with field descriptions
- Validation constraints (min/max values, required fields)
- Example payloads for quick testing
- Tag-based grouping (documents, search, graph, admin)

---

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Contributions welcome. Please open an issue first to discuss changes.
