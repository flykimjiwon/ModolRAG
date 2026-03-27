"""Test FastAPI endpoints (no DB required — tests app structure only)."""
import pytest
from modolrag.main import app


class TestAppStructure:
    def test_app_exists(self):
        assert app is not None
        assert app.title == "ModolRAG"

    def test_routes_registered(self):
        paths = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/health" in paths
        assert "/api/ingest" in paths
        assert "/api/documents" in paths
        assert "/api/search" in paths
        assert "/api/graph" in paths
        assert "/api/settings" in paths
        assert "/api/collections" in paths

    def test_route_count(self):
        api_routes = [r for r in app.routes if hasattr(r, 'methods') and hasattr(r, 'tags')]
        assert len(api_routes) >= 16

    def test_openapi_tags(self):
        tags = [t["name"] for t in app.openapi_tags]
        assert "documents" in tags
        assert "search" in tags
        assert "graph" in tags
        assert "admin" in tags
        assert "collections" in tags

    def test_openapi_schema_generates(self):
        schema = app.openapi()
        assert schema["info"]["title"] == "ModolRAG"
        assert schema["info"]["version"] == "0.1.0"
        assert len(schema["paths"]) >= 8


class TestRouteMethodsAndPaths:
    def _get_route_map(self):
        """Build {path: set(methods)} from app routes."""
        route_map = {}
        for r in app.routes:
            if hasattr(r, 'path') and hasattr(r, 'methods'):
                route_map[r.path] = r.methods
        return route_map

    def test_health_is_get(self):
        rm = self._get_route_map()
        assert "GET" in rm.get("/health", set())

    def test_ingest_is_post(self):
        rm = self._get_route_map()
        assert "POST" in rm.get("/api/ingest", set())

    def test_search_is_post(self):
        rm = self._get_route_map()
        assert "POST" in rm.get("/api/search", set())

    def test_documents_is_get(self):
        rm = self._get_route_map()
        assert "GET" in rm.get("/api/documents", set())

    def test_settings_is_get(self):
        rm = self._get_route_map()
        assert "GET" in rm.get("/api/settings", set())

    def test_no_duplicate_paths(self):
        """Each path+method combo should be unique."""
        seen = set()
        for r in app.routes:
            if hasattr(r, 'path') and hasattr(r, 'methods'):
                for m in r.methods:
                    key = (r.path, m)
                    assert key not in seen, f"Duplicate route: {m} {r.path}"
                    seen.add(key)


class TestModuleImports:
    def test_parsers(self):
        from modolrag.parsers import get_parser
        assert callable(get_parser)

    def test_chunker(self):
        from modolrag.core.chunker import get_chunker
        assert callable(get_chunker)

    def test_embedder(self):
        from modolrag.core.embedder import get_embedder, OllamaEmbedder, OpenAIEmbedder
        assert callable(get_embedder)

    def test_vector_store(self):
        from modolrag.core.vector_store import search_similar, upsert_chunks
        assert callable(search_similar)

    def test_fts(self):
        from modolrag.core.fts import search_fts
        assert callable(search_fts)

    def test_graph_store(self):
        from modolrag.core.graph_store import traverse_graph, upsert_node
        assert callable(traverse_graph)

    def test_hybrid_search(self):
        from modolrag.core.hybrid_search import hybrid_search, rrf_fuse
        assert callable(hybrid_search)

    def test_extractor(self):
        from modolrag.core.extractor import extract_entities_and_relations, extract_wikilinks
        assert callable(extract_entities_and_relations)

    def test_pipeline(self):
        from modolrag.core.pipeline import ingest_document
        assert callable(ingest_document)

    def test_config(self):
        from modolrag.config import get_settings
        s = get_settings()
        assert s.EMBEDDING_PROVIDER in ("ollama", "openai")
