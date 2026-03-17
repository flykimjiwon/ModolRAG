"""Test RRF fusion and hybrid search logic."""
from modolrag.core.hybrid_search import rrf_fuse, SearchResult


class TestRRFFusion:
    def test_single_list(self):
        items = [{"chunk_id": "a", "content": "x"}, {"chunk_id": "b", "content": "y"}]
        result = rrf_fuse([items])
        assert len(result) == 2
        assert result[0]["chunk_id"] == "a"

    def test_two_lists_boost_overlap(self):
        list_a = [{"chunk_id": "1"}, {"chunk_id": "2"}, {"chunk_id": "3"}]
        list_b = [{"chunk_id": "2"}, {"chunk_id": "1"}, {"chunk_id": "4"}]
        result = rrf_fuse([list_a, list_b], k=60)
        ids = [r["chunk_id"] for r in result]
        assert "1" in ids[:2] and "2" in ids[:2]
        assert "4" in ids

    def test_rrf_scores_exist(self):
        items = [{"chunk_id": "x"}]
        result = rrf_fuse([items])
        assert "rrf_score" in result[0]
        assert result[0]["rrf_score"] > 0

    def test_empty_lists(self):
        assert rrf_fuse([]) == []
        assert rrf_fuse([[]]) == []

    def test_three_lists(self):
        a = [{"chunk_id": "1"}, {"chunk_id": "2"}]
        b = [{"chunk_id": "2"}, {"chunk_id": "3"}]
        c = [{"chunk_id": "1"}, {"chunk_id": "3"}]
        result = rrf_fuse([a, b, c])
        assert len(result) == 3
        scores = {r["chunk_id"]: r["rrf_score"] for r in result}
        # Items appearing in more lists get higher scores
        assert scores["1"] >= scores["3"] or scores["2"] >= scores["3"]


class TestSearchResult:
    def test_dataclass(self):
        r = SearchResult(chunk_id="1", document_id="d1", content="hello", score=0.95, match_type="vector")
        assert r.chunk_id == "1"
        assert r.score == 0.95
        assert r.match_type == "vector"
