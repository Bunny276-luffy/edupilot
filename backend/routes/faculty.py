"""
Faculty API routes:
  POST /api/faculty/upload-questions   — parse + classify
  POST /api/faculty/generate-copo      — CO-PO matrix
  GET  /api/faculty/naac-report/{course_id}  — download NAAC PDF
"""
import io
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse

from models.question import UploadQuestionsRequest, UploadQuestionsResponse
from models.course import GenerateCOPORequest
from services.blooms_classifier import classify_question_set, assign_co_from_bloom
from services.copo_mapper import generate_copo_matrix, map_question_to_cos_pos
from services.mongodb_service import (
    save_question,
    get_questions_by_course,
    upsert_default_course,
)
from services.pdf_generator import generate_copo_pdf, generate_naac_pdf
from services.llm_provider import get_llm_provider

router = APIRouter(prefix="/api/faculty", tags=["Faculty"])


def _parse_pdf_text(file_bytes: bytes) -> list[str]:
    """Extract text from a PDF and split by lines that look like questions."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        text = file_bytes.decode("utf-8", errors="ignore")

    lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 20]
    # Filter lines that look like questions (contain '?' or start with number/letter)
    questions = []
    for ln in lines:
        if "?" in ln or (ln and ln[0].isdigit()):
            questions.append(ln)
    return questions if questions else lines[:20]


@router.post("/upload-questions", response_model=UploadQuestionsResponse)
async def upload_questions(
    request: Request,
    course_id: Optional[str] = Form(None),
    uploaded_by: str = Form(default="faculty"),
    file: Optional[UploadFile] = File(default=None),
    questions_text: Optional[str] = Form(default=None),
):
    """
    Accept a PDF or plain-text list of questions (via Form-data or JSON).
    Classify each using Gemini Bloom's taxonomy.
    Save to MongoDB and return classification results.
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            course_id = body.get("course_id")
            uploaded_by = body.get("uploaded_by", "faculty")
            questions_input = body.get("questions_text") or body.get("questions")
            if isinstance(questions_input, list):
                raw_questions = questions_input
            elif isinstance(questions_input, str):
                raw_questions = [q.strip() for q in questions_input.strip().split("\n") if q.strip()]
            else:
                raw_questions = []
        else:
            if not file and not questions_text:
                raise HTTPException(status_code=400, detail="Provide either a file or questions_text")

            # Parse questions
            if file:
                file_bytes = await file.read()
                raw_questions = _parse_pdf_text(file_bytes)
            else:
                raw_questions = [q.strip() for q in questions_text.strip().split("\n") if q.strip()]

        if not course_id:
            raise HTTPException(status_code=400, detail="Provide course_id")

        if not raw_questions:
            raise HTTPException(status_code=400, detail="No questions could be extracted")

        raw_questions = raw_questions[:30]  # Limit to 30 for API cost reasons

        # Classify
        result = await classify_question_set(raw_questions)

        # Ensure course exists
        await upsert_default_course(course_id)

        classified_objs = []
        # Save each classified question to MongoDB
        for item in result["classified"]:
            q_text = item.get("question", "")
            co_list, po_list, q_emb = await map_question_to_cos_pos(q_text, course_id)
            await save_question({
                "course_id": course_id,
                "question_text": q_text,
                "blooms_level": item.get("level", "Understand"),
                "reasoning": item.get("reasoning", ""),
                "co_mapping": co_list,
                "po_mapping": po_list,
                "embedding": q_emb,
                "uploaded_by": uploaded_by,
            })
            classified_objs.append({
                "question_text": q_text,
                "blooms_level": item.get("level", "Understand"),
                "reasoning": item.get("reasoning", ""),
                "co_mapping": co_list,
                "po_mapping": po_list,
                "confidence": 0.85,
            })

        return UploadQuestionsResponse(
            classified=classified_objs,
            total=result["total"],
            warning=result.get("warning"),
            suggestions=result.get("suggestions", []),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate-copo")
async def generate_copo(req: GenerateCOPORequest):
    """Generate CO-PO attainment matrix from stored questions."""
    try:
        matrix = await generate_copo_matrix(
            course_id=req.course_id,
            semester=req.semester,
            academic_year=req.academic_year,
        )
        return matrix
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/naac-report/{course}")
async def download_naac_report(
    course: str,
    semester: str = "Even 2024-25",
    academic_year: str = "2024-25",
):
    """
    Generate and stream a NAAC PDF report for a given course.
    """
    try:
        # Get matrix data
        matrix = await generate_copo_matrix(course, semester, academic_year)

        # Get questions for bloom distribution
        questions = await get_questions_by_course(course)
        from collections import Counter
        level_counts = Counter(q.get("blooms_level", "Understand") for q in questions)
        total = len(questions) or 1
        blooms_levels = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
        blooms_dist = [
            {
                "level": lvl,
                "count": level_counts.get(lvl, 0),
                "percentage": round(level_counts.get(lvl, 0) / total * 100, 1),
            }
            for lvl in blooms_levels
        ]

        # Generate AI summary
        stats = {
            "blooms_dist": {item["level"]: item["percentage"] for item in blooms_dist},
            "avg_co_attainment": matrix.get("avg_attainment", 0),
            "total_questions": total,
        }
        provider = get_llm_provider()
        prompt = f"""Write a concise NAAC accreditation summary paragraph (150–200 words) for:
Course: {matrix.get("course_name", course)}
Bloom's Distribution: {stats.get('blooms_dist', {})}
Average CO Attainment: {stats.get('avg_co_attainment', 0):.2f} out of 3.0
Total Questions Analysed: {stats.get('total_questions', 0)}

The paragraph should sound professional and suitable for an NBA/NAAC criterion report."""
        summary = await provider.generate(prompt)

        # Build PDF
        course_data = {
            "course_name": matrix.get("course_name", ""),
            "course_code": matrix.get("course_code", ""),
            "faculty_id": "Faculty",
            "semester": semester,
            "academic_year": academic_year,
        }
        pdf_bytes = generate_naac_pdf(
            course_data=course_data,
            blooms_dist=blooms_dist,
            co_attainment=matrix.get("co_attainment", {}),
            summary_text=summary,
        )

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="NAAC_{course}_{academic_year}.pdf"'
            },
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/copo-pdf/{course_id}")
async def download_copo_pdf(
    course_id: str,
    semester: str = "Even 2024-25",
    academic_year: str = "2024-25",
):
    """Stream CO-PO matrix as PDF."""
    try:
        matrix = await generate_copo_matrix(course_id, semester, academic_year)
        pdf_bytes = generate_copo_pdf(matrix)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="COPO_{course_id}.pdf"'
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
