-- PostgreSQL Schema for ModolRAG
-- All tables use modolrag_ prefix for namespace isolation

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- trigram similarity for text search
CREATE EXTENSION IF NOT EXISTS ltree;       -- hierarchical labels for communities

-- 1. modolrag_documents
-- Stores document metadata and processing status
CREATE TABLE IF NOT EXISTS modolrag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_size BIGINT,
    mime_type TEXT NOT NULL,
    category TEXT DEFAULT 'other' CHECK (category IN ('text','pdf','word','excel','powerpoint','markdown','other')),
    status TEXT DEFAULT 'uploaded' CHECK (status IN ('uploaded','processing','indexed','vectorizing','vectorized','error')),
    extracted_text TEXT,
    chunk_count INTEGER DEFAULT 0,
    embedding_model TEXT,
    vectorization_progress REAL DEFAULT 0.0,
    error_message TEXT,
    uploaded_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. modolrag_document_chunks
-- Stores document chunks with embeddings and full-text search vectors
CREATE TABLE IF NOT EXISTS modolrag_document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES modolrag_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding halfvec(1536),
    fts tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    chunk_index INTEGER NOT NULL,
    chunk_level INTEGER DEFAULT 0,
    parent_chunk_id UUID REFERENCES modolrag_document_chunks(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. modolrag_graph_nodes
-- Stores knowledge graph nodes (entities)
CREATE TABLE IF NOT EXISTS modolrag_graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace TEXT DEFAULT 'default',
    title TEXT NOT NULL,
    content TEXT,
    embedding halfvec(1536),
    node_type TEXT DEFAULT 'concept' CHECK (node_type IN ('person','org','concept','location','event','document')),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(namespace, title)
);

-- 4. modolrag_graph_edges
-- Stores relationships between graph nodes
CREATE TABLE IF NOT EXISTS modolrag_graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace TEXT DEFAULT 'default',
    source_id UUID NOT NULL REFERENCES modolrag_graph_nodes(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES modolrag_graph_nodes(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    context_snippet TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(namespace, source_id, target_id, relation_type)
);

-- 5. modolrag_communities
-- Stores hierarchical community structures for graph clustering
CREATE TABLE IF NOT EXISTS modolrag_communities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path ltree,
    summary TEXT,
    node_ids UUID[],
    level INTEGER DEFAULT 0,
    embedding halfvec(1536),
    needs_resummary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. modolrag_settings
-- Stores system-wide configuration
CREATE TABLE IF NOT EXISTS modolrag_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_size INTEGER DEFAULT 512 CHECK (chunk_size BETWEEN 128 AND 4096),
    chunk_overlap INTEGER DEFAULT 51 CHECK (chunk_overlap BETWEEN 0 AND 512),
    embedding_model TEXT DEFAULT 'nomic-embed-text',
    embedding_dimensions INTEGER DEFAULT 768,
    similarity_top_k INTEGER DEFAULT 5 CHECK (similarity_top_k BETWEEN 1 AND 50),
    similarity_threshold REAL DEFAULT 0.7 CHECK (similarity_threshold BETWEEN 0.0 AND 1.0),
    response_mode TEXT DEFAULT 'compact',
    api_keys JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance optimization

-- Vector similarity search on chunks
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON modolrag_document_chunks USING hnsw (embedding halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Full-text search on chunks
CREATE INDEX IF NOT EXISTS idx_chunks_fts ON modolrag_document_chunks USING gin(fts);

-- Document lookup
CREATE INDEX IF NOT EXISTS idx_chunks_document ON modolrag_document_chunks(document_id);

-- Graph edge lookups
CREATE INDEX IF NOT EXISTS idx_edges_source ON modolrag_graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON modolrag_graph_edges(target_id);

-- Graph node lookups
CREATE INDEX IF NOT EXISTS idx_nodes_namespace ON modolrag_graph_nodes(namespace);
CREATE INDEX IF NOT EXISTS idx_nodes_embedding ON modolrag_graph_nodes USING hnsw (embedding halfvec_cosine_ops);

-- Community hierarchy
CREATE INDEX IF NOT EXISTS idx_communities_path ON modolrag_communities USING gist(path);

-- Insert default settings if not exists
INSERT INTO modolrag_settings (id) VALUES (gen_random_uuid()) ON CONFLICT DO NOTHING;
