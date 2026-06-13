"""
Tool: classify_bloom
Wraps the Gemini-based Bloom's taxonomy classifier.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from services.blooms_classifier import classify_blooms


async def classify_bloom_tool(inputs: dict) -> dict:
    """
    Inputs:
      question (str): The exam question to classify.
    Outputs:
      dict: {question, level, reasoning}
    """
    question = inputs.get("question", "")
    if not question:
        return {"error": "question field is required"}
    return await classify_blooms(question)
