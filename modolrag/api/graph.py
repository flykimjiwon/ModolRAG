"""Graph data endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from modolrag.api.auth import require_api_key

router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/graph")
async def get_graph(namespace: str = "default", _: str = Depends(require_api_key)):
    """Get all graph nodes and edges for visualization."""
    from modolrag.core.graph_store import get_graph_data
    data = await get_graph_data(namespace=namespace)
    return data


@router.get("/graph/node/{node_id}")
async def get_node(node_id: str, namespace: str = "default", _: str = Depends(require_api_key)):
    """Get node details with neighbors."""
    from modolrag.core.graph_store import get_neighbors
    from modolrag.db import fetchrow

    node = await fetchrow("SELECT * FROM modolrag_graph_nodes WHERE id = $1::uuid", node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    neighbors = await get_neighbors(node_id=node_id, namespace=namespace)
    return {"node": dict(node), "neighbors": neighbors}
