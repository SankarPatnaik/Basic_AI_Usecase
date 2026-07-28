import pytest

from app.documents import chunk_text


def test_short_text_is_one_chunk():
    assert chunk_text("A short paragraph.") == ["A short paragraph."]


def test_long_text_is_split():
    chunks = chunk_text("word " * 1000, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    assert all(chunks)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=100, overlap=100)
