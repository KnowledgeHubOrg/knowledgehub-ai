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


# List all documents
@router.get("/", response_model=List[schemas.Document])
async def list_documents(db: AsyncSession = Depends(get_db), current_user: schemas.User = Depends(get_current_user)) -> Any:
    docs = await crud.list_documents(db)
    return docs

# Get a document by ID
@router.get("/{doc_id}", response_model=schemas.Document)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db), current_user: schemas.User = Depends(get_current_user)) -> Any:
    doc = await crud.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

# Update a document
@router.put("/{doc_id}", response_model=schemas.Document)
async def update_document(doc_id: str, doc_update: schemas.DocumentCreate, db: AsyncSession = Depends(get_db), current_user: schemas.User = Depends(get_current_user)) -> Any:
    require_admin(current_user)
    doc = await crud.update_document(db, doc_id, doc_update)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

# Delete a document
@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db), current_user: schemas.User = Depends(get_current_user)) -> None:
    require_admin(current_user)
    success = await crud.delete_document(db, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
