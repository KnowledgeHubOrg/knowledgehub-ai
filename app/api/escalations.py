from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.utils import crud
from app.db import schemas
from app.utils.security import get_current_user, require_admin
from typing import List, Any

router = APIRouter()

@router.get("/", response_model=List[schemas.Escalation])
async def list_escalations(current_user: schemas.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Any:
    require_admin(current_user)
    return await crud.get_escalations(db)

@router.post("/resolve/{escalation_id}")
async def resolve_escalation(escalation_id: str, current_user: schemas.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Any:
    require_admin(current_user)
    return await crud.resolve_escalation(db, escalation_id)
