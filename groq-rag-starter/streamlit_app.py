import streamlit as st

from app.rag import answer_question
from app.vector_store import collection, ingest_folder

st.set_page_config(page_title="Groq RAG Student Project", page_icon="📚")
st.title("📚 My First RAG Assistant")
st.caption("ChromaDB + local embeddings + Groq API")

with st.sidebar:
    st.header("Knowledge Base")
    st.write(f"Stored chunks: **{collection().count()}**")
    if st.button("Rebuild vector database"):
        try:
            count = ingest_folder("data", reset=True)
            st.success(f"Stored {count} chunks.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

question = st.text_area(
    "Ask a question about the documents",
    placeholder="Example: How many annual leave days are available?",
)
top_k = st.slider("Chunks to retrieve", 1, 8, 4)

if st.button("Ask", type="primary"):
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        try:
            with st.spinner("Retrieving context and asking Groq..."):
                result = answer_question(question, top_k)
            st.subheader("Answer")
            st.write(result.answer)
            st.subheader("Evidence")
            for index, item in enumerate(result.sources, start=1):
                with st.expander(
                    f"SOURCE {index}: {item['source']} - page {item['page']}"
                ):
                    st.write(item["text"])
                    st.caption(f"Cosine distance: {item['distance']:.3f}")
        except Exception as exc:
            st.error(str(exc))
