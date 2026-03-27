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


class TestRRFEdgeCases:
    def test_custom_weights(self):
        """Weighted RRF should boost higher-weighted lists."""
        list_a = [{"chunk_id": "a1"}, {"chunk_id": "a2"}]
        list_b = [{"chunk_id": "b1"}, {"chunk_id": "b2"}]
        result = rrf_fuse([list_a, list_b], weights=[2.0, 0.5])
        scores = {r["chunk_id"]: r["rrf_score"] for r in result}
        # list_a items (weight=2.0) should score higher than list_b (weight=0.5)
        assert scores["a1"] > scores["b1"]

    def test_duplicate_within_single_list(self):
        """Duplicate chunk_ids in same list: last occurrence wins for item data."""
        items = [{"chunk_id": "dup", "val": 1}, {"chunk_id": "dup", "val": 2}]
        result = rrf_fuse([items])
        assert len(result) == 1
        assert result[0]["chunk_id"] == "dup"

    def test_large_k_value(self):
        """Large k dampens rank differences."""
        items = [{"chunk_id": "x"}, {"chunk_id": "y"}]
        result_small_k = rrf_fuse([items], k=1)
        result_large_k = rrf_fuse([items], k=1000)
        # With small k, score gap between rank 1 and 2 is larger
        gap_small = result_small_k[0]["rrf_score"] - result_small_k[1]["rrf_score"]
        gap_large = result_large_k[0]["rrf_score"] - result_large_k[1]["rrf_score"]
        assert gap_small > gap_large

    def test_single_item_per_list(self):
        """Each list has one unique item — all should appear in result."""
        lists = [[{"chunk_id": str(i)}] for i in range(5)]
        result = rrf_fuse(lists)
        assert len(result) == 5

    def test_top_k_limits_results(self):
        """top_k parameter should limit the number of returned results."""
        items = [{"chunk_id": str(i)} for i in range(10)]
        result = rrf_fuse([items], top_k=3)
        assert len(result) == 3

    def test_top_k_none_returns_all(self):
        items = [{"chunk_id": str(i)} for i in range(10)]
        result = rrf_fuse([items], top_k=None)
        assert len(result) == 10

    def test_custom_id_key(self):
        """rrf_fuse should work with a custom id_key."""
        list_a = [{"doc_id": "a", "text": "x"}, {"doc_id": "b", "text": "y"}]
        list_b = [{"doc_id": "b", "text": "y"}, {"doc_id": "c", "text": "z"}]
        result = rrf_fuse([list_a, list_b], id_key="doc_id")
        ids = [r["doc_id"] for r in result]
        assert "b" in ids  # overlap item should be present
        assert len(result) == 3
        # "b" appears in both lists, should rank highest
        assert result[0]["doc_id"] == "b"

    def test_weights_shorter_than_lists(self):
        """When weights list is shorter than ranked_lists, extra lists default to 1.0."""
        list_a = [{"chunk_id": "a"}]
        list_b = [{"chunk_id": "b"}]
        result = rrf_fuse([list_a, list_b], weights=[0.5])
        scores = {r["chunk_id"]: r["rrf_score"] for r in result}
        # list_b gets default weight 1.0 > list_a weight 0.5
        assert scores["b"] > scores["a"]


class TestSearchResult:
    def test_dataclass(self):
        r = SearchResult(chunk_id="1", document_id="d1", content="hello", score=0.95, match_type="vector")
        assert r.chunk_id == "1"
        assert r.score == 0.95
        assert r.match_type == "vector"

    def test_to_dict(self):
        r = SearchResult(chunk_id="1", document_id="d1", content="hello", score=0.95, match_type="vector")
        d = r.to_dict()
        assert isinstance(d, dict)
        assert d["chunk_id"] == "1"
        assert d["score"] == 0.95
        assert d["match_type"] == "vector"
        assert d["metadata"] == {}

    def test_to_dict_with_metadata(self):
        r = SearchResult(chunk_id="x", document_id="d", content="c", score=0.5, metadata={"page": 3})
        d = r.to_dict()
        assert d["metadata"] == {"page": 3}

    def test_default_values(self):
        r = SearchResult(chunk_id="a", document_id="b", content="c", score=0.1)
        assert r.match_type == "hybrid"
        assert r.file_name == ""
        assert r.original_name == ""
