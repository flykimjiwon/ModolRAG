# ModolRAG Database Schema

All tables use the `modolrag_` prefix to coexist with host application tables (e.g., ModolAI) in the same PostgreSQL database.

## Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- trigram similarity
CREATE EXTENSION IF NOT EXISTS ltree;     -- hierarchical labels for communities
```

---

## Entity-Relationship Diagram

```
modolrag_documents
  ├── 1:N → modolrag_document_chunks (document_id FK, CASCADE delete)
  │              ├── embedding halfvec(1536) → HNSW index
  │              ├── fts tsvector GENERATED  → GIN index
  │              └── parent_chunk_id (self-ref, parent-child chunking)
  │
modolrag_graph_nodes (UNIQUE: namespace + title)
  ├── 1:N → modolrag_graph_edges (source_id FK, CASCADE)
  └── 1:N → modolrag_graph_edges (target_id FK, CASCADE)
              └── UNIQUE: namespace + source_id + target_id + relation_type

modolrag_communities
  └── path ltree (hierarchical community structure)

modolrag_settings (singleton row)
```

---

## Tables

### 1. modolrag_documents

Stores uploaded document metadata and processing status.

```sql
CREATE TABLE IF NOT EXISTS modolrag_documents (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name              TEXT NOT NULL,
    original_name          TEXT NOT NULL,
    file_size              BIGINT,
    mime_type              TEXT NOT NULL,
    category               TEXT DEFAULT 'other'
        CHECK (category IN ('text','pdf','word','excel','powerpoint','markdown','other')),
    status                 TEXT DEFAULT 'uploaded'
        CHECK (status IN ('uploaded','processing','indexed','vectorizing','vectorized','error')),
    extracted_text         TEXT,
    chunk_count            INTEGER DEFAULT 0,
    embedding_model        TEXT,
    vectorization_progress REAL DEFAULT 0.0,
    error_message          TEXT,
    uploaded_by            TEXT,
    created_at             TIMESTAMPTZ DEFAULT now(),
    updated_at             TIMESTAMPTZ DEFAULT now()
);
```

### 2. modolrag_document_chunks

Text chunks with vector embeddings and auto-generated FTS column.

```sql
CREATE TABLE IF NOT EXISTS modolrag_document_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES modolrag_documents(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    embedding       halfvec(1536),
    fts             tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    chunk_index     INTEGER NOT NULL,
    chunk_level     INTEGER DEFAULT 0,
    parent_chunk_id UUID REFERENCES modolrag_document_chunks(id) ON DELETE SET NULL,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### 3. modolrag_graph_nodes

Knowledge graph entities.

```sql
CREATE TABLE IF NOT EXISTS modolrag_graph_nodes (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace  TEXT DEFAULT 'default',
    title      TEXT NOT NULL,
    content    TEXT,
    embedding  halfvec(1536),
    node_type  TEXT DEFAULT 'concept'
        CHECK (node_type IN ('person','org','concept','location','event','document')),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(namespace, title)
);
```

### 4. modolrag_graph_edges

Relationships between graph nodes.

```sql
CREATE TABLE IF NOT EXISTS modolrag_graph_edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace       TEXT DEFAULT 'default',
    source_id       UUID NOT NULL REFERENCES modolrag_graph_nodes(id) ON DELETE CASCADE,
    target_id       UUID NOT NULL REFERENCES modolrag_graph_nodes(id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,
    weight          REAL DEFAULT 1.0,
    context_snippet TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(namespace, source_id, target_id, relation_type)
);
```

On conflict (duplicate edge): `weight = weight + 1.0` (accumulate evidence).

### 5. modolrag_communities

Hierarchical community detection for graph summarization.

```sql
CREATE TABLE IF NOT EXISTS modolrag_communities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path            ltree,
    summary         TEXT,
    node_ids        UUID[],
    level           INTEGER DEFAULT 0,
    embedding       halfvec(1536),
    needs_resummary BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### 6. modolrag_settings

Singleton configuration table.

```sql
CREATE TABLE IF NOT EXISTS modolrag_settings (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_size           INTEGER DEFAULT 512   CHECK (chunk_size BETWEEN 128 AND 4096),
    chunk_overlap        INTEGER DEFAULT 51    CHECK (chunk_overlap BETWEEN 0 AND 512),
    embedding_model      TEXT DEFAULT 'nomic-embed-text',
    embedding_dimensions INTEGER DEFAULT 768,
    similarity_top_k     INTEGER DEFAULT 5     CHECK (similarity_top_k BETWEEN 1 AND 50),
    similarity_threshold REAL DEFAULT 0.7      CHECK (similarity_threshold BETWEEN 0.0 AND 1.0),
    response_mode        TEXT DEFAULT 'compact',
    api_keys             JSONB DEFAULT '[]',
    created_at           TIMESTAMPTZ DEFAULT now(),
    updated_at           TIMESTAMPTZ DEFAULT now()
);
```

---

## Indexes

| Index | Type | Table | Column(s) | Purpose |
|---|---|---|---|---|
| `idx_chunks_embedding` | HNSW | document_chunks | `embedding halfvec_cosine_ops` | Vector similarity search |
| `idx_chunks_fts` | GIN | document_chunks | `fts` | Full-text keyword search |
| `idx_chunks_document` | B-tree | document_chunks | `document_id` | Chunk lookup by document |
| `idx_edges_source` | B-tree | graph_edges | `source_id` | Outgoing edge traversal |
| `idx_edges_target` | B-tree | graph_edges | `target_id` | Incoming edge traversal |
| `idx_nodes_namespace` | B-tree | graph_nodes | `namespace` | Namespace filtering |
| `idx_nodes_embedding` | HNSW | graph_nodes | `embedding halfvec_cosine_ops` | Node vector search |
| `idx_communities_path` | GiST | communities | `path` | Hierarchical path queries |

HNSW parameters: `m=16, ef_construction=64` (balanced recall/build-time).

---

## Supabase Compatibility

ModolRAG uses standard PostgreSQL features only:
- `gen_random_uuid()` (built-in since PG13)
- `pgvector` extension (available on Supabase)
- `halfvec` type (pgvector 0.7+)
- No Supabase Edge Functions dependency
- Connection via standard `POSTGRES_URI`

The `modolrag_` prefix ensures zero conflicts with Supabase's own tables (`auth.*`, `storage.*`, etc.).
