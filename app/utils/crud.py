from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import schemas, models
from typing import Optional
import uuid

# List all documents
async def list_documents(db: AsyncSession):
    result = await db.execute(select(models.Document))
    return result.scalars().all()

# Get document by ID
async def get_document_by_id(db: AsyncSession, doc_id: str):
    result = await db.execute(select(models.Document).where(models.Document.id == doc_id))
    return result.scalars().first()

# Update document
async def update_document(db: AsyncSession, doc_id: str, doc_update):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        return None
    for field, value in doc_update.dict(exclude_unset=True).items():
        setattr(doc, field, value)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

# Delete document
async def delete_document(db: AsyncSession, doc_id: str):
    doc = await get_document_by_id(db, doc_id)
    if not doc:
        return False
    await db.delete(doc)
    await db.commit()
    return True

async def get_escalations(db: AsyncSession):
    result = await db.execute(select(models.Escalation))
    return result.scalars().all()

async def resolve_escalation(db: AsyncSession, escalation_id: str):
    result = await db.execute(select(models.Escalation).where(models.Escalation.id == escalation_id))
    escalation = result.scalars().first()
    if escalation:
        setattr(escalation, "status", "Resolved")
        db.add(escalation)
        await db.commit()
        await db.refresh(escalation)
    return escalation

# Example CRUD for User
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        id=uuid.uuid4(),
        name=user.name,
        email=user.email,
        password_hash=user.password,  # Hash before storing
        role_id=user.role_id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user_by_id(db: AsyncSession, user_id: str):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalars().first()

async def update_user_password(db: AsyncSession, user_id: str, new_password_hash: str):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user:
        setattr(user, "password_hash", new_password_hash)
        db.add(user)
        await db.commit()
        await db.refresh(user)
