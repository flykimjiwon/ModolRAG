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
