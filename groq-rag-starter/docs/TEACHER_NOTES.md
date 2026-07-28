# Teacher Notes

## Suggested pace

- Session 1: AI, LLM, hallucination and RAG concepts
- Session 2: Python environment, packages and API-key security
- Session 3: documents, chunks and embeddings
- Session 4: ChromaDB ingestion and retrieval
- Session 5: Groq prompting and grounded answers
- Session 6: Streamlit, FastAPI and tests
- Session 7: student enhancement project

## Demonstration order

1. Ask Groq a question without document context.
2. Inspect the sample handbook.
3. Run ingestion.
4. Ask an exact question.
5. Ask a paraphrased question.
6. Ask an unsupported question.
7. Inspect retrieved chunks.
8. Change the sample document and re-ingest.

## Assessment rubric

| Area | Beginner | Competent | Strong |
|---|---|---|---|
| Concepts | Repeats definitions | Explains RAG flow | Explains design tradeoffs |
| Setup | Needs guidance | Runs independently | Helps debug another learner |
| Retrieval | Runs ingestion | Explains top-k and distance | Improves chunking/metadata |
| Generation | Calls Groq | Uses grounded prompt | Evaluates unsupported answers |
| Security | Knows key is secret | Uses `.env` correctly | Explains production secret management |
| Delivery | Runs one interface | Runs UI and API | Publishes clean GitHub repository |
