"""
Bloom's Taxonomy classifier service.
Orchestrates classification for multiple questions and generates statistics,
integrated with the pluggable LLM provider.
"""
import json
from collections import Counter
from typing import Any

from services.llm_provider import get_llm_provider

BLOOMS_LEVELS = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]

# NBA standard: at least 30% should be Analyze/Evaluate/Create
HIGH_ORDER_THRESHOLD = 0.30
WARNING_THRESHOLD = 0.60  # warn if >60% are Remember/Understand


async def classify_blooms(question: str) -> dict[str, Any]:
    """Classify a single question using the pluggable LLM provider."""
    provider = get_llm_provider()
    prompt = f"""Classify this exam question into one of Bloom's Taxonomy levels:
Remember, Understand, Apply, Analyze, Evaluate, Create.

Question: {question}

Return STRICTLY as JSON with keys: question, level, reasoning. No markdown, no extra text.
"""
    raw = await provider.generate(prompt)
    try:
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        data = json.loads(clean)
        # Ensure correct keys
        return {
            "question": data.get("question", question),
            "level": data.get("level", "Understand"),
            "reasoning": data.get("reasoning", "Classified using configured LLM provider.")
        }
    except Exception:
        # Fallback keyword heuristic
        q_lower = question.lower()
        level = "Understand"
        reasoning = "Concept explanation question (fallback)."
        if any(k in q_lower for k in ["define", "what is", "list", "state", "name"]):
            level = "Remember"
            reasoning = "Recalls basic definitions or terms."
        elif any(k in q_lower for k in ["apply", "solve", "calculate", "use"]):
            level = "Apply"
            reasoning = "Applies a technique or solves a numerical query."
        elif any(k in q_lower for k in ["analyze", "compare", "contrast", "distinguish"]):
            level = "Analyze"
            reasoning = "Examines components or structural differences."
        elif any(k in q_lower for k in ["evaluate", "assess", "justify"]):
            level = "Evaluate"
            reasoning = "Requires critical judgment or validation."
        elif any(k in q_lower for k in ["design", "create", "develop", "construct"]):
            level = "Create"
            reasoning = "Requires synthesizing components into a new architecture."
        
        return {
            "question": question,
            "level": level,
            "reasoning": reasoning
        }


async def suggest_higher_bloom_questions(original_questions: list[str]) -> list[str]:
    """Suggest 3 replacement questions at Analyze/Evaluate/Create level."""
    provider = get_llm_provider()
    q_list = "\n".join(f"- {q}" for q in original_questions[:5])
    prompt = f"""The following exam questions are mostly at Remember/Understand level.
Suggest 3 better exam questions at Analyze, Evaluate, or Create level for the same topics.

Original questions:
{q_list}

Return ONLY a JSON array of 3 strings (no markdown):
["<question1>", "<question2>", "<question3>"]"""

    raw = await provider.generate(prompt)
    try:
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        suggestions = json.loads(clean)
        if isinstance(suggestions, list):
            return [str(s) for s in suggestions[:3]]
        return []
    except Exception:
        # Hardcoded high-quality fallbacks
        return [
            "Analyze the time complexity trade-offs of the proposed solution compared to a balanced AVL tree structure.",
            "Evaluate the correctness and edge-case behaviors of the given implementation under concurrency.",
            "Design an optimized distributed consensus architecture that minimizes packet drops in a high-concurrency setup."
        ]


async def classify_question_set(questions: list[str]) -> dict[str, Any]:
    """
    Classify a list of questions and return statistics + optional warning + suggestions.
    """
    classified = []
    for q in questions:
        result = await classify_blooms(q)
        classified.append(result)

    level_counts = Counter(r.get("level", "Understand") for r in classified)
    total = len(classified)

    distribution = []
    for level in BLOOMS_LEVELS:
        count = level_counts.get(level, 0)
        distribution.append(
            {
                "level": level,
                "count": count,
                "percentage": round((count / total) * 100, 1) if total > 0 else 0.0,
            }
        )

    low_order_count = level_counts.get("Remember", 0) + level_counts.get("Understand", 0)
    low_order_pct = low_order_count / total if total > 0 else 0

    warning = None
    suggestions = []
    if low_order_pct > WARNING_THRESHOLD:
        warning = (
            "⚠️ NBA standards require at least 30% of questions to be at "
            "Analysis/Evaluation/Creation level. Your paper has "
            f"{round(low_order_pct * 100)}% Remember/Understand questions."
        )
        low_order_qs = [
            r["question"]
            for r in classified
            if r.get("level") in ("Remember", "Understand")
        ]
        suggestions = await suggest_higher_bloom_questions(low_order_qs)

    return {
        "classified": classified,
        "distribution": distribution,
        "total": total,
        "warning": warning,
        "suggestions": suggestions,
        "high_order_percentage": round(
            (1 - low_order_pct) * 100, 1
        ),
    }


def assign_co_from_bloom(blooms_level: str) -> list[str]:
    """Heuristic CO mapping based on Bloom's level (used if vector similarity falls back)."""
    mapping = {
        "Remember": ["CO1"],
        "Understand": ["CO1", "CO2"],
        "Apply": ["CO2", "CO3"],
        "Analyze": ["CO3", "CO4"],
        "Evaluate": ["CO4", "CO5"],
        "Create": ["CO4", "CO5"],
    }
    return mapping.get(blooms_level, ["CO1"])
