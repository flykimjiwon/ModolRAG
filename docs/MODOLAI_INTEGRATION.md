# ModolAI Integration Guide

This guide explains how to connect ModolAI (Next.js AI chat platform) with ModolRAG (RAG engine).

## Architecture

```
ModolAI (Next.js)              ModolRAG (FastAPI)
┌─────────────────┐            ┌──────────────────┐
│ Chat UI         │            │ POST /api/ingest  │
│ Admin Panel     │──HTTP──→   │ POST /api/search  │
│ /v1/embeddings  │            │ GET  /api/graph   │
│ /v1/rerank      │            │ GET  /dashboard   │
└─────────────────┘            └──────────────────┘
        │                              │
        └──────── Same PostgreSQL ─────┘
          (modolai tables + modolrag_ tables)
```

## Setup

### 1. Environment Variables (ModolAI side)

Add to ModolAI's `.env.local`:

```env
MODOLRAG_URL=http://localhost:8000
MODOLRAG_API_KEY=your-shared-api-key
```

### 2. Start ModolRAG

```bash
# Same database as ModolAI
modolrag serve --db $POSTGRES_URI

# Or with Docker (separate container, same network)
docker compose up -d
```

### 3. Configure ModolRAG

```env
MODOLRAG_POSTGRES_URI=postgresql://user:pass@localhost:5432/modolai
MODOLRAG_API_KEYS=your-shared-api-key
MODOLRAG_EMBEDDING_PROVIDER=ollama
MODOLRAG_EMBEDDING_MODEL=nomic-embed-text
```

## Integration Pattern

### RAG-enhanced Chat Completion

In ModolAI's completions API handler, add RAG context before sending to LLM:

```javascript
// In ModolAI: app/api/v1/chat/completions/route.js
async function enhanceWithRAG(userMessage) {
  const response = await fetch(`${process.env.MODOLRAG_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.MODOLRAG_API_KEY,
    },
    body: JSON.stringify({
      query: userMessage,
      top_k: 5,
      mode: 'hybrid',
    }),
  });
  
  const { results } = await response.json();
  
  if (results.length === 0) return null;
  
  return results.map(r => r.content).join('\n\n---\n\n');
}
```

### Document Upload from ModolAI Admin

```javascript
async function uploadToRAG(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${process.env.MODOLRAG_URL}/api/ingest`, {
    method: 'POST',
    headers: { 'X-API-Key': process.env.MODOLRAG_API_KEY },
    body: formData,
  });
  
  return response.json(); // { document_id, status }
}
```

## Docker Network Configuration

When running both services in Docker:

```yaml
# docker-compose.yml (ModolAI + ModolRAG)
services:
  modolai:
    image: modolai:latest
    environment:
      MODOLRAG_URL: http://modolrag:8000
      MODOLRAG_API_KEY: shared-key
    depends_on:
      - modolrag

  modolrag:
    build: ./ModolRAG
    environment:
      MODOLRAG_POSTGRES_URI: postgresql://user:pass@postgres:5432/modolai
      MODOLRAG_API_KEYS: shared-key

  postgres:
    image: pgvector/pgvector:pg15
    # Shared by both services
```

## Reusing ModolAI's Embedding Endpoint

ModolRAG can use ModolAI's existing `/v1/embeddings` endpoint instead of calling Ollama/OpenAI directly:

```env
# Point ModolRAG's Ollama URL to ModolAI's API
MODOLRAG_OLLAMA_BASE_URL=http://modolai:3000/v1
```

This reuses ModolAI's model server routing and load balancing.

## Migration from Existing RAG Tables

If ModolAI already has `rag_documents`, `rag_models`, `rag_settings` tables:

1. **Phase 1 — Coexistence**: ModolRAG uses `modolrag_*` tables alongside existing `rag_*` tables. No migration needed.
2. **Phase 2 — Migration**: Use `modolrag migrate --from-modolai` to transfer documents. Re-embedding is required (vector format differs).
3. **Phase 3 — Native**: ModolAI calls ModolRAG API directly for all RAG operations.

## Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| Connection refused | ModolRAG not running | Check `curl http://localhost:8000/health` |
| 401 Unauthorized | API key mismatch | Ensure same key in both `MODOLRAG_API_KEY` and `MODOLRAG_API_KEYS` |
| Empty search results | No documents ingested | Upload documents via `/api/ingest` first |
| Slow embedding | Ollama model not loaded | First request loads model; subsequent calls are fast |
| Timeout on large files | Default timeout too low | Increase `MODOLRAG_CHUNK_SIZE` or process smaller files |
