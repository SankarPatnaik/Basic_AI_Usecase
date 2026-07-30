from __future__ import annotations

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from chatbot import DEFAULT_MODE, build_chat_messages
from ollama_client import OllamaChatError, OllamaSettings, chat


def main() -> None:
    load_dotenv()
    settings = OllamaSettings.from_env()
    history: list[dict[str, str]] = []

    print("\nLocal Qwen Assistant")
    print(f"Model: {settings.model}")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        history.append({"role": "user", "content": question})
        try:
            answer = chat(build_chat_messages(history, DEFAULT_MODE), settings)
        except OllamaChatError as exc:
            print(f"\nError: {exc}\n")
            history.pop()
            continue

        history.append({"role": "assistant", "content": answer})
        print(f"\nAssistant: {answer}\n")


if __name__ == "__main__":
    main()
