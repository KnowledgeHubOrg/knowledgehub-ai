
import os
from typing import List, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import DocumentEmbedding
import httpx

# Get embedding for query using Ollama API
async def get_query_embedding(query: str) -> List[float]:
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    ollama_model = os.getenv("OLLAMA_MODEL")
    if not ollama_base_url or not ollama_model:
        raise RuntimeError("OLLAMA_BASE_URL and OLLAMA_MODEL must be set in .env")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ollama_base_url}/api/embeddings",
            json={"model": ollama_model, "prompt": query}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("embedding", [0.0] * 384)
    return [0.0] * 384

# Vector search using pgvector ANN
async def vector_search(db: AsyncSession, query: str, domain_id: str, top_k: int = 5) -> List[str]:
    query_embedding = await get_query_embedding(query)
    # pgvector ANN search: ORDER BY vector <=> query_embedding LIMIT top_k
    stmt = (
        select(DocumentEmbedding)
        .where(DocumentEmbedding.vector != None)
        .where(DocumentEmbedding.document_id.in_(
            select(DocumentEmbedding.document_id).where(DocumentEmbedding.document_id != None)
        ))
        .order_by(DocumentEmbedding.vector.l2_distance(query_embedding))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    embeddings = result.scalars().all()
    # Ensure we return actual strings, not SQLAlchemy columns
    return [str(e.chunk_text) for e in embeddings if hasattr(e, "chunk_text")]


# LLM answer generation using Ollama API
async def generate_answer(chunks: List[str], question: str) -> Tuple[str, float, List[str]]:
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    ollama_model = os.getenv("OLLAMA_MODEL")
    if not ollama_base_url or not ollama_model:
        raise RuntimeError("OLLAMA_BASE_URL and OLLAMA_MODEL must be set in .env")
    # Prepare context for LLM
    context = "\n\n".join(chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ollama_base_url}/api/generate",
            json={"model": ollama_model, "prompt": prompt}
        )
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "")
            # Confidence estimation: simple heuristic (can be improved)
            confidence = 0.9 if answer else 0.0
            return answer, confidence, chunks
    return "", 0.0, chunks

async def rag_pipeline(
    db: AsyncSession,
    question: str,
    domain_id: str,
    top_k: int = 5
) -> Tuple[str, float, List[str]]:
    # Step 1: Retrieve relevant chunks
    chunks = await vector_search(db, question, domain_id, top_k)
    if not chunks:
        return "No relevant documents found.", 0.0, []
    # Step 2: Generate answer using LLM
    answer, confidence, source_docs = await generate_answer(chunks, question)
    return answer, confidence, source_docs
