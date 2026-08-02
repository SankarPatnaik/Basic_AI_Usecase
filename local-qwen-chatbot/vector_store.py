from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from pdf_documents import PDFChunk, pdf_chunks


@dataclass(frozen=True)
class RAGSettings:
    chroma_path: str = "chroma_db"
    collection_name: str = "local_qwen_pdf_chunks"
    upload_dir: str = "uploads/pdf"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = 4
    chunk_size: int = 900
    chunk_overlap: int = 150

    @classmethod
    def from_env(cls) -> "RAGSettings":
        return cls(
            chroma_path=os.getenv("RAG_CHROMA_PATH", cls.chroma_path),
            collection_name=os.getenv("RAG_COLLECTION_NAME", cls.collection_name),
            upload_dir=os.getenv("RAG_UPLOAD_DIR", cls.upload_dir),
            embedding_model=os.getenv("EMBEDDING_MODEL", cls.embedding_model),
            top_k=int(os.getenv("RAG_TOP_K", str(cls.top_k))),
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE", str(cls.chunk_size))),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", str(cls.chunk_overlap))),
        )


@lru_cache(maxsize=1)
def embedding_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def collection(settings: RAGSettings | None = None):
    active = settings or RAGSettings.from_env()
    client = chromadb.PersistentClient(path=active.chroma_path)
    return client.get_or_create_collection(
        name=active.collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def clear_collection(settings: RAGSettings | None = None) -> None:
    store = collection(settings)
    existing = store.get(include=[])
    if existing.get("ids"):
        store.delete(ids=existing["ids"])


def _chunk_id(path: Path, chunk: PDFChunk) -> str:
    return f"{path.resolve().as_posix()}:p{chunk.page}:c{chunk.chunk}"


def ingest_pdf(
    path: Path,
    settings: RAGSettings | None = None,
    reset: bool = False,
) -> int:
    active = settings or RAGSettings.from_env()
    chunks = pdf_chunks(
        path,
        chunk_size=active.chunk_size,
        overlap=active.chunk_overlap,
    )
    store = collection(active)
    if reset:
        clear_collection(active)

    ids = [_chunk_id(path, chunk) for chunk in chunks]
    documents = [chunk.text for chunk in chunks]
    metadatas = [
        {
            "source": chunk.source,
            "page": chunk.page,
            "chunk": chunk.chunk,
            "characters": chunk.characters,
        }
        for chunk in chunks
    ]
    vectors = embedding_model(active.embedding_model).encode(
        documents,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()
    store.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=vectors)
    return len(chunks)


def stored_chunk_count(settings: RAGSettings | None = None) -> int:
    return collection(settings).count()


def search_pdf_chunks(
    question: str,
    settings: RAGSettings | None = None,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    active = settings or RAGSettings.from_env()
    store = collection(active)
    if store.count() == 0:
        raise RuntimeError("The PDF vector database is empty. Upload and ingest a PDF first.")

    query_vector = embedding_model(active.embedding_model).encode(
        [question],
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()
    result = store.query(
        query_embeddings=query_vector,
        n_results=top_k or active.top_k,
        include=["documents", "metadatas", "distances"],
    )

    rows: list[dict[str, Any]] = []
    for text, metadata, distance in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        rows.append(
            {
                "text": text,
                "source": metadata.get("source", "unknown.pdf"),
                "page": int(metadata.get("page", 0)),
                "chunk": int(metadata.get("chunk", 0)),
                "characters": int(metadata.get("characters", len(text))),
                "distance": float(distance),
            }
        )
    return rows
