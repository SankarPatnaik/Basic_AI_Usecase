from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.config import settings
from app.documents import SUPPORTED_EXTENSIONS, document_chunks, safe_filename
from app.rag import answer_question, chat_with_groq
from app.vector_store import collection, ingest_folder, ingest_paths


DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
PROVIDER_OPTIONS = {
    "Groq API": "groq",
    "Local Qwen through Ollama": "local_qwen",
}


def save_uploaded_pdfs(uploaded_files) -> list[Path]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []
    for uploaded_file in uploaded_files:
        target = UPLOAD_DIR / safe_filename(uploaded_file.name)
        target.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(target)
    return saved_paths


def available_documents() -> list[Path]:
    if not DATA_DIR.exists():
        return []
    return sorted(
        path
        for path in DATA_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def render_sources(sources: list[dict]) -> None:
    st.subheader("Retrieved evidence")
    for index, item in enumerate(sources, start=1):
        label = f"Source {index}: {item['source']} - page {item['page']}"
        with st.expander(label):
            st.write(item["text"])
            st.caption(f"Cosine distance: {item['distance']:.3f}")


def render_chat_history(history: list[dict[str, str]]) -> None:
    for message in history:
        with st.chat_message(message["role"]):
            st.write(message["content"])


st.set_page_config(page_title="Student RAG Lab", page_icon="R")
st.title("Student RAG Lab")
st.caption("Upload PDFs, inspect chunks, ask grounded questions, and compare Groq with local Qwen.")

if "rag_history" not in st.session_state:
    st.session_state.rag_history = []
if "groq_chat_history" not in st.session_state:
    st.session_state.groq_chat_history = []

with st.sidebar:
    st.header("Knowledge base")
    try:
        st.metric("Stored chunks", collection().count())
    except Exception as exc:
        st.error(f"ChromaDB is not ready: {exc}")

    uploaded_pdfs = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Uploaded PDFs are saved under data/uploads and can be inspected later.",
    )
    reset_upload = st.checkbox("Replace existing vectors before upload")
    if st.button("Add uploaded PDFs", disabled=not uploaded_pdfs):
        try:
            saved = save_uploaded_pdfs(uploaded_pdfs)
            count = ingest_paths(saved, reset=reset_upload)
            st.success(f"Stored {count} chunks from {len(saved)} PDF file(s).")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if st.button("Rebuild from data folder"):
        try:
            count = ingest_folder("data", reset=True)
            st.success(f"Stored {count} chunks from data/.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.divider()
    st.header("Generation model")
    provider_label = st.radio("Provider", list(PROVIDER_OPTIONS.keys()))
    provider = PROVIDER_OPTIONS[provider_label]
    if provider == "groq":
        selected_model = st.text_input(
            "Groq model",
            value=settings.groq_model,
            key="selected_groq_model",
        )
    else:
        selected_model = st.text_input(
            "Ollama Qwen model",
            value=settings.local_qwen_model,
            key="selected_qwen_model",
        )
        st.caption("Requires Ollama running locally.")
    top_k = st.slider("Chunks to retrieve", 1, 8, settings.top_k)

rag_tab, chunks_tab, chat_tab, teaching_tab = st.tabs(
    ["Ask PDF RAG", "Chunking demo", "Groq chat", "Teaching guide"]
)

with rag_tab:
    st.subheader("Ask a question over uploaded or sample documents")
    with st.form("rag_question_form"):
        question = st.text_area(
            "Question",
            placeholder="Example: What policy applies to annual leave?",
            height=110,
        )
        submitted = st.form_submit_button("Ask with RAG")

    if submitted:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            try:
                with st.spinner("Retrieving chunks and generating an answer..."):
                    result = answer_question(
                        question,
                        top_k=top_k,
                        provider=provider,
                        model=selected_model,
                    )
                st.session_state.rag_history.append(
                    {
                        "question": question,
                        "answer": result.answer,
                        "sources": result.sources,
                        "provider": provider_label,
                        "model": selected_model,
                    }
                )
            except Exception as exc:
                st.error(str(exc))

    if st.session_state.rag_history:
        latest = st.session_state.rag_history[-1]
        st.subheader("Answer")
        st.caption(f"{latest['provider']} - {latest['model']}")
        st.write(latest["answer"])
        render_sources(latest["sources"])

        with st.expander("Previous RAG questions"):
            for item in reversed(st.session_state.rag_history[:-1]):
                st.markdown(f"**Q:** {item['question']}")
                st.markdown(f"**A:** {item['answer']}")
                st.caption(f"{item['provider']} - {item['model']}")

with chunks_tab:
    st.subheader("Show students how document chunking works")
    paths = available_documents()
    if not paths:
        st.info("Add a TXT, PDF or DOCX file to data/ or upload a PDF first.")
    else:
        labels = [path.as_posix() for path in paths]
        selected_path = Path(st.selectbox("Document", labels))
        chunk_size = st.slider("Chunk size", 300, 1500, 900, 50)
        max_overlap = min(400, chunk_size - 50)
        overlap = st.slider("Overlap", 0, max_overlap, min(150, max_overlap), 25)
        chunks = document_chunks(selected_path, chunk_size=chunk_size, overlap=overlap)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Chunks created", len(chunks))
        col_b.metric("Chunk size", chunk_size)
        col_c.metric("Overlap", overlap)

        replace_selected = st.checkbox("Replace existing vectors before storing this document")
        if st.button("Store selected document in ChromaDB"):
            try:
                count = ingest_paths([selected_path], reset=replace_selected)
                st.success(f"Stored {count} chunks from {selected_path.name}.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if not chunks:
            st.warning("No readable text was extracted from this document.")
        for chunk in chunks[:12]:
            title = (
                f"Page {chunk['page']} - chunk {chunk['chunk']} "
                f"({chunk['characters']} characters)"
            )
            with st.expander(title):
                st.write(chunk["text"])
        if len(chunks) > 12:
            st.caption("Showing the first 12 chunks only.")

with chat_tab:
    st.subheader("Interactive chat with Groq API")
    st.caption("This tab is a normal chat loop. It does not retrieve document context.")

    groq_chat_model = st.text_input(
        "Groq chat model",
        value=settings.groq_model,
        key="groq_chat_model",
    )
    if st.button("Clear Groq chat"):
        st.session_state.groq_chat_history = []
        st.rerun()

    render_chat_history(st.session_state.groq_chat_history)

    with st.form("groq_chat_form", clear_on_submit=True):
        chat_message = st.text_area(
            "Message",
            placeholder="Ask the model to explain embeddings to a beginner.",
            height=90,
        )
        sent = st.form_submit_button("Send to Groq")

    if sent:
        if not chat_message.strip():
            st.warning("Enter a chat message first.")
        else:
            try:
                st.session_state.groq_chat_history.append(
                    {"role": "user", "content": chat_message}
                )
                with st.spinner("Calling Groq..."):
                    assistant_message = chat_with_groq(
                        st.session_state.groq_chat_history,
                        model=groq_chat_model,
                    )
                st.session_state.groq_chat_history.append(
                    {"role": "assistant", "content": assistant_message}
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with teaching_tab:
    st.subheader("Classroom walkthrough")
    st.markdown(
        """
1. Upload a PDF in the sidebar and store it in ChromaDB.
2. Open the chunking demo and show how one document becomes many smaller chunks.
3. Ask a question in the RAG tab and inspect which chunks were retrieved.
4. Switch between Groq API and local Qwen to show that retrieval stays the same while generation changes.
5. Open the Groq chat tab to show a plain chat loop without retrieval.
"""
    )

    st.subheader("Local Qwen setup")
    st.code(
        """# Install Ollama from https://ollama.com
ollama pull qwen2.5:3b
ollama serve

# Optional .env settings
LOCAL_QWEN_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://localhost:11434""",
        language="bash",
    )

    st.subheader("Groq chat loop steps")
    st.markdown(
        """
1. Store the conversation in `st.session_state`.
2. Append each student message as `{"role": "user", "content": message}`.
3. Send the full message list to `client.chat.completions.create(...)`.
4. Append the model reply as `{"role": "assistant", "content": reply}`.
5. Render the history with `st.chat_message(...)`.
"""
    )

    st.code(
        """from groq import Groq

client = Groq(api_key=settings.groq_api_key)
response = client.chat.completions.create(
    model=settings.groq_model,
    messages=st.session_state.groq_chat_history,
)
reply = response.choices[0].message.content""",
        language="python",
    )
