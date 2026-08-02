from pdf_rag import build_pdf_context, build_pdf_rag_messages


def test_build_pdf_context_includes_page_and_source():
    context = build_pdf_context([
        {
            "source": "policy.pdf",
            "page": 3,
            "chunk": 1,
            "text": "Employees receive 24 days of leave.",
        }
    ])

    assert "policy.pdf" in context
    assert "page 3" in context
    assert "Employees receive 24 days" in context


def test_build_pdf_rag_messages_instruct_page_citations():
    messages = build_pdf_rag_messages(
        "How much leave is available?",
        [
            {
                "source": "policy.pdf",
                "page": 3,
                "chunk": 1,
                "text": "Employees receive 24 days of leave.",
            }
        ],
    )

    assert messages[0]["role"] == "system"
    assert "Cite page numbers" in messages[0]["content"]
    assert "How much leave is available?" in messages[1]["content"]
    assert "[PDF 1, page 3" in messages[1]["content"]
