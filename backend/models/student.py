from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TopicProgress(BaseModel):
    topic: str
    level: str  # Struggling | Getting It | Mastered
    last_session: datetime = Field(default_factory=datetime.utcnow)
    session_count: int = 1


class StudentCreate(BaseModel):
    name: str
    roll_number: str
    college: str


class StudentInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    roll_number: str
    college: str
    topics_progress: List[TopicProgress] = []

    class Config:
        populate_by_name = True


class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    student_id: str
    topic: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    understanding_level: str
    exchange_count: int


class SessionInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    student_id: str
    topic: str
    messages: List[ChatMessage] = []
    understanding_level: str = "Struggling"
    exchange_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
