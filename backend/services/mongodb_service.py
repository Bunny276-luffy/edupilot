"""
MongoDB Atlas service — CRUD + vector similarity search,
with thread-safe in-memory fallback repository for local/datathon environments.
"""
import os
import logging
from typing import Any, Optional, List
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "edupilot")

logger = logging.getLogger("edupilot")

_client: Optional[AsyncIOMotorClient] = None
_use_in_memory = False

# ─── In-Memory Datastore Fallback ──────────────────────────────────────────────
_courses: dict = {}
_questions: List[dict] = []
_students: dict = {}
_sessions: dict = {}

import json
MOCK_DB_FILE = os.path.join(os.path.dirname(__file__), "..", "traces", "mock_db.json")


def _save_to_disk() -> None:
    if not _use_in_memory:
        return
    try:
        data = {
            "courses": _courses,
            "questions": _questions,
            "students": _students,
            "sessions": _sessions
        }
        def serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat() + "Z"
            return str(obj)
        os.makedirs(os.path.dirname(MOCK_DB_FILE), exist_ok=True)
        with open(MOCK_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, default=serializer, indent=2)
    except Exception as e:
        logger.error(f"Failed to write mock db to disk: {e}")


def _load_from_disk() -> None:
    global _courses, _questions, _students, _sessions
    if not os.path.exists(MOCK_DB_FILE):
        return
    try:
        with open(MOCK_DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _courses.clear()
        _courses.update(data.get("courses", {}))
        
        raw_qs = data.get("questions", [])
        _questions.clear()
        for q in raw_qs:
            if "created_at" in q and isinstance(q["created_at"], str):
                try:
                    q["created_at"] = datetime.fromisoformat(q["created_at"].replace("Z", ""))
                except Exception:
                    pass
            _questions.append(q)
            
        _students.clear()
        _students.update(data.get("students", {}))
        for s in _students.values():
            for tp in s.get("topics_progress", []):
                if "last_session" in tp and isinstance(tp["last_session"], str):
                    try:
                        tp["last_session"] = datetime.fromisoformat(tp["last_session"].replace("Z", ""))
                    except Exception:
                        pass
                        
        _sessions.clear()
        _sessions.update(data.get("sessions", {}))
        for s in _sessions.values():
            if "created_at" in s and isinstance(s["created_at"], str):
                try:
                    s["created_at"] = datetime.fromisoformat(s["created_at"].replace("Z", ""))
                except Exception:
                    pass
            if "updated_at" in s and isinstance(s["updated_at"], str):
                try:
                    s["updated_at"] = datetime.fromisoformat(s["updated_at"].replace("Z", ""))
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Failed to load mock db from disk: {e}")


async def check_mongodb_connection() -> None:
    """Attempt connection to MongoDB, fall back to in-memory mode if it fails."""
    global _client, _use_in_memory
    try:
        _client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        # Force a request to verify connection
        await _client.admin.command("ping")
        _use_in_memory = False
        logger.info("Successfully connected to MongoDB Atlas.")
    except Exception as e:
        _use_in_memory = True
        _load_from_disk()
        logger.warning(
            f"MongoDB connection failed: {e}. Switching to InMemoryFallbackRepository. "
            "Note: In-memory fallback datastores are not shared across multiple uvicorn worker processes. "
            "Please run the server with a single worker (no --workers > 1) to ensure data consistency."
        )


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client


def get_db():
    return get_client()[MONGODB_DB_NAME]


# ─── Helper ───────────────────────────────────────────────────────────────────

def _oid(doc: dict) -> dict:
    """Convert ObjectId _id to string."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ─── Questions ────────────────────────────────────────────────────────────────

async def save_question(question_doc: dict) -> str:
    if _use_in_memory:
        qid = str(ObjectId())
        question_doc["_id"] = qid
        question_doc["created_at"] = datetime.utcnow()
        _questions.append(question_doc)
        return qid

    db = get_db()
    question_doc["created_at"] = datetime.utcnow()
    result = await db.questions.insert_one(question_doc)
    return str(result.inserted_id)


async def get_questions_by_course(course_id: str) -> list[dict]:
    if _use_in_memory:
        qs = [q for q in _questions if q.get("course_id") == course_id]
        qs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        return [_oid(q.copy()) for q in qs]

    db = get_db()
    cursor = db.questions.find({"course_id": course_id}).sort("created_at", DESCENDING)
    return [_oid(doc) async for doc in cursor]


async def vector_search_questions(
    embedding: list[float],
    course_id: str,
    limit: int = 5,
) -> list[dict]:
    """
    MongoDB Atlas Vector Search.
    Falls back to in-memory numpy cosine similarity.
    """
    if _use_in_memory:
        import numpy as np
        qs = [q for q in _questions if q.get("course_id") == course_id and q.get("embedding")]
        if not qs:
            return [_oid(q.copy()) for q in _questions if q.get("course_id") == course_id][:limit]

        results = []
        q_vec = np.array(embedding)
        for q in qs:
            q_emb = np.array(q["embedding"])
            denom = np.linalg.norm(q_vec) * np.linalg.norm(q_emb)
            sim = float(np.dot(q_vec, q_emb) / denom) if denom > 0 else 0.0
            q_copy = q.copy()
            q_copy["score"] = sim
            results.append(q_copy)

        results.sort(key=lambda x: x["score"], reverse=True)
        return [_oid(r) for r in results[:limit]]

    db = get_db()
    pipeline = [
        {
            "$vectorSearch": {
                "index": "embedding_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 50,
                "limit": limit,
                "filter": {"course_id": {"$eq": course_id}},
            }
        },
        {"$project": {"_id": 1, "question_text": 1, "co_mapping": 1, "po_mapping": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]
    results = []
    async for doc in db.questions.aggregate(pipeline):
        results.append(_oid(doc))
    return results


# ─── Courses ──────────────────────────────────────────────────────────────────

async def save_course(course_doc: dict) -> str:
    if _use_in_memory:
        cid = str(ObjectId())
        course_doc["_id"] = cid
        _courses[cid] = course_doc
        _courses[course_doc["code"]] = course_doc
        return cid

    db = get_db()
    result = await db.courses.insert_one(course_doc)
    return str(result.inserted_id)


async def get_course(course_id: str) -> Optional[dict]:
    if _use_in_memory:
        doc = _courses.get(course_id)
        return _oid(doc.copy()) if doc else None

    db = get_db()
    # Try looking up as ObjectId if valid hex
    try:
        doc = await db.courses.find_one({"_id": ObjectId(course_id)})
    except Exception:
        doc = None
    if not doc:
        # Fallback to lookup by code
        doc = await db.courses.find_one({"code": course_id})
    return _oid(doc) if doc else None


async def get_course_by_code(code: str) -> Optional[dict]:
    if _use_in_memory:
        doc = _courses.get(code)
        return _oid(doc.copy()) if doc else None

    db = get_db()
    doc = await db.courses.find_one({"code": code})
    return _oid(doc) if doc else None


async def list_courses() -> list[dict]:
    if _use_in_memory:
        seen_ids = set()
        res = []
        for c in _courses.values():
            if c["_id"] not in seen_ids:
                seen_ids.add(c["_id"])
                res.append(_oid(c.copy()))
        return res

    db = get_db()
    return [_oid(doc) async for doc in db.courses.find()]


async def upsert_default_course(course_id: str) -> dict:
    """Return or create a default course for demo purposes."""
    if _use_in_memory:
        doc = _courses.get(course_id)
        if doc:
            return _oid(doc.copy())
        default = {
            "_id": str(ObjectId()),
            "name": "Data Structures and Algorithms",
            "code": course_id,
            "faculty_id": "faculty_001",
            "course_outcomes": [
                {"id": "CO1", "description": "Understand fundamental data structures"},
                {"id": "CO2", "description": "Apply sorting and searching algorithms"},
                {"id": "CO3", "description": "Analyze time and space complexity"},
                {"id": "CO4", "description": "Design solutions using trees and graphs"},
                {"id": "CO5", "description": "Evaluate algorithm efficiency"},
            ],
            "program_outcomes": [
                {"id": "PO1", "description": "Engineering knowledge"},
                {"id": "PO2", "description": "Problem analysis"},
                {"id": "PO3", "description": "Design and development"},
                {"id": "PO4", "description": "Investigation"},
                {"id": "PO5", "description": "Modern tool usage"},
                {"id": "PO6", "description": "The engineer and society"},
            ],
        }
        _courses[default["_id"]] = default
        _courses[course_id] = default
        return _oid(default.copy())

    db = get_db()
    doc = await db.courses.find_one({"code": course_id})
    if doc:
        return _oid(doc)
    default = {
        "name": "Data Structures and Algorithms",
        "code": course_id,
        "faculty_id": "faculty_001",
        "course_outcomes": [
            {"id": "CO1", "description": "Understand fundamental data structures"},
            {"id": "CO2", "description": "Apply sorting and searching algorithms"},
            {"id": "CO3", "description": "Analyze time and space complexity"},
            {"id": "CO4", "description": "Design solutions using trees and graphs"},
            {"id": "CO5", "description": "Evaluate algorithm efficiency"},
        ],
        "program_outcomes": [
            {"id": "PO1", "description": "Engineering knowledge"},
            {"id": "PO2", "description": "Problem analysis"},
            {"id": "PO3", "description": "Design and development"},
            {"id": "PO4", "description": "Investigation"},
            {"id": "PO5", "description": "Modern tool usage"},
            {"id": "PO6", "description": "The engineer and society"},
        ],
    }
    result = await db.courses.insert_one(default)
    default["_id"] = str(result.inserted_id)
    return default


# ─── Students ─────────────────────────────────────────────────────────────────

async def save_student(student_doc: dict) -> str:
    if _use_in_memory:
        sid = str(ObjectId())
        student_doc["_id"] = sid
        _students[sid] = student_doc
        return sid

    db = get_db()
    result = await db.students.insert_one(student_doc)
    return str(result.inserted_id)


async def get_student(student_id: str) -> Optional[dict]:
    if _use_in_memory:
        doc = _students.get(student_id)
        return _oid(doc.copy()) if doc else None

    db = get_db()
    try:
        doc = await db.students.find_one({"_id": ObjectId(student_id)})
    except Exception:
        doc = None
    return _oid(doc) if doc else None


async def update_student_progress(student_id: str, topic: str, level: str) -> None:
    if _use_in_memory:
        student = _students.get(student_id)
        if not student:
            student = {
                "_id": student_id,
                "name": "Mock Student",
                "roll_number": "CS2026",
                "college": "PSG College of Technology",
                "topics_progress": []
            }
            _students[student_id] = student

        now = datetime.utcnow()
        found = False
        for tp in student.get("topics_progress", []):
            if tp["topic"] == topic:
                tp["level"] = level
                tp["last_session"] = now
                tp["session_count"] = tp.get("session_count", 1) + 1
                found = True
                break
        if not found:
            student.setdefault("topics_progress", []).append({
                "topic": topic,
                "level": level,
                "last_session": now,
                "session_count": 1
            })
        return

    db = get_db()
    now = datetime.utcnow()
    existing = await db.students.find_one(
        {"_id": ObjectId(student_id), "topics_progress.topic": topic}
    )
    if existing:
        await db.students.update_one(
            {"_id": ObjectId(student_id), "topics_progress.topic": topic},
            {
                "$set": {
                    "topics_progress.$.level": level,
                    "topics_progress.$.last_session": now,
                },
                "$inc": {"topics_progress.$.session_count": 1},
            },
        )
    else:
        await db.students.update_one(
            {"_id": ObjectId(student_id)},
            {
                "$push": {
                    "topics_progress": {
                        "topic": topic,
                        "level": level,
                        "last_session": now,
                        "session_count": 1,
                    }
                }
            },
            upsert=True,
        )


# ─── Sessions ─────────────────────────────────────────────────────────────────

async def save_session(session_doc: dict) -> str:
    if _use_in_memory:
        sid = str(ObjectId())
        session_doc["_id"] = sid
        session_doc["created_at"] = datetime.utcnow()
        session_doc["updated_at"] = datetime.utcnow()
        _sessions[sid] = session_doc
        return sid

    db = get_db()
    session_doc["created_at"] = datetime.utcnow()
    session_doc["updated_at"] = datetime.utcnow()
    result = await db.sessions.insert_one(session_doc)
    return str(result.inserted_id)


async def get_session(session_id: str) -> Optional[dict]:
    if _use_in_memory:
        doc = _sessions.get(session_id)
        return _oid(doc.copy()) if doc else None

    db = get_db()
    try:
        doc = await db.sessions.find_one({"_id": ObjectId(session_id)})
    except Exception:
        doc = None
    return _oid(doc) if doc else None


async def update_session(session_id: str, update_doc: dict) -> None:
    if _use_in_memory:
        session = _sessions.get(session_id)
        if session:
            session.update(update_doc)
            session["updated_at"] = datetime.utcnow()
        return

    db = get_db()
    update_doc["updated_at"] = datetime.utcnow()
    await db.sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": update_doc},
    )


async def append_session_message(session_id: str, message: dict) -> None:
    if _use_in_memory:
        session = _sessions.get(session_id)
        if session:
            session.setdefault("messages", []).append(message)
            session["updated_at"] = datetime.utcnow()
        return

    db = get_db()
    await db.sessions.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )


async def get_student_sessions(student_id: str) -> list[dict]:
    if _use_in_memory:
        ss = [s for s in _sessions.values() if s.get("student_id") == student_id]
        ss.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=True)
        return [_oid(s.copy()) for s in ss]

    db = get_db()
    cursor = db.sessions.find({"student_id": student_id}).sort("updated_at", DESCENDING)
    return [_oid(doc) async for doc in cursor]
