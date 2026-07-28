from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    chroma_path: str = os.getenv("CHROMA_PATH", "chroma_db")
    collection_name: str = os.getenv(
        "COLLECTION_NAME", "student_rag_documents"
    )
    top_k: int = int(os.getenv("TOP_K", "4"))


settings = Settings()
