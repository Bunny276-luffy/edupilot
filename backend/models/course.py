from pydantic import BaseModel, Field
from typing import Optional, List


class Outcome(BaseModel):
    id: str   # e.g. "CO1", "PO1"
    description: str


class CourseCreate(BaseModel):
    name: str
    code: str
    faculty_id: str
    course_outcomes: List[Outcome] = []
    program_outcomes: List[Outcome] = []


class CourseInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    code: str
    faculty_id: str
    course_outcomes: List[Outcome] = []
    program_outcomes: List[Outcome] = []

    class Config:
        populate_by_name = True


class COPOCell(BaseModel):
    co_id: str
    po_id: str
    attainment: float  # 0.0 – 3.0 (NBA scale)


class COPOMatrix(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    cells: List[COPOCell] = []
    semester: str = ""
    academic_year: str = ""


class GenerateCOPORequest(BaseModel):
    course_id: str
    semester: str = "Even 2024-25"
    academic_year: str = "2024-25"
