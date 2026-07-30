from __future__ import annotations

import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

from chatbot import ASSISTANT_MODES, build_chat_messages, export_markdown
from ollama_client import OllamaChatError, OllamaSettings, chat


load_dotenv()

st.set_page_config(page_title="Local Qwen Assistant", page_icon="Q")
st.title("Local Qwen Assistant")
st.caption("A simple local chatbot powered by Ollama and qwen2.5:3b.")

if "messages" not in st.session_state:
    st.session_state.messages = []

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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_message = st.chat_input("Ask for help with any task")

if user_message:
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.write(user_message)

    active_settings = OllamaSettings(
        base_url=base_url,
        model=model,
        timeout_seconds=settings.timeout_seconds,
    )
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
