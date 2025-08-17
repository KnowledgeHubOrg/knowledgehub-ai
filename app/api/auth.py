from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.utils import crud
from app.db import schemas
from app.utils.security import verify_password, get_password_hash, create_access_token
from typing import Any

router = APIRouter()

@router.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)) -> Any:
    # Check if user exists
    db_user = await crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = get_password_hash(user.password)
    return await crud.create_user(db, user)

@router.post("/login")
async def login(form_data: schemas.UserLogin, db: AsyncSession = Depends(get_db)) -> Any:
    db_user = await crud.get_user_by_email(db, form_data.email)
    if not db_user or not verify_password(form_data.password, getattr(db_user, "password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    role_id_value = db_user.role_id
    # If role_id is a UUID, convert to string; if None, keep as None
    if hasattr(role_id_value, 'hex'):
        role_id_str = str(role_id_value)
    else:
        role_id_str = None
    access_token = create_access_token({
        "sub": str(db_user.id),
        "role": role_id_str
    })
    return {"access_token": access_token, "token_type": "bearer"}

# Password reset endpoint
from fastapi import Body
from app.utils.security import create_access_token, get_password_hash

@router.post("/password-reset-request")
async def password_reset_request(email: str = Body(...), db: AsyncSession = Depends(get_db)):
    """
    Initiate password reset by generating a reset token (to be sent via email in production).
    """
    user = await crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reset_token = create_access_token({"sub": str(user.id), "action": "reset"})
    # In production, send this token via email
    return {"reset_token": reset_token}

@router.post("/password-reset-confirm")
async def password_reset_confirm(token: str = Body(...), new_password: str = Body(...), db: AsyncSession = Depends(get_db)):
    """
    Confirm password reset using the token and set new password.
    """
    from jose import jwt, JWTError
    from app.utils.security import SECRET_KEY, ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        action = payload.get("action")
        if action != "reset":
            raise HTTPException(status_code=400, detail="Invalid token action")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token: missing user_id")
    user = await crud.get_user_by_id(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    hashed_pw = get_password_hash(new_password)
    await crud.update_user_password(db, str(user_id), hashed_pw)
    return {"msg": "Password reset successful"}
