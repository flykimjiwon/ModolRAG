"""Knowledge graph store with PostgreSQL recursive CTE traversal."""
from __future__ import annotations
import json
import uuid
from modolrag.db import fetch, fetchrow, execute


def _format_halfvec(embedding: list[float]) -> str:
    return "[" + ",".join(str(v) for v in embedding) + "]"


async def upsert_node(
    namespace: str,
    title: str,
    content: str | None = None,
    embedding: list[float] | None = None,
    node_type: str = "concept",
    properties: dict | None = None,
) -> str:
    """Upsert a graph node. Returns node ID."""
    node_id = str(uuid.uuid4())
    embedding_str = _format_halfvec(embedding) if embedding else None
    props_json = json.dumps(properties) if properties else "{}"

    row = await fetchrow(
        """
        INSERT INTO modolrag_graph_nodes (id, namespace, title, content, embedding, node_type, properties)
        VALUES ($1::uuid, $2, $3, $4, $5::halfvec, $6, $7::jsonb)
        ON CONFLICT (namespace, title) DO UPDATE SET
            content = COALESCE(EXCLUDED.content, modolrag_graph_nodes.content),
            embedding = COALESCE(EXCLUDED.embedding, modolrag_graph_nodes.embedding),
            node_type = EXCLUDED.node_type,
            properties = modolrag_graph_nodes.properties || EXCLUDED.properties,
            updated_at = now()
        RETURNING id
        """,
        node_id, namespace, title, content, embedding_str, node_type, props_json
    )
    return str(row["id"])


async def upsert_edge(
    namespace: str,
    source_id: str,
    target_id: str,
    relation_type: str,
    weight: float = 1.0,
    context_snippet: str | None = None,
    metadata: dict | None = None,
) -> str:
    """Upsert a graph edge. On conflict, increment weight. Returns edge ID."""
    edge_id = str(uuid.uuid4())
    meta_json = json.dumps(metadata) if metadata else "{}"

    row = await fetchrow(
        """
        INSERT INTO modolrag_graph_edges (id, namespace, source_id, target_id, relation_type, weight, context_snippet, metadata)
        VALUES ($1::uuid, $2, $3::uuid, $4::uuid, $5, $6, $7, $8::jsonb)
        ON CONFLICT (namespace, source_id, target_id, relation_type) DO UPDATE SET
            weight = modolrag_graph_edges.weight + 1.0,
            context_snippet = COALESCE(EXCLUDED.context_snippet, modolrag_graph_edges.context_snippet),
            metadata = modolrag_graph_edges.metadata || EXCLUDED.metadata
        RETURNING id
        """,
        edge_id, namespace, source_id, target_id, relation_type, weight, context_snippet, meta_json
    )
    return str(row["id"])


async def traverse_graph(
    seed_node_ids: list[str],
    max_depth: int = 2,
    namespace: str = "default",
) -> list[dict]:
    """BFS traversal using recursive CTE. Bidirectional, cycle-safe."""
    if not seed_node_ids:
        return []

    seed_array = "{" + ",".join(seed_node_ids) + "}"

    rows = await fetch(
        """
        WITH RECURSIVE graph_expansion AS (
            -- Seed nodes
            SELECT
                n.id AS node_id,
                n.title,
                n.content,
                n.node_type,
                0 AS depth,
                ARRAY[n.id] AS visited
            FROM modolrag_graph_nodes n
            WHERE n.id = ANY($1::uuid[])
              AND n.namespace = $3

            UNION ALL

            -- Expand outgoing edges
            SELECT
                n.id AS node_id,
                n.title,
                n.content,
                n.node_type,
                ge.depth + 1,
                ge.visited || n.id
            FROM graph_expansion ge
            JOIN modolrag_graph_edges e ON (
                e.source_id = ge.node_id OR e.target_id = ge.node_id
            )
            JOIN modolrag_graph_nodes n ON (
                n.id = CASE WHEN e.source_id = ge.node_id THEN e.target_id ELSE e.source_id END
            )
            WHERE ge.depth < $2
              AND NOT (n.id = ANY(ge.visited))
              AND e.namespace = $3
              AND n.namespace = $3
        )
        SELECT DISTINCT ON (node_id) node_id, title, content, node_type, depth
        FROM graph_expansion
        ORDER BY node_id, depth
        """,
        seed_array, max_depth, namespace
    )

    return [
        {
            "node_id": str(row["node_id"]),
            "title": row["title"],
            "content": row["content"],
            "node_type": row["node_type"],
            "depth": row["depth"],
        }
        for row in rows
    ]


async def get_neighbors(node_id: str, namespace: str = "default") -> list[dict]:
    """Get 1-hop neighbors of a node."""
    rows = await fetch(
        """
        SELECT
            n.id, n.title, n.node_type, e.relation_type, e.weight,
            CASE WHEN e.source_id = $1::uuid THEN 'outgoing' ELSE 'incoming' END AS direction
        FROM modolrag_graph_edges e
        JOIN modolrag_graph_nodes n ON (
            n.id = CASE WHEN e.source_id = $1::uuid THEN e.target_id ELSE e.source_id END
        )
        WHERE (e.source_id = $1::uuid OR e.target_id = $1::uuid)
          AND e.namespace = $2
        ORDER BY e.weight DESC
        """,
        node_id, namespace
    )
    return [dict(row) for row in rows]


async def search_nodes_by_embedding(
    query_embedding: list[float],
    top_k: int = 10,
    namespace: str = "default",
) -> list[dict]:
    """Vector search on graph nodes."""
    embedding_str = _format_halfvec(query_embedding)

    rows = await fetch(
        """
        SELECT
            id, title, content, node_type, properties,
            1 - (embedding <=> $1::halfvec) AS similarity
        FROM modolrag_graph_nodes
        WHERE namespace = $3
          AND embedding IS NOT NULL
        ORDER BY embedding <=> $1::halfvec
        LIMIT $2
        """,
        embedding_str, top_k, namespace
    )
    return [
        {
            "node_id": str(row["id"]),
            "title": row["title"],
            "content": row["content"],
            "node_type": row["node_type"],
            "similarity": float(row["similarity"]),
        }
        for row in rows
    ]


async def get_graph_data(namespace: str = "default") -> dict:
    """Get all nodes and edges for visualization."""
    nodes = await fetch(
        "SELECT id, title, content, node_type, properties FROM modolrag_graph_nodes WHERE namespace = $1",
        namespace
    )
    edges = await fetch(
        """
        SELECT id, source_id, target_id, relation_type, weight
        FROM modolrag_graph_edges WHERE namespace = $1
        """,
        namespace
    )
    return {
        "nodes": [dict(n) for n in nodes],
        "edges": [dict(e) for e in edges],
    }


async def delete_node(node_id: str) -> None:
    """Delete a node and its edges (CASCADE handles edges)."""
    await execute("DELETE FROM modolrag_graph_nodes WHERE id = $1::uuid", node_id)
