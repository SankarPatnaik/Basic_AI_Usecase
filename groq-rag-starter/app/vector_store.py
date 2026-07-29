from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.documents import SUPPORTED_EXTENSIONS, document_chunks


@lru_cache(maxsize=1)
def embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def collection():
    client = chromadb.PersistentClient(path=settings.chroma_path)
    return client.get_or_create_collection(
        name=settings.collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def _clear_collection(store) -> None:
    existing = store.get(include=[])
    if existing.get("ids"):
        store.delete(ids=existing["ids"])


def ingest_paths(paths: Iterable[Path], reset: bool = False) -> int:
    selected_paths = sorted(Path(path) for path in paths)
    selected_paths = [
        path
        for path in selected_paths
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not selected_paths:
        raise FileNotFoundError("No TXT, PDF or DOCX files were selected for ingestion.")

    store = collection()
    if reset:
        _clear_collection(store)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for path in selected_paths:
        for row in document_chunks(path):
            ids.append(f"{path.as_posix()}:p{row['page']}:c{row['chunk']}")
            documents.append(row["text"])
            metadatas.append(
                {
                    "source": row["source"],
                    "page": row["page"],
                    "chunk": row["chunk"],
                }
            )

    if not documents:
        raise ValueError("Documents were found, but no readable text was extracted.")

    vectors = embedding_model().encode(
        documents, normalize_embeddings=True, show_progress_bar=True
    ).tolist()
    store.upsert(ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas)
    return len(documents)


def ingest_folder(data_folder: str = "data", reset: bool = False) -> int:
    folder = Path(data_folder)
    if not folder.exists():
        raise FileNotFoundError(f"No TXT, PDF or DOCX files found in {data_folder!r}")
    paths = sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not paths:
        raise FileNotFoundError(f"No TXT, PDF or DOCX files found in {data_folder!r}")
    return ingest_paths(paths, reset=reset)


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
