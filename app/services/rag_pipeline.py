
import os
from typing import List, Tuple, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import DocumentEmbedding
import httpx

# Get embedding for query using Ollama API
async def get_query_embedding(query: str) -> List[float]:
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL")
    if not ollama_base_url or not ollama_embedding_model:
        raise RuntimeError("OLLAMA_BASE_URL and OLLAMA_EMBEDDING_MODEL must be set in .env")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ollama_base_url}/api/embeddings",
            json={"model": ollama_embedding_model, "prompt": query}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("embedding", [0.0] * 384)
    return [0.0] * 384



# Vector search with domain filtering and chunk metadata
async def vector_search(db: AsyncSession, query: str, domain_id: str, top_k: int = 10) -> List[dict]:
    query_embedding = await get_query_embedding(query)
    # Filter by domain before vector search
    from app.db.models import DocumentEmbedding, Document
    stmt = (
        select(DocumentEmbedding)
        .join(Document, DocumentEmbedding.document_id == Document.id)
        .where(DocumentEmbedding.vector != None)
        .where(Document.domain_id == domain_id)
        .order_by(DocumentEmbedding.vector.l2_distance(query_embedding))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    embeddings = result.scalars().all()
    # Return chunk text and metadata for citation
    return [{"chunk_text": e.chunk_text, "document_id": str(e.document_id), "chunk_id": str(e.id)} for e in embeddings if hasattr(e, "chunk_text")]


# LLM-based reranking of chunks
async def rerank_chunks_with_llm(chunks: List[dict], question: str, ollama_base_url: str, ollama_model: str, top_k: int = 5) -> List[dict]:
    if not chunks:
        return []
    # Build rerank prompt with chunk IDs
    context = "\n".join([f"{i+1}. {chunk['chunk_text']} (Chunk ID: {chunk['chunk_id']})" for i, chunk in enumerate(chunks)])
    prompt = (
        f"Given the following context chunks and the question, rank the chunks by relevance to the question.\n"
        f"Chunks:\n{context}\n\nQuestion: {question}\n"
        "Return the most relevant chunk numbers as a comma-separated list."
    )
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ollama_base_url}/api/generate",
            json={"model": ollama_model, "prompt": prompt, "stream": False}
        )
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "")
            # Parse chunk numbers from LLM response
            import re
            match = re.findall(r'\d+', answer)
            indices = [int(i)-1 for i in match if 0 < int(i) <= len(chunks)]
            reranked = [chunks[i] for i in indices][:top_k]
            if reranked:
                return reranked
    # Fallback: return original top_k
    return chunks[:top_k]





# LLM answer generation using Ollama API with hallucination guard and citations
async def generate_answer(chunks: List[dict], question: str, max_context_chars: int = 4000) -> Tuple[str, float, List[dict]]:
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    ollama_model = os.getenv("OLLAMA_MODEL")
    if not ollama_base_url or not ollama_model:
        raise RuntimeError("OLLAMA_BASE_URL and OLLAMA_MODEL must be set in .env")
    context_chunks = []
    total_chars = 0
    used_chunk_ids = set()
    for i, chunk in enumerate(chunks):
        chunk_text = chunk["chunk_text"]
        chunk_id = chunk["chunk_id"]
        # Avoid duplicate chunks
        if chunk_id in used_chunk_ids:
            continue
        entry = f"Chunk {i+1} (ID: {chunk_id}): {chunk_text}"
        if total_chars + len(entry) > max_context_chars:
            break
        context_chunks.append(entry)
        total_chars += len(entry)
        used_chunk_ids.add(chunk_id)
    context = "\n\n".join(context_chunks)

    prompt = (
        f"Context (with chunk IDs for citation):\n{context}\n\nQuestion: {question}\n\n"
        "Instructions: Only answer using the context above. If the answer is present, cite the chunk ID. If not, reply 'I don't know.' Do not make up information."
        "\nAnswer:"
    )
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ollama_base_url}/api/generate",
            json={"model": ollama_model, "prompt": prompt, "stream": False}
        )
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "")
            # Log raw LLM response for debugging
            import logging
            logging.getLogger("rag_pipeline").info(f"LLM raw response: {answer}")
            # Confidence estimation: simple heuristic (can be improved)
            confidence = 0.9 if answer and "I don't know" not in answer else 0.0
            return answer, confidence, chunks
    return "", 0.0, chunks



async def rag_pipeline(
    db: AsyncSession,
    question: str,
    domain_id: str,
    top_k: int = 5
) -> Tuple[str, float, List[dict]]:
    # Step 1: Retrieve relevant chunks with domain filtering and metadata
    initial_chunks = await vector_search(db, question, domain_id, top_k=10)
    if not initial_chunks:
        return "No relevant documents found.", 0.0, []
    # Step 2: Rerank with LLM
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    ollama_model = os.getenv("OLLAMA_MODEL")
    if not ollama_base_url or not ollama_model:
        raise RuntimeError("OLLAMA_BASE_URL and OLLAMA_MODEL must be set in .env")
    reranked_chunks = await rerank_chunks_with_llm(initial_chunks, question, ollama_base_url, ollama_model, top_k=top_k)
    # Step 3: Generate answer using LLM with hallucination guard and citations
    answer, confidence, source_docs = await generate_answer(reranked_chunks, question)
    return answer, confidence, source_docs
