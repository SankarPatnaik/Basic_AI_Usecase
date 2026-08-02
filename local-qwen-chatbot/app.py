from __future__ import annotations

from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from chatbot import ASSISTANT_MODES, build_chat_messages, export_markdown
from ollama_client import OllamaChatError, OllamaSettings, chat
from pdf_documents import pdf_chunks, save_uploaded_pdf
from pdf_rag import answer_pdf_question
from trip_planner import (
    TripRequest,
    build_search_query,
    build_trip_follow_up_messages,
    build_trip_messages,
)
from vector_store import RAGSettings, ingest_pdf, stored_chunk_count
from web_research import research_web


load_dotenv()

st.set_page_config(page_title="Local Qwen Assistant", page_icon="Q")
st.title("Local Qwen Assistant")
st.caption("A local Qwen chatbot with PDF RAG and internet-assisted trip planning.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_rag_messages" not in st.session_state:
    st.session_state.pdf_rag_messages = []
if "pdf_sources" not in st.session_state:
    st.session_state.pdf_sources = []
if "last_pdf_path" not in st.session_state:
    st.session_state.last_pdf_path = ""
if "trip_messages" not in st.session_state:
    st.session_state.trip_messages = []
if "trip_pages" not in st.session_state:
    st.session_state.trip_pages = []
if "trip_warnings" not in st.session_state:
    st.session_state.trip_warnings = []

settings = OllamaSettings.from_env()
rag_settings = RAGSettings.from_env()

with st.sidebar:
    st.header("Local model")
    model = st.text_input("Model", value=settings.model)
    base_url = st.text_input("Ollama URL", value=settings.base_url)
    mode = st.selectbox("Assistant mode", list(ASSISTANT_MODES.keys()))
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.05)
    num_predict = st.slider("Max output tokens", 100, 2000, 800, 100)

    if st.button("Clear assistant chat"):
        st.session_state.messages = []
        st.rerun()

    st.download_button(
        "Download transcript",
        export_markdown(st.session_state.messages),
        file_name="local_qwen_chat.md",
        mime="text/markdown",
        disabled=not st.session_state.messages,
    )

active_settings = OllamaSettings(
    base_url=base_url,
    model=model,
    timeout_seconds=settings.timeout_seconds,
)

pdf_tab, assistant_tab, travel_tab = st.tabs(["PDF RAG", "Assistant chat", "Trip planner"])

with pdf_tab:
    st.subheader("Ask questions about an uploaded PDF")
    st.caption("PDF text is chunked, embedded locally, stored in ChromaDB, and answered by local Qwen.")

    pdf_upload_dir = Path(rag_settings.upload_dir)

    col_a, col_b, col_c = st.columns(3)
    try:
        col_a.metric("Stored PDF chunks", stored_chunk_count(rag_settings))
    except Exception as exc:
        col_a.warning(f"ChromaDB not ready: {exc}")
    col_b.metric("Top K", rag_settings.top_k)
    col_c.metric("Chunk size", rag_settings.chunk_size)

    uploaded_pdf = st.file_uploader("Upload one PDF", type=["pdf"])
    reset_vectors = st.checkbox("Replace existing PDF vectors", value=True)

    if st.button("Ingest PDF into ChromaDB", disabled=uploaded_pdf is None):
        try:
            with st.spinner("Reading PDF, creating chunks and embeddings..."):
                saved_path = save_uploaded_pdf(uploaded_pdf, pdf_upload_dir)
                chunk_count = ingest_pdf(saved_path, settings=rag_settings, reset=reset_vectors)
                st.session_state.last_pdf_path = saved_path.as_posix()
                st.session_state.pdf_rag_messages = []
                st.session_state.pdf_sources = []
            st.success(f"Stored {chunk_count} chunks from {saved_path.name}.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.last_pdf_path:
        st.caption(f"Last ingested PDF: {st.session_state.last_pdf_path}")
        with st.expander("Preview extracted chunks"):
            try:
                chunks = pdf_chunks(Path(st.session_state.last_pdf_path))
                for chunk in chunks[:8]:
                    st.markdown(
                        f"**Page {chunk.page}, chunk {chunk.chunk}** "
                        f"({chunk.characters} characters)"
                    )
                    st.write(chunk.text[:900])
                if len(chunks) > 8:
                    st.caption("Showing the first 8 chunks only.")
            except Exception as exc:
                st.warning(f"Could not preview chunks: {exc}")

    top_k = st.slider("PDF chunks to retrieve", 1, 8, rag_settings.top_k)

    if st.button("Clear PDF RAG chat"):
        st.session_state.pdf_rag_messages = []
        st.session_state.pdf_sources = []
        st.rerun()

    st.download_button(
        "Download PDF RAG chat",
        export_markdown(st.session_state.pdf_rag_messages),
        file_name="pdf_rag_chat.md",
        mime="text/markdown",
        disabled=not st.session_state.pdf_rag_messages,
    )

    for message in st.session_state.pdf_rag_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if st.session_state.pdf_sources:
        with st.expander("Retrieved PDF evidence"):
            for index, source in enumerate(st.session_state.pdf_sources, start=1):
                st.markdown(
                    f"**[PDF {index}] {source['source']} - page {source['page']}, "
                    f"chunk {source['chunk']}**"
                )
                st.caption(f"Cosine distance: {source['distance']:.3f}")
                st.write(source["text"])

    with st.form("pdf_question_form", clear_on_submit=True):
        pdf_question = st.text_area(
            "Ask a question about the uploaded PDF",
            placeholder="Example: What are the main terms mentioned in this document?",
            height=90,
        )
        asked_pdf_question = st.form_submit_button("Ask PDF")

    if asked_pdf_question:
        if not pdf_question.strip():
            st.warning("Enter a PDF question first.")
        else:
            try:
                with st.spinner("Retrieving PDF chunks and asking local Qwen..."):
                    result = answer_pdf_question(
                        pdf_question,
                        active_settings,
                        rag_settings=rag_settings,
                        top_k=top_k,
                        temperature=min(temperature, 0.2),
                        num_predict=num_predict,
                    )
                st.session_state.pdf_rag_messages.append(
                    {"role": "user", "content": pdf_question}
                )
                st.session_state.pdf_rag_messages.append(
                    {"role": "assistant", "content": result.answer}
                )
                st.session_state.pdf_sources = result.sources
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with assistant_tab:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_message = st.chat_input("Ask for help with any task")

    if user_message:
        st.session_state.messages.append({"role": "user", "content": user_message})
        with st.chat_message("user"):
            st.write(user_message)

        messages_for_model = build_chat_messages(st.session_state.messages, mode)

        with st.chat_message("assistant"):
            with st.spinner("Thinking locally..."):
                try:
                    answer = chat(
                        messages_for_model,
                        active_settings,
                        temperature=temperature,
                        num_predict=num_predict,
                    )
                    st.write(answer)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                except OllamaChatError as exc:
                    st.error(str(exc))

with travel_tab:
    st.subheader("Internet-assisted vacation planner")
    st.caption("Research travel pages, then let local Qwen build and refine the itinerary.")

    with st.form("trip_planner_form"):
        col_a, col_b = st.columns(2)
        destination = col_a.text_input("Destination", placeholder="Tokyo, Japan")
        dates = col_b.text_input("Dates or duration", placeholder="5 days in October")
        starting_city = col_a.text_input("Starting city", placeholder="Bengaluru")
        travelers = col_b.text_input("Travelers", value="2 adults")
        budget = col_a.selectbox("Budget", ["budget", "moderate", "premium"])
        pace = col_b.selectbox("Pace", ["relaxed", "balanced", "packed"])
        interests = st.text_area(
            "Interests",
            placeholder="Food, museums, nature, shopping, local culture",
            height=80,
        )
        notes = st.text_area(
            "Constraints or preferences",
            placeholder="Vegetarian food, avoid late nights, kid friendly, public transport only",
            height=80,
        )
        urls_text = st.text_area(
            "Optional websites to crawl",
            placeholder="Paste official tourism, hotel, event or attraction URLs here.",
            height=90,
        )
        col_c, col_d = st.columns(2)
        use_search = col_c.checkbox("Search the web automatically", value=True)
        max_pages = col_d.slider("Pages to read", 1, 6, 4)
        planned = st.form_submit_button("Research and plan trip")

    if planned:
        if not destination.strip() or not dates.strip():
            st.warning("Destination and dates/duration are required.")
        else:
            request = TripRequest(
                destination=destination,
                dates=dates,
                starting_city=starting_city,
                travelers=travelers,
                budget=budget,
                interests=interests,
                pace=pace,
                notes=notes,
            )
            query = build_search_query(request)

            with st.spinner("Searching and reading travel pages..."):
                pages, warnings = research_web(
                    query=query,
                    urls_text=urls_text,
                    use_search=use_search,
                    max_pages=max_pages,
                )
                st.session_state.trip_pages = pages
                st.session_state.trip_warnings = warnings

            with st.spinner("Asking local Qwen to build the itinerary..."):
                try:
                    answer = chat(
                        build_trip_messages(request, st.session_state.trip_pages),
                        active_settings,
                        temperature=temperature,
                        num_predict=max(num_predict, 1200),
                    )
                    st.session_state.trip_messages = [
                        {
                            "role": "user",
                            "content": (
                                f"Plan a {dates} trip to {destination} for "
                                f"{travelers}. Interests: {interests or 'not provided'}"
                            ),
                        },
                        {"role": "assistant", "content": answer},
                    ]
                except OllamaChatError as exc:
                    st.error(str(exc))

    if st.session_state.trip_warnings:
        with st.expander("Research notes"):
            for warning in st.session_state.trip_warnings:
                st.warning(warning)

    if st.session_state.trip_pages:
        with st.expander("Web sources used"):
            for index, page in enumerate(st.session_state.trip_pages, start=1):
                st.markdown(f"**[WEB {index}] {page.title}**")
                st.caption(page.url)
                st.write(page.text[:700] + ("..." if len(page.text) > 700 else ""))

    for message in st.session_state.trip_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    st.download_button(
        "Download trip plan",
        export_markdown(st.session_state.trip_messages),
        file_name="qwen_trip_plan.md",
        mime="text/markdown",
        disabled=not st.session_state.trip_messages,
    )

    with st.form("trip_follow_up_form", clear_on_submit=True):
        follow_up = st.text_area(
            "Ask a follow-up about this trip",
            placeholder="Make it cheaper, add vegetarian restaurants, or reduce travel time.",
            height=80,
        )
        asked_follow_up = st.form_submit_button("Ask follow-up")

    if asked_follow_up:
        if not st.session_state.trip_messages:
            st.warning("Create a trip plan first.")
        elif not follow_up.strip():
            st.warning("Enter a follow-up question first.")
        else:
            try:
                answer = chat(
                    build_trip_follow_up_messages(
                        st.session_state.trip_messages,
                        st.session_state.trip_pages,
                        follow_up,
                    ),
                    active_settings,
                    temperature=temperature,
                    num_predict=num_predict,
                )
                st.session_state.trip_messages.append(
                    {"role": "user", "content": follow_up}
                )
                st.session_state.trip_messages.append(
                    {"role": "assistant", "content": answer}
                )
                st.rerun()
            except OllamaChatError as exc:
                st.error(str(exc))
