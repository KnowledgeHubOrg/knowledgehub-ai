from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.utils import crud
from app.db import schemas
from app.services.rag_pipeline import rag_pipeline
from app.utils.security import get_current_user
from typing import Any

router = APIRouter()

@router.post("/ask", response_model=schemas.Answer)
async def ask_question(
    question: schemas.QuestionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    # Store question
    from app.db.models import Question, Answer, Escalation
    import uuid
    db_question = Question(id=uuid.uuid4(), user_id=current_user["id"], question_text=question.question_text, domain_id=question.domain_id)
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)

    # RAG pipeline for answer
    answer_text, confidence, source_docs = await rag_pipeline(db, question.question_text, str(question.domain_id))
    db_answer = Answer(id=uuid.uuid4(), question_id=db_question.id, answer_text=answer_text, source_docs=source_docs, confidence=confidence)
    db.add(db_answer)
    await db.commit()
    await db.refresh(db_answer)

    # Escalate if confidence low
    if confidence < 0.7:
        escalation = Escalation(id=uuid.uuid4(), question_id=db_question.id, user_id=current_user["id"], status="Pending")
        db.add(escalation)
        await db.commit()
        await db.refresh(escalation)
    return db_answer
