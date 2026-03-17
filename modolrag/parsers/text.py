"""Plain text parser with encoding detection."""
from __future__ import annotations

import os

from modolrag.parsers.base import ParsedDocument, ParserBase

_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]


class TextParser(ParserBase):
    """Parse plain text files with automatic encoding detection."""

    def supported_mime_types(self) -> list[str]:
        return [
            "text/plain",
            "text/csv",
            "text/tab-separated-values",
            "application/json",
            "application/xml",
            "text/xml",
            "text/html",
        ]

    def parse(self, file_path: str) -> ParsedDocument:
        text = ""
        detected_encoding = "unknown"

        for enc in _ENCODINGS:
            try:
                with open(file_path, encoding=enc, errors="strict") as fh:
                    text = fh.read()
                detected_encoding = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue
            except Exception as exc:
                return ParsedDocument(text="", metadata={"error": str(exc)})

        if not text and detected_encoding == "unknown":
            # Last resort: read with replacement
            try:
                with open(file_path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                detected_encoding = "utf-8 (with replacements)"
            except Exception as exc:
                return ParsedDocument(text="", metadata={"error": str(exc)})

        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            file_size = -1

        metadata: dict = {
            "file_size": file_size,
            "encoding": detected_encoding,
        }

        pages = [text] if text else []
        return ParsedDocument(text=text, metadata=metadata, pages=pages)
