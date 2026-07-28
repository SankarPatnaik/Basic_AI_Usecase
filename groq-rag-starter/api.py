from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.rag import answer_question
from app.vector_store import collection

app = FastAPI(title="Beginner Groq RAG API", version="1.0.0")


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=8)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "stored_chunks": collection().count()}


@app.post("/ask")
def ask(request: QuestionRequest) -> dict:
    try:
        result = answer_question(request.question, request.top_k)
        return {"answer": result.answer, "sources": result.sources}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
