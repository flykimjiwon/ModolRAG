"""LLM-based entity and relationship extraction."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
import httpx


@dataclass
class Entity:
    name: str
    type: str  # person, org, concept, location, event
    description: str = ""

@dataclass
class Relationship:
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0  # 1.0=explicit, 0.7=strongly implied, 0.5=inferred

@dataclass
class ExtractionResult:
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


# Extraction prompt
EXTRACTION_PROMPT = '''Extract entities and relationships from the following text.

Return JSON with this exact format:
{{
  "entities": [
    {{"name": "Entity Name", "type": "person|org|concept|location|event", "description": "brief description"}}
  ],
  "relationships": [
    {{"subject": "Entity A", "predicate": "relationship verb", "object": "Entity B", "confidence": 0.7}}
  ]
}}

Confidence levels:
- 1.0: Explicitly stated in text
- 0.7: Strongly implied
- 0.5: Inferred from context

Entity types: person, org, concept, location, event

Text:
{text}

JSON:'''


def extract_wikilinks(text: str) -> list[Relationship]:
    """Extract [[wikilink]] patterns as explicit relationships."""
    if not text:
        return []
    pattern = r'\[\[([^\]]+)\]\]'
    raw_matches = re.findall(pattern, text)
    # Filter out empty/whitespace-only links and strip
    matches = [m.strip() for m in raw_matches if m.strip()]
    relationships = []
    for i, match in enumerate(matches):
        for j, other in enumerate(matches):
            if i != j:
                relationships.append(Relationship(
                    subject=match,
                    predicate="explicitly_linked",
                    object=other,
                    confidence=1.0,
                ))
    return relationships


async def extract_entities_and_relations(
    text: str,
    llm_endpoint: str = "http://localhost:11434/api/chat",
    model: str = "llama3",
    timeout: float = 120.0,
) -> ExtractionResult:
    """Extract entities and relationships from text using LLM.

    Supports Ollama chat API format.
    """
    result = ExtractionResult()

    # 1. Extract wikilinks first
    wikilink_rels = extract_wikilinks(text)
    result.relationships.extend(wikilink_rels)

    # 2. LLM extraction
    prompt = EXTRACTION_PROMPT.format(text=text[:4000])  # Truncate to avoid token limits

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                llm_endpoint,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Parse response — handle both Ollama and OpenAI formats
            content = ""
            if "message" in data:
                content = data["message"].get("content", "")
            elif "choices" in data:
                content = data["choices"][0]["message"]["content"]

            if content:
                parsed = _parse_llm_json(content)
                if parsed:
                    for e in parsed.get("entities", []):
                        result.entities.append(Entity(
                            name=e.get("name", ""),
                            type=e.get("type", "concept"),
                            description=e.get("description", ""),
                        ))
                    for r in parsed.get("relationships", []):
                        result.relationships.append(Relationship(
                            subject=r.get("subject", ""),
                            predicate=r.get("predicate", ""),
                            object=r.get("object", ""),
                            confidence=float(r.get("confidence", 0.7)),
                        ))
    except (httpx.HTTPError, httpx.TimeoutException, json.JSONDecodeError, KeyError):
        # LLM unavailable — return only wikilink results
        pass

    # Add wikilink entities
    wikilink_entities: set[str] = set()
    for rel in wikilink_rels:
        wikilink_entities.add(rel.subject)
        wikilink_entities.add(rel.object)
    for name in wikilink_entities:
        if not any(e.name == name for e in result.entities):
            result.entities.append(Entity(name=name, type="concept"))

    return result


def _parse_llm_json(text: str) -> dict | None:
    """Try to parse JSON from LLM output, handling markdown code blocks."""
    if not text or not text.strip():
        return None

    # Try direct parse
    try:
        result = json.loads(text)
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block (greedy to handle nested blocks)
    for pattern in [
        r'```json\s*\n(.*?)\n\s*```',
        r'```\s*\n(.*?)\n\s*```',
    ]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                return result if isinstance(result, dict) else None
            except json.JSONDecodeError:
                pass

    # Try finding JSON object — use greedy match for nested braces
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(0))
            return result if isinstance(result, dict) else None
        except json.JSONDecodeError:
            pass

    return None
