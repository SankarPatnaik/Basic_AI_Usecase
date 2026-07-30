from __future__ import annotations

import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from chatbot import ASSISTANT_MODES, build_chat_messages, export_markdown
from ollama_client import OllamaChatError, OllamaSettings, chat
from trip_planner import (
    TripRequest,
    build_search_query,
    build_trip_follow_up_messages,
    build_trip_messages,
)
from web_research import research_web


load_dotenv()

st.set_page_config(page_title="Local Qwen Assistant", page_icon="Q")
st.title("Local Qwen Assistant")
st.caption("A local Qwen chatbot with an internet-assisted vacation planner.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "trip_messages" not in st.session_state:
    st.session_state.trip_messages = []
if "trip_pages" not in st.session_state:
    st.session_state.trip_pages = []
if "trip_warnings" not in st.session_state:
    st.session_state.trip_warnings = []

settings = OllamaSettings.from_env()

with st.sidebar:
    st.header("Local model")
    model = st.text_input("Model", value=settings.model)
    base_url = st.text_input("Ollama URL", value=settings.base_url)
    mode = st.selectbox("Assistant mode", list(ASSISTANT_MODES.keys()))
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.05)
    num_predict = st.slider("Max output tokens", 100, 2000, 800, 100)

    if st.button("Clear chat"):
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

assistant_tab, travel_tab = st.tabs(["Assistant chat", "Trip planner"])

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
