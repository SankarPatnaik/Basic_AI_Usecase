from __future__ import annotations

from typing import Iterable


DEFAULT_MODE = "General helper"

ASSISTANT_MODES = {
    "General helper": (
        "You are a helpful local assistant. Support the user's task clearly and "
        "practically. Ask one short clarifying question only when it is needed. "
        "When useful, give steps, examples, or a concise checklist."
    ),
    "Study coach": (
        "You are a patient study coach. Explain ideas simply, use examples, and "
        "check understanding with short questions."
    ),
    "Code helper": (
        "You are a careful programming assistant. Explain the approach, provide "
        "small readable code examples, and point out likely errors."
    ),
    "Writing helper": (
        "You are a writing assistant. Improve clarity, structure, and tone while "
        "preserving the user's intent."
    ),
    "Planning helper": (
        "You are a planning assistant. Break work into practical steps, identify "
        "risks, and suggest the next best action."
    ),
}


def system_message(mode: str = DEFAULT_MODE) -> dict[str, str]:
    prompt = ASSISTANT_MODES.get(mode, ASSISTANT_MODES[DEFAULT_MODE])
    return {"role": "system", "content": prompt}


def build_chat_messages(
    history: Iterable[dict[str, str]],
    mode: str = DEFAULT_MODE,
    max_history_messages: int = 16,
) -> list[dict[str, str]]:
    recent_history = list(history)[-max_history_messages:]
    return [system_message(mode), *recent_history]


def export_markdown(messages: Iterable[dict[str, str]]) -> str:
    lines = ["# Local Qwen Chat Transcript", ""]
    for message in messages:
        role = message.get("role", "message").title()
        content = message.get("content", "").strip()
        lines.extend([f"## {role}", content, ""])
    return "\n".join(lines).strip() + "\n"
