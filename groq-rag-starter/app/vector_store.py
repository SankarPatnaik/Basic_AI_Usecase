from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.documents import SUPPORTED_EXTENSIONS, chunk_text, read_document


@lru_cache(maxsize=1)
def embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def collection():
    client = chromadb.PersistentClient(path=settings.chroma_path)
    return client.get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_folder(data_folder: str = "data", reset: bool = False) -> int:
    store = collection()
    if reset:
        existing = store.get(include=[])
        if existing.get("ids"):
            store.delete(ids=existing["ids"])

    paths = sorted(
        p for p in Path(data_folder).iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not paths:
        raise FileNotFoundError(f"No TXT, PDF or DOCX files found in {data_folder!r}")

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for path in paths:
        for page, text in read_document(path):
            for chunk_number, chunk in enumerate(chunk_text(text)):
                ids.append(f"{path.name}:p{page}:c{chunk_number}")
                documents.append(chunk)
                metadatas.append(
                    {"source": path.name, "page": page, "chunk": chunk_number}
                )

    if not documents:
        raise ValueError("Documents were found, but no readable text was extracted.")

    vectors = embedding_model().encode(
        documents, normalize_embeddings=True, show_progress_bar=True
    ).tolist()
    store.upsert(ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas)
    return len(documents)


def search(question: str, top_k: int | None = None) -> list[dict[str, Any]]:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    store = collection()
    if store.count() == 0:
        raise RuntimeError("The vector database is empty. Run: python ingest.py")

    query_vector = embedding_model().encode(
        [question], normalize_embeddings=True
    ).tolist()
    result = store.query(
        query_embeddings=query_vector,
        n_results=top_k or settings.top_k,
        include=["documents", "metadatas", "distances"],
    )

    rows: list[dict[str, Any]] = []
    for document, metadata, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        rows.append(
            {
                "text": document,
                "source": metadata.get("source", "unknown"),
                "page": metadata.get("page", 1),
                "chunk": metadata.get("chunk", 0),
                "distance": float(distance),
            }
        )
    return rows
