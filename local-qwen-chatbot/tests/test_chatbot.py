from chatbot import build_chat_messages, export_markdown, system_message


def test_system_message_uses_requested_mode():
    message = system_message("Code helper")

    assert message["role"] == "system"
    assert "programming assistant" in message["content"]


def test_build_chat_messages_adds_system_prompt_and_trims_history():
    history = [
        {"role": "user", "content": f"question {index}"}
        for index in range(5)
    ]

    messages = build_chat_messages(history, "General helper", max_history_messages=2)

    assert messages[0]["role"] == "system"
    assert [message["content"] for message in messages[1:]] == [
        "question 3",
        "question 4",
    ]


def test_export_markdown_contains_roles_and_content():
    markdown = export_markdown([
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ])

    assert "# Local Qwen Chat Transcript" in markdown
    assert "## User" in markdown
    assert "Hello" in markdown
    assert "## Assistant" in markdown
    assert "Hi there" in markdown
