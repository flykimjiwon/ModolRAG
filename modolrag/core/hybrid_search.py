"""Hybrid search combining vector, FTS, and graph with RRF fusion."""
from __future__ import annotations
from dataclasses import dataclass, field

from modolrag.core.vector_store import search_similar
from modolrag.core.fts import search_fts
from modolrag.core.graph_store import traverse_graph, search_nodes_by_embedding


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    content: str
    score: float
    file_name: str = ""
    original_name: str = ""
    match_type: str = "hybrid"  # vector, fts, graph, hybrid
    metadata: dict = field(default_factory=dict)


def rrf_fuse(
    ranked_lists: list[list[dict]],
    k: int = 60,
    id_key: str = "chunk_id",
    weights: list[float] | None = None,
) -> list[dict]:
    """Weighted Reciprocal Rank Fusion across multiple ranked result lists.

    score = Σ weight_i * 1/(k + rank_i) for each list where the item appears.
    k=60 is the standard constant (Cormack et al., SIGIR 2009).
    """
    if weights is None:
        weights = [1.0] * len(ranked_lists)

    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for list_idx, ranked_list in enumerate(ranked_lists):
        w = weights[list_idx] if list_idx < len(weights) else 1.0
        for rank, item in enumerate(ranked_list, start=1):
            item_id = item[id_key]
            scores[item_id] = scores.get(item_id, 0.0) + w * 1.0 / (k + rank)
            if item_id not in items:
                items[item_id] = item

    # Sort by RRF score descending
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    result = []
    for item_id in sorted_ids:
        item = items[item_id].copy()
        item["rrf_score"] = scores[item_id]
        result.append(item)

    return result


async def hybrid_search(
    query_text: str,
    query_embedding: list[float],
    top_k: int = 10,
    mode: str = "hybrid",
    namespace: str = "default",
    vector_weight: float = 1.0,
    fts_weight: float = 1.0,
    graph_weight: float = 0.8,
    document_ids: list[str] | None = None,
) -> list[SearchResult]:
    """Execute hybrid search across vector, FTS, and graph.

    Modes:
        - "vector": Vector search only
        - "fts": Full-text search only
        - "graph": Graph traversal only
        - "hybrid": All three fused with RRF
    """
    results_lists: list[list[dict]] = []
    rrf_weights: list[float] = []

    # 1. Vector search
    if mode in ("vector", "hybrid"):
        vector_results = await search_similar(
            query_embedding=query_embedding,
            top_k=top_k * 2,
            threshold=0.0,
            document_ids=document_ids,
        )
        for r in vector_results:
            r["match_type"] = "vector"
        if vector_results:
            results_lists.append(vector_results)
            rrf_weights.append(vector_weight)

    if mode in ("fts", "hybrid"):
        fts_results = await search_fts(
            query_text=query_text,
            top_k=top_k * 2,
            document_ids=document_ids,
        )
        for r in fts_results:
            r["match_type"] = "fts"
        if fts_results:
            results_lists.append(fts_results)
            rrf_weights.append(fts_weight)

    # 3. Graph-enhanced search
    if mode in ("graph", "hybrid"):
        # Find seed nodes via embedding similarity
        seed_nodes = await search_nodes_by_embedding(
            query_embedding=query_embedding,
            top_k=5,
            namespace=namespace,
        )

        if seed_nodes:
            seed_ids = [n["node_id"] for n in seed_nodes]
            # Traverse 2 hops from seed nodes
            expanded = await traverse_graph(
                seed_node_ids=seed_ids,
                max_depth=2,
                namespace=namespace,
            )

            # Convert graph nodes to search results format
            graph_results = []
            for node in expanded:
                if node.get("content"):
                    graph_results.append({
                        "chunk_id": node["node_id"],
                        "document_id": "",
                        "content": node["content"],
                        "match_type": "graph",
                        "file_name": "",
                        "original_name": "",
                        "metadata": {"node_type": node["node_type"], "depth": node["depth"]},
                        "graph_depth": node["depth"],
                    })
            # Apply depth decay: sort by depth ascending so shallower nodes rank higher
            graph_results.sort(key=lambda x: x["graph_depth"])
            if graph_results:
                results_lists.append(graph_results)
                rrf_weights.append(graph_weight)

    # Single mode — return directly without RRF
    if len(results_lists) == 1:
        fused = results_lists[0][:top_k]
    elif len(results_lists) == 0:
        fused = []
    else:
        # Weighted RRF fusion
        fused = rrf_fuse(results_lists, k=60, weights=rrf_weights)[:top_k]

    # Convert to SearchResult
    return [
        SearchResult(
            chunk_id=r.get("chunk_id", ""),
            document_id=r.get("document_id", ""),
            content=r.get("content", ""),
            score=r.get("rrf_score", r.get("similarity", r.get("rank", 0.0))),
            file_name=r.get("file_name", ""),
            original_name=r.get("original_name", ""),
            match_type=r.get("match_type", mode),
            metadata=r.get("metadata", {}),
        )
        for r in fused
    ]
