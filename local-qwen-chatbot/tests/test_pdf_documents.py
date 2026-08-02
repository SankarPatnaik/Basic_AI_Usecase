import pytest

from pdf_documents import chunk_text, safe_filename


def test_safe_filename_keeps_pdf_extension_and_removes_path():
    assert safe_filename("../Employee Handbook 2026!.PDF") == "Employee_Handbook_2026.pdf"


def test_chunk_text_splits_long_text_with_overlap():
    chunks = chunk_text("word " * 300, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    assert all(chunks)


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=100, overlap=100)
