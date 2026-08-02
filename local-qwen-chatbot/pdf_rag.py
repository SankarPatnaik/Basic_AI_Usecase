from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ollama_client import OllamaSettings, chat
from vector_store import RAGSettings, search_pdf_chunks


PDF_RAG_SYSTEM_PROMPT = (
    "You are a careful PDF RAG assistant. Answer only from the retrieved PDF "
    "context. If the context does not contain the answer, say that the answer "
    "was not found in the uploaded PDF. Cite page numbers using labels such as "
    "[PDF 1, page 3]. Do not invent facts."
)


@dataclass(frozen=True)
class PDFRAGResult:
    answer: str
    sources: list[dict[str, Any]]


def build_pdf_context(sources: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for index, source in enumerate(sources, start=1):
        sections.append(
            "[PDF {index}, page {page}, chunk {chunk}: {source}]\n{text}".format(
                index=index,
                page=source["page"],
                chunk=source["chunk"],
                source=source["source"],
                text=source["text"],
            )
        )
    return "\n\n".join(sections)


def build_pdf_rag_messages(
    question: str,
    sources: list[dict[str, Any]],
) -> list[dict[str, str]]:
    context = build_pdf_context(sources)
    return [
        {"role": "system", "content": PDF_RAG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"RETRIEVED PDF CONTEXT:\n{context}\n\n"
                f"QUESTION:\n{question}\n\n"
                "Answer with page citations. Keep the answer clear and practical."
            ),
        },
    ]


def answer_pdf_question(
    question: str,
    ollama_settings: OllamaSettings,
    rag_settings: RAGSettings | None = None,
    top_k: int | None = None,
    temperature: float = 0.1,
    num_predict: int = 900,
) -> PDFRAGResult:
    sources = search_pdf_chunks(question, settings=rag_settings, top_k=top_k)
    answer = chat(
        build_pdf_rag_messages(question, sources),
        ollama_settings,
        temperature=temperature,
        num_predict=num_predict,
    )
    return PDFRAGResult(answer=answer, sources=sources)
