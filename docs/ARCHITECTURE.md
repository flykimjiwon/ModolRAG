# ModolRAG Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ModolRAG                                │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ REST API │  │Dashboard │  │   CLI    │  │ ModolAI       │  │
│  │ FastAPI  │  │React SPA │  │ argparse │  │ (HTTP client) │  │
│  └────┬─────┘  └──────────┘  └────┬─────┘  └───────┬───────┘  │
│       │                           │                 │          │
│  ┌────┴──────────────────────────┴─────────────────┴────────┐  │
│  │                    Core Engine                            │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │ Parser  │→│ Chunker │→│ Embedder │→│ Vector Store │  │  │
│  │  └─────────┘ └─────────┘ └──────────┘ └──────────────┘  │  │
│  │  ┌──────────────┐ ┌───────────┐ ┌─────────────────────┐  │  │
│  │  │ FTS Search   │ │Graph Store│ │ Hybrid Search (RRF) │  │  │
│  │  └──────────────┘ └───────────┘ └─────────────────────┘  │  │
│  │  ┌──────────────┐ ┌───────────────────────────────────┐  │  │
│  │  │  Extractor   │ │        Pipeline (E2E)             │  │  │
│  │  └──────────────┘ └───────────────────────────────────┘  │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                   PostgreSQL                              │  │
│  │  pgvector (HNSW) │ tsvector (GIN) │ Graph Tables (CTE)   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Ingestion Pipeline

```
Upload (multipart) 
  → Save to temp file + create DB record (status: uploaded)
  → Parse document (pypdf/python-docx/openpyxl/python-pptx/markdown/text)
  → Chunk text (RecursiveChunker: separators \n\n → \n → ". " → " " → char)
  → Embed chunks (Ollama or OpenAI, batch processing)
  → Store in modolrag_document_chunks (pgvector halfvec + auto tsvector)
  → Extract entities/relationships (LLM-based, best-effort)
  → Build graph nodes/edges (modolrag_graph_nodes, modolrag_graph_edges)
  → Update status: vectorized, progress: 100%
```

Each step updates `modolrag_documents.status` and `vectorization_progress` for real-time tracking. On failure, `status='error'` with `error_message`.

Graph extraction is **best-effort** — if the LLM is unavailable, the pipeline completes without graph data. Documents are still searchable via vector and FTS.

---

## Search Pipeline

```
Query (text + mode)
  → Embed query text (same embedder as ingestion)
  → Execute search(es) based on mode:
      ├── Vector: embedding <=> query_embedding ORDER BY cosine distance
      ├── FTS: fts @@ websearch_to_tsquery(query) ORDER BY ts_rank_cd
      └── Graph: seed nodes (embedding similarity) → 2-hop BFS → related content
  → RRF Fusion (if hybrid mode)
  → Return top_k results
```

### RRF Fusion Algorithm

Reciprocal Rank Fusion combines multiple ranked lists without requiring score normalization:

```
score(item) = Σ 1/(k + rank_i)  for each list where item appears
```

Where `k=60` (standard constant). Items appearing in multiple lists get higher scores.

Example: An item ranked #1 in vector and #3 in FTS:
```
score = 1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = 0.0323
```

This is parameter-free and has been shown to improve precision by +22% over vector-only search.

---

## Graph RAG

### Why PostgreSQL, Not Neo4j

For RAG knowledge graphs with 2-3 hop traversal:

| Benchmark | PostgreSQL BFS CTE | Neo4j | Apache AGE |
|---|---|---|---|
| 10K nodes shortest path | **0.09ms** | ~1ms | 23ms |
| 100K nodes shortest path | **0.33ms** | ~2ms | 23ms |

PostgreSQL recursive CTEs are sufficient and avoid the operational complexity of a separate graph database.

### Traversal Pattern

```sql
WITH RECURSIVE graph_expansion AS (
    -- Seed: start from matched nodes
    SELECT id AS node_id, 0 AS depth, ARRAY[id] AS visited
    FROM modolrag_graph_nodes WHERE id = ANY($seed_ids)
    
    UNION ALL
    
    -- Expand: follow edges bidirectionally
    SELECT n.id, ge.depth + 1, ge.visited || n.id
    FROM graph_expansion ge
    JOIN modolrag_graph_edges e ON (e.source_id = ge.node_id OR e.target_id = ge.node_id)
    JOIN modolrag_graph_nodes n ON (n.id = CASE WHEN e.source_id = ge.node_id 
                                                 THEN e.target_id ELSE e.source_id END)
    WHERE ge.depth < 2                    -- Max 2 hops
      AND NOT (n.id = ANY(ge.visited))    -- Cycle prevention
)
SELECT DISTINCT ON (node_id) * FROM graph_expansion ORDER BY node_id, depth;
```

### Entity Extraction

LLM-based extraction (Ollama or OpenAI) produces:
- **Entities**: name, type (person/org/concept/location/event), description
- **Relationships**: subject, predicate, object, confidence (1.0=explicit, 0.7=implied, 0.5=inferred)
- **Wikilinks**: `[[text]]` patterns auto-detected as explicit relationships

---

## Embedding Adapters

Factory pattern supporting multiple providers:

```python
embedder = get_embedder(settings)  # Returns OllamaEmbedder or OpenAIEmbedder
embedding = await embedder.embed("text")
embeddings = await embedder.embed_batch(["text1", "text2", ...])
```

| Provider | Model | Dimensions | Endpoint |
|---|---|---|---|
| Ollama | nomic-embed-text | 768 | `{base_url}/api/embeddings` |
| OpenAI | text-embedding-3-small | 1536 | `api.openai.com/v1/embeddings` |

Dimensions auto-detected on first call. Batch processing with configurable batch sizes.

---

## Chunking Strategies

| Strategy | Description | Use Case |
|---|---|---|
| **Recursive** | Split by separator hierarchy: `\n\n` → `\n` → `. ` → ` ` → char | Default, general purpose |
| **Semantic** | Split where embedding similarity drops below threshold | When topic boundaries matter |
| **Page** | Split by page markers (form feed or ParsedDocument.pages) | PDFs with page structure |

Default: RecursiveChunker with chunk_size=512, overlap=51.

---

## API Design

RESTful JSON API with X-API-Key authentication:

- `POST /api/ingest` — Multipart file upload, returns document_id
- `GET/DELETE /api/documents[/{id}]` — CRUD operations
- `POST /api/search` — `{query, top_k, mode, namespace}`
- `GET /api/graph` — Full graph data for visualization
- `GET/PUT /api/settings` — Runtime configuration
- `GET /health` — Health check (no auth)

OpenAPI docs auto-generated at `/docs`.
