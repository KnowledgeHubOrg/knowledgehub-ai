from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.utils import crud
from app.db import schemas
from app.utils.security import get_current_user, require_admin
from app.services.ingest_pipeline import ingest_document
from typing import List, Any

router = APIRouter()

@router.post("/upload", response_model=schemas.Document)
async def upload_document(
    title: str,
    domain_id: str,
    file: UploadFile = File(...),
    tags: Any = None,
    file_type: str = "",
    current_user: schemas.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    # Only admin can upload
    require_admin(current_user)
    # Save file, chunk, embed, store
    # Create document object (stub, replace with actual CRUD logic)
    from app.db.models import Document
    doc = Document(title=title, content="", domain_id=domain_id, uploaded_by=current_user.id, tags=tags, file_type=file_type, status="uploaded")
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    # Chunk, embed, and store in vector DB
    await ingest_document(db, doc, file)
    return doc

# ... Add update, delete, list endpoints ...
