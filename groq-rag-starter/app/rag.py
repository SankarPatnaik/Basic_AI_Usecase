from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
import urllib.error
import urllib.request

from app.config import settings
from app.prompts import build_context
from app.vector_store import search


@dataclass
class RAGResult:
    answer: str
    sources: list[dict[str, Any]]


RAG_SYSTEM_PROMPT = (
    "You are a careful RAG assistant. Answer only from the supplied context. "
    "If the answer is not present, say: 'I could not find that information in "
    "the provided documents.' Cite supporting sources using [SOURCE 1], "
    "[SOURCE 2], and so on. Do not invent facts."
)

CHAT_SYSTEM_PROMPT = (
    "You are a concise teaching assistant. Explain clearly, ask useful follow-up "
    "questions when needed, and keep examples beginner friendly."
)


def _normalize_provider(provider: str) -> str:
    normalized = provider.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in {"groq", "groq_api"}:
        return "groq"
    if normalized in {"local", "local_qwen", "qwen", "ollama", "qwen_ollama"}:
        return "local_qwen"
    raise ValueError("Provider must be 'groq' or 'local_qwen'.")


def build_rag_messages(question: str, context: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}",
        },
    ]


def _call_groq(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 700,
) -> str:
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Copy .env.example to .env and add your key."
        )

    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)

    response = client.chat.completions.create(
        model=model or settings.groq_model,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content or "No answer was returned."


def _call_local_qwen(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 700,
) -> str:
    base_url = settings.ollama_base_url.rstrip("/")
    payload = {
        "model": model or settings.local_qwen_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    request = urllib.request.Request(
        f"{base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request, timeout=settings.ollama_timeout_seconds
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Local Qwen is selected, but Ollama is not reachable at "
            f"{base_url}. Install Ollama, run 'ollama pull "
            f"{model or settings.local_qwen_model}', then start Ollama."
        ) from exc

    message = data.get("message", {})
    return message.get("content") or data.get("response") or "No answer was returned."


def generate_text(
    messages: list[dict[str, str]],
    provider: str = "groq",
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 700,
) -> str:
    provider = _normalize_provider(provider)
    if provider == "groq":
        return _call_groq(messages, model, temperature, max_tokens)
    return _call_local_qwen(messages, model, temperature, max_tokens)


def answer_question(
    question: str,
    top_k: int | None = None,
    provider: str = "groq",
    model: str | None = None,
) -> RAGResult:
    sources = search(question, top_k)
    context = build_context(sources)
    answer = generate_text(
        build_rag_messages(question, context),
        provider=provider,
        model=model,
    )
    return RAGResult(answer=answer, sources=sources)


def chat_with_groq(
    history: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 700,
) -> str:
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}, *history]
    return _call_groq(messages, model=model, temperature=temperature, max_tokens=max_tokens)
