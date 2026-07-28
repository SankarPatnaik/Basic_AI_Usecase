from app.prompts import build_context


def test_context_contains_source_labels():
    context = build_context([
        {"source": "policy.txt", "page": 1, "text": "Leave is 24 days."}
    ])
    assert "SOURCE 1" in context
    assert "policy.txt" in context
    assert "Leave is 24 days" in context
