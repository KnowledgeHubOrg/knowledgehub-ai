
import os
import mimetypes
from typing import Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, DocumentEmbedding
from app.utils.logging import log_action
from PyPDF2 import PdfReader
import docx
import httpx
from langchain.text_splitter import RecursiveCharacterTextSplitter



# Semantic chunking using LangChain's splitter (sentence/paragraph boundaries)
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", "! ", "? "]  # prioritize semantic boundaries
    )
    return splitter.split_text(text)

async def get_embedding(chunk: str) -> List[float]:
    """
    Call Ollama/OpenAI embedding API to get vector for chunk.
    """
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL")
    if not ollama_base_url or not ollama_embedding_model:
        raise RuntimeError("OLLAMA_BASE_URL and OLLAMA_EMBEDDING_MODEL must be set in .env")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ollama_base_url}/api/embeddings",
            json={"model": ollama_embedding_model, "prompt": chunk}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("embedding", [0.0] * 384)
    return [0.0] * 384

async def ingest_document(
    db: AsyncSession,
    document: Document,
    file: Any,
    user_id: Optional[str] = None
) -> None:
    """
    Chunk the document, generate embeddings, and store in vector DB.
    Supports PDF, DOCX, TXT. Logs audit actions.
    Args:
        db: AsyncSession for DB access
        document: Document SQLAlchemy object
        file: File-like object (PDF/DOCX/TXT)
        user_id: User performing the upload
    """
    # Detect file type
    filename = getattr(file, "filename", "")
    mime_type, _ = mimetypes.guess_type(filename)
    chunks = []

    if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                chunks.extend(chunk_text(text))
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.lower().endswith(".docx"):
        doc = docx.Document(file)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        chunks = chunk_text(full_text)
    elif mime_type == "text/plain" or filename.lower().endswith(".txt"):
        if hasattr(file, "read"):
            file_bytes = await file.read()
            text = file_bytes.decode("utf-8")
        else:
            text = str(file)
        chunks = chunk_text(text)
    else:
        # Fallback: treat as text
        if hasattr(file, "read"):
            file_bytes = await file.read()
            text = file_bytes.decode("utf-8")
        else:
            text = str(file)
        chunks = chunk_text(text)

    # Store chunks and embeddings
    for chunk in chunks:
        vector = await get_embedding(chunk)
        embedding = DocumentEmbedding(document_id=document.id, chunk_text=chunk, vector=vector)
        db.add(embedding)
    await db.commit()

    # Audit log
    if user_id:
        await log_action(user_id, "upload_document", str(document.id))
