from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


class OllamaChatError(RuntimeError):
    """Raised when the local Ollama server cannot return a chat response."""


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"
    timeout_seconds: float = 120

    @classmethod
    def from_env(cls) -> "OllamaSettings":
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", cls.base_url),
            model=os.getenv("OLLAMA_MODEL", cls.model),
            timeout_seconds=float(
                os.getenv("OLLAMA_TIMEOUT_SECONDS", str(cls.timeout_seconds))
            ),
        )


def chat(
    messages: list[dict[str, str]],
    settings: OllamaSettings,
    temperature: float = 0.3,
    num_predict: int = 800,
) -> str:
    payload = {
        "model": settings.model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }
    request = urllib.request.Request(
        f"{settings.base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=settings.timeout_seconds
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise OllamaChatError(f"Ollama returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise OllamaChatError(
            "Cannot reach Ollama. Start Ollama, then run: "
            f"ollama pull {settings.model}"
        ) from exc

    content = data.get("message", {}).get("content", "")
    if not content:
        raise OllamaChatError("Ollama returned an empty response.")
    return content.strip()
