from app.prompts import build_context
from app.rag import build_rag_messages


def test_context_contains_source_labels():
    context = build_context([
        {"source": "policy.txt", "page": 1, "text": "Leave is 24 days."}
    ])
    assert "SOURCE 1" in context
    assert "policy.txt" in context
    assert "Leave is 24 days" in context


def test_rag_messages_include_context_and_question():
    messages = build_rag_messages("How much leave?", "Leave is 24 days.")

    assert messages[0]["role"] == "system"
    assert "Answer only from the supplied context" in messages[0]["content"]
    assert "Leave is 24 days." in messages[1]["content"]
    assert "How much leave?" in messages[1]["content"]
