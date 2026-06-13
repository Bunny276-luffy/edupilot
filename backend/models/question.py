from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QuestionCreate(BaseModel):
    course_id: str
    question_text: str
    uploaded_by: str = "faculty"


class QuestionClassified(BaseModel):
    question_text: str
    blooms_level: str  # Remember | Understand | Apply | Analyze | Evaluate | Create
    reasoning: str
    co_mapping: List[str] = []
    po_mapping: List[str] = []
    confidence: float = 0.0


class QuestionInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    course_id: str
    question_text: str
    blooms_level: str
    reasoning: str
    co_mapping: List[str] = []
    po_mapping: List[str] = []
    embedding: List[float] = []
    uploaded_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class UploadQuestionsRequest(BaseModel):
    course_id: str
    questions: List[str]
    uploaded_by: str = "faculty"


class UploadQuestionsResponse(BaseModel):
    classified: List[QuestionClassified]
    total: int
    warning: Optional[str] = None
    suggestions: List[str] = []


class BloomsSummary(BaseModel):
    level: str
    count: int
    percentage: float
