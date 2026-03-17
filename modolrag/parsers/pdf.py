"""PDF parser using pypdf + pdfplumber."""
from __future__ import annotations

from modolrag.parsers.base import ParsedDocument, ParserBase


class PdfParser(ParserBase):
    """Parse PDF files using pypdf for text and pdfplumber for tables."""

    def supported_mime_types(self) -> list[str]:
        return ["application/pdf"]

    def parse(self, file_path: str) -> ParsedDocument:
        try:
            import pypdf
            import pdfplumber
        except ImportError as e:
            return ParsedDocument(
                text="",
                metadata={"error": f"Missing dependency: {e}"},
            )

        pages: list[str] = []
        metadata: dict = {}

        # --- pypdf: metadata + basic text ---
        try:
            reader = pypdf.PdfReader(file_path)

            if reader.is_encrypted:
                return ParsedDocument(
                    text="",
                    metadata={"error": "PDF is encrypted", "page_count": 0},
                )

            info = reader.metadata or {}
            metadata["page_count"] = len(reader.pages)
            metadata["title"] = info.get("/Title", "") or ""
            metadata["author"] = info.get("/Author", "") or ""

        except Exception as exc:
            return ParsedDocument(
                text="",
                metadata={"error": str(exc)},
            )

        # --- pdfplumber: page text + tables ---
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    parts: list[str] = []

                    # Extract plain text
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        parts.append(page_text)

                    # Extract tables as markdown
                    for table in page.extract_tables():
                        if not table:
                            continue
                        md_rows: list[str] = []
                        for i, row in enumerate(table):
                            cells = [str(c or "") for c in row]
                            md_rows.append("| " + " | ".join(cells) + " |")
                            if i == 0:
                                md_rows.append(
                                    "| " + " | ".join(["---"] * len(cells)) + " |"
                                )
                        parts.append("\n".join(md_rows))

                    pages.append("\n\n".join(parts))

        except Exception as exc:
            metadata["pdfplumber_error"] = str(exc)
            # Fall back to pypdf text if pdfplumber fails
            try:
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    pages.append(page.extract_text() or "")
            except Exception:
                pass

        full_text = "\n\n".join(pages)
        return ParsedDocument(text=full_text, metadata=metadata, pages=pages)
