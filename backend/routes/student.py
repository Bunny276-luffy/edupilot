"""
Student API routes:
  POST /api/student/chat           — Socratic tutor response
  GET  /api/student/progress/{id}  — student topic progress
  POST /api/student/register       — register a student
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from models.student import ChatRequest, ChatResponse, StudentCreate
from services.llm_provider import get_llm_provider
from services.mongodb_service import (
    save_student,
    get_student,
    update_student_progress,
    get_session,
    save_session,
    update_session,
    append_session_message,
    get_student_sessions,
)

router = APIRouter(prefix="/api/student", tags=["Student"])


@router.post("/register")
async def register_student(student: StudentCreate):
    """Register a new student and return their ID."""
    try:
        doc = student.model_dump()
        student_id = await save_student(doc)
        return {"student_id": student_id, "message": "Student registered successfully"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


async def socratic_response(
    topic: str,
    conversation_history: list[dict],
    exchange_count: int,
) -> dict[str, str]:
    """
    Generate a Socratic tutor response using the pluggable LLM provider.
    Returns {reply, understanding_level}.
    """
    system_prompt = (
        "You are a Socratic tutor for undergraduate engineering students in India. "
        "Never give direct answers. Guide the student with probing questions that lead "
        "them to discover the concept themselves. After 3 exchanges, if the student is "
        "still stuck, give a small hint only. "
        "At the end of your response, on a NEW LINE, output ONLY one of these labels "
        "exactly: [LEVEL: Struggling] or [LEVEL: Getting It] or [LEVEL: Mastered]."
    )

    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in conversation_history[-8:]
    )
    hint_note = (
        "\n(The student has asked 3+ times. You may give a small hint now.)"
        if exchange_count >= 3
        else ""
    )
    prompt = f"Topic: {topic}\n\nConversation so far:\n{history_text}{hint_note}\n\nYour Socratic response:"

    provider = get_llm_provider()
    raw = await provider.generate(prompt, system_prompt=system_prompt)

    # Parse level tag
    level = "Struggling"
    reply = raw
    if "[LEVEL:" in raw:
        parts = raw.rsplit("[LEVEL:", 1)
        reply = parts[0].strip()
        level_raw = parts[1].replace("]", "").strip()
        if level_raw in ("Struggling", "Getting It", "Mastered"):
            level = level_raw

    return {"reply": reply, "understanding_level": level}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Socratic tutor endpoint.
    Maintains conversation context across exchanges within a session.
    """
    try:
        # Load or create session
        session = None
        if req.session_id:
            session = await get_session(req.session_id)

        if session is None:
            session_doc = {
                "student_id": req.student_id,
                "topic": req.topic,
                "messages": [],
                "understanding_level": "Struggling",
                "exchange_count": 0,
            }
            session_id = await save_session(session_doc)
            session = await get_session(session_id)
        else:
            session_id = req.session_id

        # Append user message
        user_msg = {
            "role": "user",
            "content": req.message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await append_session_message(session_id, user_msg)

        messages = session.get("messages", []) + [user_msg]
        exchange_count = session.get("exchange_count", 0) + 1

        # Get Socratic response from Gemini
        result = await socratic_response(
            topic=req.topic,
            conversation_history=messages,
            exchange_count=exchange_count,
        )

        ai_msg = {
            "role": "assistant",
            "content": result["reply"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        await append_session_message(session_id, ai_msg)

        # Update session
        understanding = result["understanding_level"]
        await update_session(
            session_id,
            {"understanding_level": understanding, "exchange_count": exchange_count},
        )

        # Update student topic progress
        try:
            await update_student_progress(req.student_id, req.topic, understanding)
        except Exception:
            pass  # Non-critical

        return ChatResponse(
            session_id=session_id,
            reply=result["reply"],
            understanding_level=understanding,
            exchange_count=exchange_count,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/progress/{id}")
async def get_progress(id: str):
    """Return a student's topic progress and session history."""
    try:
        student = await get_student(id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        sessions = await get_student_sessions(id)
        # Summarise sessions per topic
        return {
            "student": student,
            "topics_progress": student.get("topics_progress", []),
            "recent_sessions": [
                {
                    "session_id": s["_id"],
                    "topic": s.get("topic"),
                    "understanding_level": s.get("understanding_level"),
                    "message_count": len(s.get("messages", [])),
                    "updated_at": s.get("updated_at"),
                }
                for s in sessions[:10]
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/sessions/{student_id}")
async def get_sessions(student_id: str):
    """Return all sessions for a student."""
    try:
        sessions = await get_student_sessions(student_id)
        return {"sessions": sessions}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
