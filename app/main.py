from fastapi import FastAPI
from pydantic import BaseModel

from app.rag.service import RAGService


app = FastAPI(
    title="SolarIQ",
    description="Real-Time Solar Energy Intelligence Agent",
    version="0.1.0",
)


class RAGQuery(BaseModel):
    query: str
    top_k: int = 3


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "SolarIQ",
        "version": "0.1.0",
    }


@app.post("/rag/query")
def rag_query(request: RAGQuery):
    service = RAGService()

    return service.retrieve(
        query=request.query,
        top_k=request.top_k,
    )