from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) # type: ignore
Base = declarative_base()

# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session: # type: ignore
        yield session
