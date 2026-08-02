from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


MAX_UPLOAD_MB = 25


@dataclass(frozen=True)
class PDFChunk:
    source: str
    page: int
    chunk: int
    text: str
    characters: int


def safe_filename(filename: str) -> str:
    path = Path(filename).name
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(path).stem).strip("_")
    suffix = re.sub(r"[^A-Za-z0-9.]+", "", Path(path).suffix.lower())
    return f"{stem or 'uploaded_document'}{suffix or '.pdf'}"


def validate_pdf_path(path: Path) -> None:
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported in this RAG demo.")
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")


def clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def read_pdf_pages(path: Path) -> list[tuple[int, str]]:
    validate_pdf_path(path)
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported in this beginner demo.")

    pages: list[tuple[int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if text:
            pages.append((page_number, text))
    if not pages:
        raise ValueError(
            "No readable text was found. Scanned image PDFs need OCR before RAG."
        )
    return pages


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if overlap < 0:
        raise ValueError("overlap cannot be negative.")
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap.")

    cleaned = clean_text(text)
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        if end < len(cleaned):
            boundary = max(
                cleaned.rfind("\n", start, end),
                cleaned.rfind(". ", start, end),
            )
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = end - overlap
    return chunks


def pdf_chunks(
    path: Path,
    chunk_size: int = 900,
    overlap: int = 150,
) -> list[PDFChunk]:
    chunks: list[PDFChunk] = []
    for page_number, text in read_pdf_pages(path):
        for chunk_number, chunk in enumerate(
            chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        ):
            chunks.append(
                PDFChunk(
                    source=path.name,
                    page=page_number,
                    chunk=chunk_number,
                    text=chunk,
                    characters=len(chunk),
                )
            )
    if not chunks:
        raise ValueError("Text was extracted, but no chunks were created.")
    return chunks


def save_uploaded_pdf(uploaded_file, upload_dir: Path, max_mb: int = MAX_UPLOAD_MB) -> Path:
    filename = safe_filename(uploaded_file.name)
    if not filename.endswith(".pdf"):
        raise ValueError("Only PDF files are supported.")

    data = uploaded_file.getbuffer()
    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"PDF is too large. Maximum size is {max_mb} MB.")

    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / filename
    target.write_bytes(data)
    return target
