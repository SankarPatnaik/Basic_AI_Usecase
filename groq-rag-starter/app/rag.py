from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.prompts import build_context
from app.vector_store import search


@dataclass
class RAGResult:
    answer: str
    sources: list[dict[str, Any]]


def answer_question(question: str, top_k: int | None = None) -> RAGResult:
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Copy .env.example to .env and add your key."
        )

    sources = search(question, top_k)
    context = build_context(sources)
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)

    response = client.chat.completions.create(
        model=settings.groq_model,
        temperature=0.1,
        max_completion_tokens=700,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful RAG assistant. Answer only from the supplied "
                    "context. If the answer is not present, say: 'I could not find "
                    "that information in the provided documents.' Cite supporting "
                    "sources using [SOURCE 1], [SOURCE 2], and so on. Do not invent facts."
                ),
            },
            {
                "role": "user",
                "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}",
            },
        ],
    )
    answer = response.choices[0].message.content or "No answer was returned."
    return RAGResult(answer=answer, sources=sources)
