import pytest

from app.documents import chunk_text, document_chunks, safe_filename


def test_short_text_is_one_chunk():
    assert chunk_text("A short paragraph.") == ["A short paragraph."]


def test_long_text_is_split():
    chunks = chunk_text("word " * 1000, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    assert all(chunks)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=100, overlap=100)


def test_safe_filename_removes_path_and_special_characters():
    assert safe_filename("../Policy 2026!.pdf") == "Policy_2026.pdf"


def test_document_chunks_include_teaching_metadata(tmp_path):
    path = tmp_path / "policy.txt"
    path.write_text("First paragraph. Second paragraph.", encoding="utf-8")

    chunks = document_chunks(path, chunk_size=100, overlap=10)

    assert chunks == [
        {
            "source": "policy.txt",
            "page": 1,
            "chunk": 0,
            "text": "First paragraph. Second paragraph.",
            "characters": 34,
        }
    ]
