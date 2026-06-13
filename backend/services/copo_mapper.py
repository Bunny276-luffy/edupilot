"""
CO-PO mapping service.
Computes attainment scores using Bloom's level and question CO mappings,
integrated with pluggable LLM provider for vector embeddings.
"""
from typing import Any
import numpy as np
from services.llm_provider import get_llm_provider
from services.mongodb_service import get_questions_by_course, get_course, upsert_default_course


# NBA attainment scale: 3 = high, 2 = moderate, 1 = low, 0 = not addressed
BLOOMS_ATTAINMENT = {
    "Remember": 1.0,
    "Understand": 1.5,
    "Apply": 2.0,
    "Analyze": 2.5,
    "Evaluate": 3.0,
    "Create": 3.0,
}

# Default PO mapping for each CO index (1-indexed)
DEFAULT_CO_PO_MAP = {
    "CO1": ["PO1", "PO2"],
    "CO2": ["PO1", "PO2", "PO3"],
    "CO3": ["PO2", "PO4"],
    "CO4": ["PO3", "PO4", "PO5"],
    "CO5": ["PO4", "PO5"],
}


async def generate_copo_matrix(course_id: str, semester: str, academic_year: str) -> dict[str, Any]:
    """
    Build a CO-PO attainment matrix from classified questions in MongoDB.
    Returns matrix data and course info.
    """
    course = await get_course(course_id)
    if not course:
        course = await upsert_default_course(course_id)

    questions = await get_questions_by_course(course_id)

    cos = [o["id"] for o in course.get("course_outcomes", [])]
    pos = [o["id"] for o in course.get("program_outcomes", [])]

    if not cos:
        cos = [f"CO{i}" for i in range(1, 6)]
    if not pos:
        pos = [f"PO{i}" for i in range(1, 7)]

    # Accumulate attainment scores per CO
    co_scores: dict[str, list[float]] = {co: [] for co in cos}

    for q in questions:
        bloom_level = q.get("blooms_level", "Understand")
        attainment = BLOOMS_ATTAINMENT.get(bloom_level, 1.5)
        mapped_cos = q.get("co_mapping", [])
        for co in mapped_cos:
            if co in co_scores:
                co_scores[co].append(attainment)

    # Average attainment per CO
    co_attainment = {}
    for co, scores in co_scores.items():
        co_attainment[co] = round(sum(scores) / len(scores), 2) if scores else 0.0

    # Build matrix: rows = COs, cols = POs
    cells = []
    for co in cos:
        for po in pos:
            # Check if CO maps to this PO
            co_po_list = DEFAULT_CO_PO_MAP.get(co, [])
            if po in co_po_list:
                value = co_attainment.get(co, 0.0)
            else:
                value = 0.0
            cells.append({"co_id": co, "po_id": po, "attainment": value})

    avg_attainment = (
        sum(co_attainment.values()) / len(co_attainment) if co_attainment else 0.0
    )

    return {
        "course_id": course_id,
        "course_code": course.get("code", course_id),
        "course_name": course.get("name", "Course"),
        "semester": semester,
        "academic_year": academic_year,
        "cos": cos,
        "pos": pos,
        "cells": cells,
        "co_attainment": co_attainment,
        "avg_attainment": round(avg_attainment, 2),
        "total_questions": len(questions),
    }


async def map_question_to_cos_pos(question_text: str, course_id: str) -> tuple[list[str], list[str], list[float]]:
    """
    Generate question embedding, calculate cosine similarity with CO descriptions,
    map to top 3 COs, and inherit the course's PO list.
    """
    provider = get_llm_provider()
    q_emb = await provider.embed(question_text)
    
    course = await get_course(course_id)
    if not course:
        course = await upsert_default_course(course_id)
        
    course_outcomes = course.get("course_outcomes", [])
    program_outcomes = course.get("program_outcomes", [])
    
    if not course_outcomes:
        course_outcomes = [
            {"id": "CO1", "description": "Understand fundamental data structures"},
            {"id": "CO2", "description": "Apply sorting and searching algorithms"},
            {"id": "CO3", "description": "Analyze time and space complexity"},
            {"id": "CO4", "description": "Design solutions using trees and graphs"},
            {"id": "CO5", "description": "Evaluate algorithm efficiency"},
        ]
        
    co_similarities = []
    for co in course_outcomes:
        co_desc = co.get("description", "")
        co_emb = await provider.embed(co_desc)
        
        a = np.array(q_emb)
        b = np.array(co_emb)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        similarity = float(np.dot(a, b) / denom) if denom > 0 else 0.0
        co_similarities.append((co.get("id"), similarity))
        
    co_similarities.sort(key=lambda x: x[1], reverse=True)
    top_cos = [item[0] for item in co_similarities[:3]]
    
    po_list = [po.get("id") for po in program_outcomes]
    if not po_list:
        po_list = ["PO1", "PO2", "PO3", "PO4", "PO5", "PO6"]
        
    return top_cos, po_list, q_emb
