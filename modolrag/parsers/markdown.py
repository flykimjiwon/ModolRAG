"""Markdown parser with YAML frontmatter support."""
from __future__ import annotations

import re

from modolrag.parsers.base import ParsedDocument, ParserBase

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_H2_SPLIT_RE = re.compile(r"(?=^## )", re.MULTILINE)


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and return (metadata_dict, remaining_content)."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    yaml_text = match.group(1)
    remaining = content[match.end():]

    try:
        import yaml  # PyYAML is a common stdlib-adjacent dep; use stdlib fallback if absent
        fm = yaml.safe_load(yaml_text) or {}
        if not isinstance(fm, dict):
            fm = {}
    except Exception:
        # Minimal key: value parser as fallback
        fm = {}
        for line in yaml_text.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip()

    return fm, remaining


class MarkdownParser(ParserBase):
    """Parse Markdown files, splitting by H2 headings into pages."""

    def supported_mime_types(self) -> list[str]:
        return ["text/markdown", "text/x-markdown"]

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            with open(file_path, encoding="utf-8") as fh:
                content = fh.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="latin-1") as fh:
                    content = fh.read()
            except Exception as exc:
                return ParsedDocument(text="", metadata={"error": str(exc)})
        except Exception as exc:
            return ParsedDocument(text="", metadata={"error": str(exc)})

        frontmatter, body = _parse_frontmatter(content)

        # Split body into sections at H2 boundaries
        raw_sections = _H2_SPLIT_RE.split(body)
        pages = [s.strip() for s in raw_sections if s.strip()]

        full_text = body.strip()
        metadata: dict = {"frontmatter": frontmatter}

        return ParsedDocument(text=full_text, metadata=metadata, pages=pages)
