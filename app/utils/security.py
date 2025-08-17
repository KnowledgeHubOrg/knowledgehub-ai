from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Any
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import Role

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Hash password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Create JWT token
def create_access_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# Get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Any:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Dummy: Replace with DB lookup
        return {"id": user_id, "role_id": payload.get("role")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Require admin role
async def require_admin(user: Any, db: AsyncSession = Depends(get_db)) -> None:
    role_id = user.get("role_id")
    if not role_id:
        raise HTTPException(status_code=403, detail="Admin access required")
    # Query role name from DB
    result = await db.execute(Role.__table__.select().where(Role.id == role_id))
    role = result.fetchone()
    if not role or role.name != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
