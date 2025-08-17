from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class RoleBase(BaseModel):
    name: str
    permissions: Any

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: UUID
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role_id: Optional[UUID]

# For login endpoint: only email and password required
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: UUID
    role_id: Optional[UUID]
    created_at: datetime
    class Config:
        orm_mode = True

class DomainBase(BaseModel):
    name: str

class DomainCreate(DomainBase):
    pass

class Domain(DomainBase):
    id: UUID
    class Config:
        orm_mode = True

class DocumentBase(BaseModel):
    title: str
    content: str
    domain_id: UUID
    tags: Optional[Any]
    file_type: Optional[str]
    status: Optional[str]

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: UUID
    uploaded_by: UUID
    uploaded_at: datetime
    version: int
    class Config:
        orm_mode = True

class DocumentEmbeddingBase(BaseModel):
    document_id: UUID
    chunk_text: str
    vector: List[float]

class DocumentEmbedding(DocumentEmbeddingBase):
    id: UUID
    created_at: datetime
    class Config:
        orm_mode = True

class QuestionBase(BaseModel):
    user_id: UUID
    question_text: str
    domain_id: UUID

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: UUID
    created_at: datetime
    class Config:
        orm_mode = True

class AnswerBase(BaseModel):
    question_id: UUID
    answer_text: str
    source_docs: Any
    confidence: float

class AnswerCreate(AnswerBase):
    pass

class Answer(AnswerBase):
    id: UUID
    created_at: datetime
    class Config:
        orm_mode = True

class EscalationBase(BaseModel):
    question_id: UUID
    user_id: UUID
    status: str

class EscalationCreate(EscalationBase):
    pass

class Escalation(EscalationBase):
    id: UUID
    created_at: datetime
    class Config:
        orm_mode = True

class AuditLogBase(BaseModel):
    user_id: UUID
    action: str
    target_id: UUID

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: UUID
    timestamp: datetime
    class Config:
        orm_mode = True
