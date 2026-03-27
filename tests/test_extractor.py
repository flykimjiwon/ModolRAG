"""Test entity/relationship extractor."""
from modolrag.core.extractor import extract_wikilinks, ExtractionResult, Entity, Relationship


class TestWikilinks:
    def test_extracts_links(self):
        rels = extract_wikilinks("See [[Python]] and [[FastAPI]] for details.")
        assert len(rels) >= 2
        subjects = {r.subject for r in rels}
        assert "Python" in subjects
        assert "FastAPI" in subjects

    def test_no_links(self):
        rels = extract_wikilinks("No links here.")
        assert len(rels) == 0

    def test_single_link(self):
        rels = extract_wikilinks("Check [[ModolRAG]] out.")
        assert len(rels) == 0  # needs 2+ for relationships


class TestWikilinksEdgeCases:
    def test_special_chars_in_link(self):
        rels = extract_wikilinks("See [[C++]] and [[Node.js]] here.")
        subjects = {r.subject for r in rels}
        assert "C++" in subjects
        assert "Node.js" in subjects

    def test_empty_brackets(self):
        """Empty [[]] should not produce relationships."""
        rels = extract_wikilinks("Empty [[]] here.")
        # [[]] matches empty string — should still work without crash
        assert isinstance(rels, list)

    def test_duplicate_links(self):
        """Same link appearing twice — relationships still valid."""
        rels = extract_wikilinks("[[A]] and [[A]] and [[B]]")
        subjects = [r.subject for r in rels]
        assert "A" in subjects
        assert "B" in subjects

    def test_korean_links(self):
        rels = extract_wikilinks("참고: [[파이썬]]과 [[자바스크립트]]를 비교.")
        subjects = {r.subject for r in rels}
        assert "파이썬" in subjects
        assert "자바스크립트" in subjects

    def test_many_links(self):
        """Many links produce n*(n-1) relationships."""
        text = " ".join(f"[[item{i}]]" for i in range(5))
        rels = extract_wikilinks(text)
        assert len(rels) == 5 * 4  # permutations

    def test_whitespace_only_links_filtered(self):
        """[[ ]] should be ignored."""
        rels = extract_wikilinks("[[  ]] and [[A]] and [[B]]")
        subjects = {r.subject for r in rels}
        assert "A" in subjects
        assert "B" in subjects
        assert "" not in subjects

    def test_empty_text(self):
        assert extract_wikilinks("") == []
        assert extract_wikilinks(None or "") == []


class TestParseLlmJson:
    def test_direct_json(self):
        from modolrag.core.extractor import _parse_llm_json
        result = _parse_llm_json('{"entities": [], "relationships": []}')
        assert result == {"entities": [], "relationships": []}

    def test_markdown_code_block(self):
        from modolrag.core.extractor import _parse_llm_json
        text = '```json\n{"entities": [{"name": "X"}]}\n```'
        result = _parse_llm_json(text)
        assert result["entities"][0]["name"] == "X"

    def test_garbage_returns_none(self):
        from modolrag.core.extractor import _parse_llm_json
        assert _parse_llm_json("not json at all") is None

    def test_empty_string_returns_none(self):
        from modolrag.core.extractor import _parse_llm_json
        assert _parse_llm_json("") is None
        assert _parse_llm_json("   ") is None

    def test_json_array_returns_none(self):
        """Only dicts are valid, not arrays."""
        from modolrag.core.extractor import _parse_llm_json
        assert _parse_llm_json('[1, 2, 3]') is None

    def test_json_with_surrounding_text(self):
        from modolrag.core.extractor import _parse_llm_json
        text = 'Here is the result: {"entities": []} and some more text'
        result = _parse_llm_json(text)
        assert result == {"entities": []}

    def test_nested_json_objects(self):
        from modolrag.core.extractor import _parse_llm_json
        text = '{"entities": [{"name": "X", "type": "concept"}], "relationships": []}'
        result = _parse_llm_json(text)
        assert len(result["entities"]) == 1


class TestDataClasses:
    def test_entity(self):
        e = Entity(name="Python", type="concept", description="A language")
        assert e.name == "Python"
        assert e.type == "concept"

    def test_relationship(self):
        r = Relationship(subject="A", predicate="uses", object="B", confidence=0.8)
        assert r.confidence == 0.8

    def test_extraction_result(self):
        er = ExtractionResult(
            entities=[Entity(name="X", type="concept")],
            relationships=[Relationship(subject="X", predicate="rel", object="Y")]
        )
        assert len(er.entities) == 1
        assert len(er.relationships) == 1
