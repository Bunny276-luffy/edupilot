"""
seed_demo.py — Demo data seeder for EduPilot datathon submission.

Usage:
    python seed_demo.py

Inserts:
  • 1 course  : CS101 — Data Structures
  • 5 questions (Bloom levels auto-assigned, embeddings via llm_provider)
  • 1 demo student : Rahul Sharma

Works with or without a live MongoDB connection.
If MongoDB is unreachable, data is written to services/../traces/mock_db.json
so it persists across uvicorn restarts (single-worker mode).
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# ── Make sure we can import backend modules ────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()


async def seed():
    # ── 1. Boot MongoDB / in-memory fallback ──────────────────────────────────
    from services.mongodb_service import (
        check_mongodb_connection,
        save_course,
        save_question,
        save_student,
        get_course_by_code,
        get_student,
        _save_to_disk,
        _students,
    )
    from services.llm_provider import get_llm_provider

    await check_mongodb_connection()
    llm = get_llm_provider()

    # ── 2. Seed Course ─────────────────────────────────────────────────────────
    existing_course = await get_course_by_code("CS101")
    if existing_course:
        print("ℹ️  Course CS101 already exists, skipping.")
        course_id = "CS101"
    else:
        course_doc = {
            "name": "Data Structures",
            "code": "CS101",
            "faculty_id": "faculty_001",
            "course_outcomes": [
                {"id": "CO1", "description": "Apply data structures like arrays, linked lists, stacks, queues"},
                {"id": "CO2", "description": "Analyze time and space complexity of algorithms"},
                {"id": "CO3", "description": "Design and implement trees, graphs, and hash maps"},
                {"id": "CO4", "description": "Evaluate trade-offs between data structure choices"},
            ],
            "program_outcomes": [
                {"id": "PO1", "description": "Engineering Knowledge"},
                {"id": "PO2", "description": "Problem Analysis"},
                {"id": "PO3", "description": "Design / Development of Solutions"},
                {"id": "PO4", "description": "Conduct Investigations"},
            ],
        }
        await save_course(course_doc)
        course_id = "CS101"
        print(f"✅ Seeded course: {course_doc['name']} ({course_id})")

    # ── 3. Seed Questions ──────────────────────────────────────────────────────
    questions_to_seed = [
        {
            "question_text": "Define a binary tree.",
            "blooms_level": "Remember",
            "co_mapping": ["CO1"],
            "po_mapping": ["PO1"],
            "reasoning": "Requires simple recall of a definition.",
        },
        {
            "question_text": "Explain the difference between BFS and DFS.",
            "blooms_level": "Understand",
            "co_mapping": ["CO3"],
            "po_mapping": ["PO2"],
            "reasoning": "Requires understanding two traversal strategies and articulating the difference.",
        },
        {
            "question_text": "Implement a stack using arrays.",
            "blooms_level": "Apply",
            "co_mapping": ["CO1", "CO3"],
            "po_mapping": ["PO3"],
            "reasoning": "Requires writing code to apply knowledge of stacks and arrays.",
        },
        {
            "question_text": "Compare quicksort and mergesort worst-case complexities.",
            "blooms_level": "Analyze",
            "co_mapping": ["CO2", "CO4"],
            "po_mapping": ["PO2", "PO4"],
            "reasoning": "Requires breaking down and comparing algorithm complexities.",
        },
        {
            "question_text": "Design a LRU cache with O(1) operations.",
            "blooms_level": "Create",
            "co_mapping": ["CO3", "CO4"],
            "po_mapping": ["PO3"],
            "reasoning": "Requires synthesising knowledge of hashmaps and doubly-linked lists.",
        },
    ]

    seeded_questions = 0
    for q in questions_to_seed:
        # Generate embedding via the configured LLM provider
        try:
            embedding = await llm.embed(q["question_text"])
        except Exception as e:
            print(f"  ⚠️  Embedding failed for '{q['question_text'][:40]}…': {e}")
            embedding = []

        question_doc = {
            "course_id": course_id,
            "question_text": q["question_text"],
            "blooms_level": q["blooms_level"],
            "co_mapping": q["co_mapping"],
            "po_mapping": q["po_mapping"],
            "reasoning": q["reasoning"],
            "embedding": embedding,
            "uploaded_by": "faculty_001",
        }
        await save_question(question_doc)
        seeded_questions += 1

    print(f"✅ Seeded {seeded_questions} questions for course {course_id}")

    # ── 4. Seed Student ────────────────────────────────────────────────────────
    now_utc = datetime.now(timezone.utc)
    demo_student_id = "60c72b2f9b1d8e1f5c8f8b8a"

    existing_student = await get_student(demo_student_id)
    if existing_student:
        print("ℹ️  Demo student already exists, skipping.")
    else:
        student_doc = {
            "_id": demo_student_id,
            "name": "Rahul Sharma",
            "roll_number": "21CS1012",
            "college": "IIT Demo College",
            "topics_progress": [
                {
                    "topic": "Binary Search Trees",
                    "level": "Getting It",
                    "last_session": now_utc,
                    "session_count": 3,
                },
                {
                    "topic": "Sorting Algorithms",
                    "level": "Struggling",
                    "last_session": now_utc,
                    "session_count": 1,
                },
            ],
        }
        # For in-memory store, inject directly since save_student auto-generates _id
        from services import mongodb_service as _ms
        if _ms._use_in_memory:
            student_doc_copy = {**student_doc}
            _ms._students[demo_student_id] = student_doc_copy
        else:
            # MongoDB path: save without the pre-set _id (let Mongo assign),
            # then store the known ID so the frontend can use it.
            sid = await save_student(student_doc)
            print(f"  (MongoDB student _id: {sid})")

        print(f"✅ Seeded student: {student_doc['name']} (ID: {demo_student_id})")

    # ── 5. Persist to disk (in-memory fallback only) ───────────────────────────
    _save_to_disk()

    print()
    print("✅ Seeded 1 course, 5 questions, 1 student.")
    print("Run `uvicorn main:app --reload` and visit http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(seed())
