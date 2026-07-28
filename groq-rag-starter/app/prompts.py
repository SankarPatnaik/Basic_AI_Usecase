from __future__ import annotations

from typing import Any


def build_context(results: list[dict[str, Any]]) -> str:
    sections = []
    for index, item in enumerate(results, start=1):
        sections.append(
            f"[SOURCE {index}: {item['source']}, page {item['page']}]\n{item['text']}"
        )
    return "\n\n".join(sections)
