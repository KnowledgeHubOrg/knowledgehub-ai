from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Document, DocumentEmbedding
import mimetypes
from PyPDF2 import PdfReader
import docx
from app.utils.logging import log_action

# Local chunking function
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """
    Splits text into chunks of chunk_size with overlap.
    Args:
        text: The input text to chunk
        chunk_size: Size of each chunk
        overlap: Number of overlapping characters between chunks
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
import httpx
from typing import Any, List, Optional

async def get_embedding(chunk: str) -> List[float]:
    """
    Call Ollama/OpenAI embedding API to get vector for chunk.
    """
    # Example: Call Ollama local API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "gemma:2b", "prompt": chunk}
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
        text = file.read().decode("utf-8") if hasattr(file, "read") else str(file)
        chunks = chunk_text(text)
    else:
        # Fallback: treat as text
        text = file.read().decode("utf-8") if hasattr(file, "read") else str(file)
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
