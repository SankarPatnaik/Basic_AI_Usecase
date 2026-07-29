from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def read_document(path: Path) -> list[tuple[int, str]]:
    """Return a list of (page_or_section_number, text) pairs."""
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return [(1, path.read_text(encoding="utf-8"))]

    if suffix == ".pdf":
        reader = PdfReader(path)
        return [
            (page_number, page.extract_text() or "")
            for page_number, page in enumerate(reader.pages, start=1)
        ]

    if suffix == ".docx":
        document = Document(path)
        text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
        return [(1, text)]

    raise ValueError(f"Unsupported file type: {suffix}")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        if end < len(cleaned):
            boundary = max(cleaned.rfind("\n", start, end), cleaned.rfind(". ", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = end - overlap
    return chunks


def safe_filename(filename: str) -> str:
    """Return a simple filename that is safe to save under data/uploads."""
    path = Path(filename).name
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(path).stem).strip("_")
    suffix = re.sub(r"[^A-Za-z0-9.]+", "", Path(path).suffix)
    return f"{stem or 'uploaded_document'}{suffix}"


def document_chunks(
    path: Path,
    chunk_size: int = 900,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    """Read a document and return chunk records suitable for preview or storage."""
    chunks: list[dict[str, Any]] = []
    for page, text in read_document(path):
        for chunk_number, chunk in enumerate(
            chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        ):
            chunks.append(
                {
                    "source": path.name,
                    "page": page,
                    "chunk": chunk_number,
                    "text": chunk,
                    "characters": len(chunk),
                }
            )
    return chunks
